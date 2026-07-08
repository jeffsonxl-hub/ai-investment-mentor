"""TuShareClient — wraps the tushare library for A-share structured data.

TuShare's pro_api is synchronous and returns pandas DataFrames. This client
runs calls in a ThreadPoolExecutor with a semaphore of 1 (sequential access
required by TuShare's free tier). All methods raise DataFetchError on failure.

This is a Component (deterministic, no LLM), not an Agent.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .exceptions import DataFetchError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 15.0


class TuShareClient:
    """Async wrapper around tushare pro_api for A-share structured data.

    Enforces sequential access (semaphore=1) for TuShare free-tier compliance.
    All methods raise DataFetchError on failure.
    """

    def __init__(self, token: str, call_timeout: float = _DEFAULT_TIMEOUT):
        self._token = token
        self._call_timeout = call_timeout
        self._semaphore = asyncio.Semaphore(1)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._pro = None  # Lazily initialized

    def _get_pro(self):
        """Lazy import tushare so the module loads even if tushare is missing or token is invalid."""
        if self._pro is None:
            import tushare as ts

            # Pass token directly - set_token() writes tk.csv to ~/ which fails on locked-down Windows
            self._pro = ts.pro_api(token=self._token)
        return self._pro

    async def _run_sync(self, fn, *args, **kwargs) -> Any:
        """Run a synchronous tushare call sequentially through a thread pool.

        Acquires the internal semaphore first to ensure sequential access.
        Wraps all errors in DataFetchError.
        """
        async with self._semaphore:
            try:
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, lambda: fn(*args, **kwargs)),
                    timeout=self._call_timeout,
                )
                return result
            except asyncio.TimeoutError:
                raise DataFetchError(
                    "tushare",
                    f"Call timed out after {self._call_timeout:.0f}s",
                )
            except DataFetchError:
                raise
            except Exception as e:
                raise DataFetchError("tushare", str(e), original=e)

    async def get_daily(self, trade_date: str) -> list[dict]:
        """Return OHLCV + trading status for all A-share stocks on a given date.

        Args:
            trade_date: Trading date in 'YYYYMMDD' format.

        Returns:
            List of {ts_code, open, high, low, close, pre_close, change, pct_chg, vol, amount}.
        """
        pro = self._get_pro()
        df = await self._run_sync(pro.daily, trade_date=trade_date)
        return self._df_to_dicts(df)

    async def get_stock_basic(self) -> list[dict]:
        """Return full A-share stock list.

        Returns:
            List of {ts_code, name, industry, market, list_date}.
        """
        pro = self._get_pro()
        df = await self._run_sync(
            pro.stock_basic, list_status="L", fields="ts_code,name,industry,market,list_date"
        )
        return self._df_to_dicts(df)

    async def get_daily_basic(
        self,
        trade_date: str,
        ts_codes: list[str] | None = None,
    ) -> list[dict]:
        """Return daily valuation metrics.

        Args:
            trade_date: Trading date in 'YYYYMMDD' format.
            ts_codes: Optional list of stock codes to fetch. None = all stocks.

        Returns:
            List of {ts_code, pe, pb, total_mv, turnover_rate, ...}.
        """
        pro = self._get_pro()
        kwargs: dict[str, Any] = {"trade_date": trade_date}
        if ts_codes:
            kwargs["ts_code"] = ",".join(ts_codes)
        df = await self._run_sync(pro.daily_basic, **kwargs)
        return self._df_to_dicts(df)

    async def get_income(self, ts_codes: list[str], period: str) -> list[dict]:
        """Return income statement data for specified stocks.

        Args:
            ts_codes: Stock codes, joined with commas internally.
            period: Reporting period, e.g. '20260630' for Q2 2026.

        Returns:
            List of {ts_code, end_date, revenue, n_income, total_revenue, ...}.
        """
        pro = self._get_pro()
        df = await self._run_sync(pro.income, ts_code=",".join(ts_codes), period=period)
        return self._df_to_dicts(df)

    async def get_index_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Return index OHLCV over a date range.

        Args:
            ts_code: TuShare index code, e.g. '000001.SH' for Shanghai Composite.
            start_date: Start date in 'YYYYMMDD' format.
            end_date: End date in 'YYYYMMDD' format.

        Returns:
            List of {ts_code, trade_date, open, high, low, close, vol, amount}.
        """
        pro = self._get_pro()
        df = await self._run_sync(
            pro.index_daily,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )
        return self._df_to_dicts(df)

    @staticmethod
    def _df_to_dicts(df) -> list[dict]:
        """Convert pandas DataFrame to list of dicts."""
        if df is None or getattr(df, "empty", True):
            return []
        import pandas as pd

        # Convert all values to Python native types
        if isinstance(df, pd.DataFrame):
            return df.where(df.notna(), None).to_dict(orient="records")
        return []
