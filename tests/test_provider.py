import os, sys, pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_ts():
    ts = AsyncMock()
    ts.get_index_daily.return_value = [
        {"ts_code": "000001.SH", "trade_date": "20260706", "close": 3510.0, "open": 3500.0, "high": 3520.0, "low": 3480.0},
    ]
    ts.get_daily.return_value = []
    ts.get_stock_basic.return_value = [
        {"ts_code": "000001.SZ", "name": "Ping An", "industry": "Bank", "market": "主板", "list_date": "19910403"},
    ]
    ts.get_daily_basic.return_value = [
        {"ts_code": "000001.SZ", "pe": 5.2, "pb": 0.8, "total_mv": 200000},
    ]
    ts.get_income.return_value = [
        {"ts_code": "000001.SZ", "revenue": 5e10, "n_income": 1e10},
    ]
    return ts


@pytest.fixture
def mock_ak():
    ak = AsyncMock()
    ak.get_index_daily.return_value = []
    ak.get_sector_performance.return_value = [
        {"sector_name": "半导体", "pct_change": 3.5},
    ]
    ak.get_shibor.return_value = {"overnight": 1.85, "1w": 2.05}
    ak.get_pmi.return_value = 50.5
    ak.get_cpi.return_value = 0.3
    ak.get_northbound_flow.return_value = {"sh_net": 10.0, "sz_net": 5.0, "total_net": 15.0}
    ak.get_stock_news.return_value = [
        {"title": "News", "content": "Body", "publish_time": "2026-07-06", "source": "East Money"},
    ]
    ak.get_stock_list.return_value = [{"code": "000001", "name": "Ping An"}]
    ak.get_stock_spot.return_value = [
        {"code": "000001", "name": "Ping An", "pe": 5.2, "pb": 0.8, "market_cap": 200000, "price": 12.5, "change_pct": 2.0, "turnover": 1.5},
    ]
    ak.get_announcements.return_value = [
        {"title": "Ann", "type": "", "publish_date": "2026-07-06", "summary": "Summary"},
    ]
    return ak


@pytest.fixture
def mock_memory():
    mem = MagicMock()
    mem.save_source_status = MagicMock()
    mem.get_source_status.return_value = []
    return mem


@pytest.mark.asyncio
async def test_get_market_snapshot_full(mock_ts, mock_ak, mock_memory):
    """Full market snapshot when both sources succeed."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    result = await provider.get_market_snapshot("2026-07-06")

    assert result["date"] == "2026-07-06"
    assert "indices" in result
    assert "macro" in result
    assert "northbound_flow" in result
    assert result["data_quality"] == "full"


@pytest.mark.asyncio
async def test_get_market_snapshot_akshare_fails(mock_ts, mock_ak, mock_memory):
    """Market snapshot should degrade when AkShare index data fails."""
    from data.provider import DataProvider

    mock_ak.get_index_daily.side_effect = RuntimeError("AkShare down")

    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory)
    result = await provider.get_market_snapshot("2026-07-06")

    assert result["data_quality"] in ("degraded", "failed")


@pytest.mark.asyncio
async def test_get_market_snapshot_akshare_macro_fails(mock_ts, mock_ak, mock_memory):
    """Market snapshot when AkShare macro fails — should still return partial."""
    from data.provider import DataProvider

    mock_ak.get_shibor.side_effect = RuntimeError("down")
    mock_ak.get_pmi.return_value = None  # Already returned by fixture, but let side_effect take priority

    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)
    result = await provider.get_market_snapshot("2026-07-06")

    assert result["data_quality"] in ("degraded", "full")


@pytest.mark.asyncio
async def test_get_fundamental_snapshot(mock_ts, mock_ak, mock_memory):
    """get_fundamental_snapshot should merge daily_basic and income."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    result = await provider.get_fundamental_snapshot(["000001.SZ"], "2026-07-06")

    assert len(result) > 0
    assert "pe" in result[0] or "ts_code" in result[0]


@pytest.mark.asyncio
async def test_get_fundamental_snapshot_partial_failure(mock_ts, mock_ak, mock_memory):
    """Should return available data even when income fails."""
    from data.exceptions import DataFetchError
    from data.provider import DataProvider

    mock_ak.get_stock_spot.side_effect = RuntimeError("AkShare spot down")

    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)
    result = await provider.get_fundamental_snapshot(["000001.SZ"], "2026-07-06")

    # Should still return daily_basic data
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_macro_indicators(mock_ts, mock_ak, mock_memory):
    """get_macro_indicators should return SHIBOR, PMI, CPI."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    result = await provider.get_macro_indicators()

    assert result["shibor_overnight"] == 1.85
    assert result["pmi"] == 50.5
    assert result["cpi"] == 0.3


@pytest.mark.asyncio
async def test_get_northbound_flow(mock_ts, mock_ak, mock_memory):
    """get_northbound_flow should delegate to AkShare."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    result = await provider.get_northbound_flow()

    assert result["total_net"] == 15.0
    mock_ak.get_northbound_flow.assert_called_once()


@pytest.mark.asyncio
async def test_get_stock_news(mock_ts, mock_ak, mock_memory):
    """get_stock_news should delegate to AkShare."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    result = await provider.get_stock_news("600519")

    assert len(result) == 1
    assert result[0]["title"] == "News"


@pytest.mark.asyncio
async def test_get_announcements(mock_ts, mock_ak, mock_memory):
    """get_announcements should delegate to AkShare."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    result = await provider.get_announcements("600519")

    assert len(result) == 1
    assert result[0]["title"] == "Ann"


@pytest.mark.asyncio
async def test_get_sector_performance(mock_ts, mock_ak, mock_memory):
    """get_sector_performance should delegate to AkShare."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    result = await provider.get_sector_performance()

    assert len(result) == 1
    assert result[0]["sector_name"] == "半导体"


@pytest.mark.asyncio
async def test_get_stock_basic_info(mock_ts, mock_ak, mock_memory):
    """get_stock_basic_info should delegate to AkShare."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory)

    result = await provider.get_stock_basic_info()

    assert len(result) == 1
    assert result[0]["name"] == "Ping An"


@pytest.mark.asyncio
async def test_source_status_recorded_on_success(mock_ts, mock_ak, mock_memory):
    """Source status should be recorded after successful operations."""
    from data.provider import DataProvider
    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)

    await provider.get_macro_indicators()

    # At least one source status should have been recorded
    assert mock_memory.save_source_status.call_count >= 1


@pytest.mark.asyncio
async def test_source_status_recorded_on_failure(mock_ts, mock_ak, mock_memory):
    """Source status should be recorded even on failure."""
    from data.provider import DataProvider

    mock_ak.get_stock_news.side_effect = RuntimeError("down")

    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)
    await provider.get_stock_news("600519")

    # Should still record status
    assert mock_memory.save_source_status.call_count >= 1


@pytest.mark.asyncio
async def test_get_source_status(mock_ts, mock_ak, mock_memory):
    """get_source_status should delegate to MemoryRepository."""
    from data.provider import DataProvider

    mock_memory.get_source_status.return_value = [
        {"date": "2026-07-06", "source": "tushare", "status": "success"},
    ]

    provider = DataProvider(ak_share_client=mock_ak, memory_repo=mock_memory, tu_share_client=mock_ts)
    result = await provider.get_source_status("2026-07-06")

    assert len(result) == 1
    assert result[0]["source"] == "tushare"
