"""AkShareClient - wraps the akshare library for A-share market data.

AkShare functions are synchronous and return pandas DataFrames. This client
runs them in a ThreadPoolExecutor to avoid blocking the asyncio event loop,
converts results to plain dicts/lists, and never raises on failure - it
returns empty results and logs warnings instead.

This is a Component (deterministic, no LLM), not an Agent.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)


class AkShareClient:
    """Async wrapper around akshare for A-share market data.

    All methods return empty results on failure instead of raising.
    Internal concurrency limit of 10 via asyncio.Semaphore.
    """

    def __init__(self, call_timeout: float = 30.0, parallel_limit: int = 10):
        self._call_timeout = call_timeout
        self._semaphore = asyncio.Semaphore(parallel_limit)
        self._executor = ThreadPoolExecutor(max_workers=parallel_limit)
        self._ak = None

    def _get_ak(self):
        """Lazy import akshare so module loads even if akshare is missing."""
        if self._ak is None:
            import akshare as ak

            self._ak = ak
        return self._ak

    async def _run_sync(self, fn, *args, **kwargs) -> Any:
        """Run a synchronous akshare function in a thread pool."""
        async with self._semaphore:
            try:
                loop = asyncio.get_running_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(self._executor, lambda: fn(*args, **kwargs)),
                    timeout=self._call_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("AkShare call timed out after %.1fs", self._call_timeout)
                raise
            except Exception:
                logger.warning("AkShare call failed", exc_info=True)
                raise

    async def get_index_daily(self, symbol: str) -> list[dict]:
        """Return index OHLCV history."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.stock_zh_index_daily, symbol=symbol)
            return self._normalize_index(df)
        except Exception:
            return []

    async def get_sector_performance(self) -> list[dict]:
        """Return sector-level performance from Tonghuashun classification."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.stock_board_industry_summary_ths)
            if df is None or df.empty:
                return []
            result = []
            for _, row in df.iterrows():
                entry = {
                    "sector_name": str(row.get("板块名称", row.iloc[0] if len(df.columns) > 0 else "")),
                    "pct_change": _safe_float(row.get("涨跌幅")),
                }
                for col in df.columns:
                    if "龙头" in str(col) or "领涨" in str(col):
                        entry["leading_stocks"] = str(row.get(col, ""))
                        break
                result.append(entry)
            return result
        except Exception:
            return []

    async def get_shibor(self) -> dict:
        """Return latest SHIBOR rates."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.macro_china_shibor_all)
            if df is None or df.empty:
                return {}
            latest = df.iloc[-1]
            return {
                "overnight": _safe_float(latest.get("O/N")),
                "1w": _safe_float(latest.get("1W")),
                "2w": _safe_float(latest.get("2W")),
                "1m": _safe_float(latest.get("1M")),
            }
        except Exception:
            return {}

    async def get_pmi(self) -> float | None:
        """Return latest manufacturing PMI value, or None on failure."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.macro_china_pmi)
            if df is None or df.empty:
                return None
            latest = df.iloc[-1]
            for col in df.columns:
                val = latest.get(col)
                f = _safe_float(val)
                if f is not None:
                    return f
            return None
        except Exception:
            return None

    async def get_cpi(self) -> float | None:
        """Return latest CPI year-over-year change, or None on failure."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.macro_china_cpi_yearly)
            if df is None or df.empty:
                return None
            latest = df.iloc[-1]
            for col in df.columns:
                val = latest.get(col)
                f = _safe_float(val)
                if f is not None:
                    return f
            return None
        except Exception:
            return None

    async def get_northbound_flow(self) -> dict:
        """Return today northbound net flow through Stock Connect."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.stock_hsgt_north_net_flow_in_em)
            if df is None or df.empty:
                return {}
            latest = df.iloc[-1]
            sh = _safe_float(latest.get("沪股通"))
            sz = _safe_float(latest.get("深股通"))
            total = _safe_float(latest.get("北上资金"))
            return {"sh_net": sh, "sz_net": sz, "total_net": total}
        except Exception:
            return {}

    async def get_stock_news(self, stock_code: str, limit: int = 20) -> list[dict]:
        """Return recent news articles for a stock from East Money."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.stock_news_em, symbol=stock_code)
            if df is None or df.empty:
                return []
            result = []
            for _, row in df.head(limit).iterrows():
                result.append(
                    {
                        "title": str(row.get("标题", row.get("title", ""))),
                        "content": str(row.get("内容", row.get("content", ""))),
                        "publish_time": str(row.get("发布时间", row.get("publish_time", ""))),
                        "source": str(row.get("文章来源", row.get("source", ""))),
                    }
                )
            return result
        except Exception:
            return []

    async def get_announcements(self, stock_code: str, limit: int = 20) -> list[dict]:
        """Return recent company announcements from exchange websites."""
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.stock_info_sh_name_code, symbol=stock_code)
            if df is None or df.empty:
                return []
            result = []
            for _, row in df.head(limit).iterrows():
                result.append(
                    {
                        "title": str(row.get("name", row.get("标题", ""))),
                        "type": "",
                        "publish_date": str(row.get("date", row.get("发布日期", ""))),
                        "summary": str(row.get("content", row.get("内容", ""))),
                    }
                )
            return result
        except Exception:
            return []

    async def get_stock_list(self) -> list[dict]:
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.stock_info_a_code_name)
            if df is None or df.empty:
                return []
            return df.to_dict(orient="records")
        except Exception:
            return []

    async def get_stock_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        try:
            ak = self._get_ak()
            df = await self._run_sync(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            if df is None or df.empty:
                return []
            result = []
            for _, row in df.iterrows():
                result.append(
                    {
                        "date": str(row.get("日期", "")),
                        "open": _safe_float(row.get("开盘")),
                        "close": _safe_float(row.get("收盘")),
                        "high": _safe_float(row.get("最高")),
                        "low": _safe_float(row.get("最低")),
                        "volume": _safe_float(row.get("成交量")),
                        "amount": _safe_float(row.get("成交额")),
                        "pct_change": _safe_float(row.get("涨跌幅")),
                    }
                )
            return result
        except Exception:
            return []

    async def get_stock_spot(self) -> list[dict]:
        try:
            ak = self._get_ak()
            df = await self._run_sync(ak.stock_zh_a_spot)
            if df is None or df.empty:
                return []
            result = []
            for _, row in df.iterrows():
                result.append(
                    {
                        "code": str(row.get("code", "")),
                        "name": str(row.get("name", "")),
                        "price": _safe_float(row.get("trade")),
                        "pe": _safe_float(row.get("per")),
                        "pb": _safe_float(row.get("pb")),
                        "market_cap": _safe_float(row.get("mktcap")),
                        "turnover": _safe_float(row.get("turnoverratio")),
                        "change_pct": _safe_float(row.get("changepercent")),
                    }
                )
            return result
        except Exception:
            return []

    @staticmethod
    def _normalize_index(df) -> list[dict]:
        """Convert AkShare index DataFrame to list of normalized dicts."""
        if df is None or getattr(df, "empty", True):
            return []
        result = []
        for _, row in df.iterrows():
            entry = {}
            for col in df.columns:
                cl = str(col).lower()
                if "date" in cl or "日期" in str(col):
                    entry["date"] = str(row[col])
                elif "open" in cl or "开盘" in str(col):
                    entry["open"] = _safe_float(row[col])
                elif "high" in cl or "最高" in str(col):
                    entry["high"] = _safe_float(row[col])
                elif "low" in cl or "最低" in str(col):
                    entry["low"] = _safe_float(row[col])
                elif "close" in cl or "收盘" in str(col):
                    entry["close"] = _safe_float(row[col])
                elif "volume" in cl or "成交" in str(col):
                    entry["volume"] = _safe_float(row[col])
            if entry:
                result.append(entry)
        return result


def _safe_float(val) -> float | None:
    """Convert a value to float, returning None if NaN, Inf, or not convertible."""
    import math

    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None
