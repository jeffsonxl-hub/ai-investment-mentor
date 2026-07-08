"""DataProvider - unified async data access for all Agents.

Uses AkShare for all data categories. TuShare is optional (kept for V2).

This is a Component (deterministic, no LLM), not an Agent.
"""

import logging
from typing import TYPE_CHECKING

from .ak_share_client import AkShareClient
from .tu_share_client import TuShareClient

if TYPE_CHECKING:
    from memory.repository import MemoryRepository

logger = logging.getLogger(__name__)


class DataProvider:
    """Unified data access for all Agents. AkShare-native, TuShare optional."""

    def __init__(
        self,
        ak_share_client: AkShareClient,
        memory_repo: "MemoryRepository",
        tu_share_client: TuShareClient | None = None,
        news_default_limit: int = 20,
    ):
        self._ak = ak_share_client
        self._ts = tu_share_client
        self._memory = memory_repo
        self._news_limit = news_default_limit

    # -- Market Data ----------------------------------------------------------

    async def get_market_snapshot(self, date: str) -> dict:
        quality_issues = []
        indices = {}
        macro = {"shibor_overnight": None, "pmi": None, "cpi": None}
        northbound = {}

        # Index data from AkShare
        try:
            for name, symbol in _AK_INDEX_SYMBOLS.items():
                data = await self._ak.get_index_daily(symbol)
                if data:
                    indices[name] = data[-1]
                else:
                    indices[name] = {}
            await self._record("akshare", "success")
        except Exception as e:
            logger.warning("AkShare index data failed: %s", e)
            quality_issues.append("index_data_degraded")
            await self._record("akshare", "partial", str(e))

        # Macro indicators from AkShare
        try:
            shibor_data = await self._ak.get_shibor()
            if shibor_data:
                macro["shibor_overnight"] = shibor_data.get("overnight")
            macro["pmi"] = await self._ak.get_pmi()
            macro["cpi"] = await self._ak.get_cpi()
        except Exception as e:
            logger.warning("AkShare macro data failed: %s", e)
            quality_issues.append("macro_missing")

        # Northbound flow from AkShare
        try:
            northbound = await self._ak.get_northbound_flow()
        except Exception as e:
            logger.warning("AkShare northbound flow failed: %s", e)
            quality_issues.append("northbound_missing")

        if not quality_issues:
            data_quality = "full"
        elif len(quality_issues) <= 2:
            data_quality = "degraded"
        else:
            data_quality = "failed"

        return {
            "date": date,
            "indices": indices,
            "macro": macro,
            "northbound_flow": northbound,
            "data_quality": data_quality,
        }

    async def get_index_data(self, start_date: str, end_date: str) -> list[dict]:
        result = []
        try:
            for symbol in _AK_INDEX_SYMBOLS.values():
                data = await self._ak.get_index_daily(symbol)
                result.extend(data)
            await self._record("akshare", "success")
        except Exception as e:
            logger.warning("AkShare index range failed: %s", e)
            await self._record("akshare", "failed", str(e))
        return result

    async def get_sector_performance(self) -> list[dict]:
        try:
            result = await self._ak.get_sector_performance()
            await self._record("akshare", "success")
            return result
        except Exception as e:
            logger.warning("AkShare sector performance failed: %s", e)
            await self._record("akshare", "failed", str(e))
            return []

    # -- Fundamental Data -----------------------------------------------------

    async def get_fundamental_snapshot(
        self,
        ts_codes: list[str],
        date: str,
    ) -> list[dict]:
        result = []
        try:
            all_spot = await self._ak.get_stock_spot()
            if not all_spot:
                await self._record("akshare", "failed", "spot returned empty")
                return []
            # Filter to requested codes
            code_set = {c.split(".")[0] if "." in c else c for c in ts_codes}
            for row in all_spot:
                if row.get("code", "") in code_set:
                    result.append(
                        {
                            "ts_code": row.get("code", ""),
                            "name": row.get("name", ""),
                            "pe": row.get("pe"),
                            "pb": row.get("pb"),
                            "total_mv": row.get("market_cap"),
                            "price": row.get("price"),
                            "change_pct": row.get("change_pct"),
                            "turnover": row.get("turnover"),
                        }
                    )
            await self._record("akshare", "success")
        except Exception as e:
            logger.warning("AkShare stock spot failed: %s", e)
            await self._record("akshare", "failed", str(e))
        return result

    async def get_stock_basic_info(self) -> list[dict]:
        try:
            result = await self._ak.get_stock_list()
            await self._record("akshare", "success")
            return result
        except Exception as e:
            logger.warning("AkShare stock list failed: %s", e)
            await self._record("akshare", "failed", str(e))
            return []

    # -- Macro Data -----------------------------------------------------------

    async def get_macro_indicators(self) -> dict:
        shibor_overnight = None
        pmi = None
        cpi = None
        try:
            shibor_data = await self._ak.get_shibor()
            shibor_overnight = shibor_data.get("overnight") if shibor_data else None
            pmi = await self._ak.get_pmi()
            cpi = await self._ak.get_cpi()
            await self._record("akshare", "success")
        except Exception as e:
            logger.warning("Macro indicators fetch failed: %s", e)
            await self._record("akshare", "partial", str(e))
        return {"shibor_overnight": shibor_overnight, "pmi": pmi, "cpi": cpi}

    # -- Capital Flow ---------------------------------------------------------

    async def get_northbound_flow(self) -> dict:
        try:
            result = await self._ak.get_northbound_flow()
            await self._record("akshare", "success")
            return result
        except Exception as e:
            logger.warning("Northbound flow failed: %s", e)
            await self._record("akshare", "failed", str(e))
            return {}

    # -- News & Announcements -------------------------------------------------

    async def get_stock_news(self, stock_code: str, limit: int | None = None) -> list[dict]:
        lim = limit if limit is not None else self._news_limit
        try:
            result = await self._ak.get_stock_news(stock_code, lim)
            await self._record("akshare", "success")
            return result
        except Exception as e:
            logger.warning("Stock news failed: %s", e)
            await self._record("akshare", "failed", str(e))
            return []

    async def get_announcements(self, stock_code: str, limit: int | None = None) -> list[dict]:
        lim = limit if limit is not None else self._news_limit
        try:
            result = await self._ak.get_announcements(stock_code, lim)
            await self._record("akshare", "success")
            return result
        except Exception as e:
            logger.warning("Announcements failed: %s", e)
            await self._record("akshare", "failed", str(e))
            return []

    # -- Status ---------------------------------------------------------------

    async def get_source_status(self, date: str) -> list[dict]:
        return self._memory.get_source_status(date)

    async def _record_source_status(
        self,
        source: str,
        status: str,
        error: str | None = None,
    ) -> None:
        self._memory.save_source_status(source, status, error)

    async def _record(self, source: str, status: str, error: str | None = None) -> None:
        try:
            await self._record_source_status(source, status, error)
        except Exception:
            logger.warning("Failed to record source status for %s", source, exc_info=True)


_AK_INDEX_SYMBOLS = {
    "shanghai": "sh000001",
    "shenzhen": "sz399001",
    "chinext": "sz399006",
    "star50": "sh000688",
}
