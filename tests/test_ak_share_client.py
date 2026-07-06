"""Tests for AkShareClient component."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_akshare():
    """Provide a mock akshare module with all required functions returning DataFrames."""
    import pandas as pd

    mock = MagicMock(name="akshare")

    # stock_zh_index_daily — returns OHLCV dataframe
    idx_df = pd.DataFrame({
        "date": ["2026-07-06"],
        "open": [3500.0],
        "high": [3520.0],
        "low": [3480.0],
        "close": [3510.0],
        "volume": [2.5e10],
    })
    mock.stock_zh_index_daily.return_value = idx_df

    # stock_board_industry_summary_ths — sector performance
    sector_df = pd.DataFrame({
        "板块名称": ["半导体", "新能源"],
        "涨跌幅": [3.5, -1.2],
    })
    mock.stock_board_industry_summary_ths.return_value = sector_df

    # macro_china_shibor_all — SHIBOR rates
    shibor_df = pd.DataFrame([
        {"O/N": 1.85, "1W": 2.05, "2W": 2.15, "1M": 2.30},
        {"O/N": 1.90, "1W": 2.10, "2W": 2.20, "1M": 2.35},
    ])
    mock.macro_china_shibor_all.return_value = shibor_df

    # macro_china_pmi — PMI
    mock.macro_china_pmi.return_value = pd.DataFrame([{"制造业": 50.5}, {"制造业": 50.3}])

    # macro_china_cpi_yearly — CPI
    mock.macro_china_cpi_yearly.return_value = pd.DataFrame([{"cpi": 0.3}, {"cpi": 0.5}])

    # stock_hsgt_north_net_flow_in_em — northbound flow
    flow_df = pd.DataFrame([
        {"沪股通": 10.0, "深股通": 5.0, "北上资金": 15.0},
        {"沪股通": 12.0, "深股通": 8.0, "北上资金": 20.0},
    ])
    mock.stock_hsgt_north_net_flow_in_em.return_value = flow_df

    # stock_news_em — news
    news_df = pd.DataFrame([
        {"标题": "Test News 1", "内容": "Content 1", "发布时间": "2026-07-06", "文章来源": "East Money"},
        {"标题": "Test News 2", "内容": "Content 2", "发布时间": "2026-07-05", "文章来源": "Sina"},
    ])
    mock.stock_news_em.return_value = news_df

    # stock_info_sh_name_code — announcements
    mock.stock_info_sh_name_code.return_value = pd.DataFrame([
        {"name": "Announcement 1", "date": "2026-07-06", "content": "Summary 1"},
    ])

    return mock


@pytest.mark.asyncio
async def test_get_index_daily(mock_akshare):
    """get_index_daily should return normalized OHLCV dicts."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_index_daily("sh000001")
    assert len(result) > 0
    assert "date" in result[0]
    assert "close" in result[0]


@pytest.mark.asyncio
async def test_get_sector_performance(mock_akshare):
    """get_sector_performance should return sector name and pct_change."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_sector_performance()
    assert len(result) == 2
    assert result[0]["sector_name"] == "半导体"
    assert result[0]["pct_change"] == 3.5


@pytest.mark.asyncio
async def test_get_shibor(mock_akshare):
    """get_shibor should return latest row with rate keys."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_shibor()
    assert result["overnight"] == 1.90
    assert "1w" in result


@pytest.mark.asyncio
async def test_get_pmi(mock_akshare):
    """get_pmi should return a float value."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_pmi()
    assert isinstance(result, float)


@pytest.mark.asyncio
async def test_get_cpi(mock_akshare):
    """get_cpi should return a float value."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_cpi()
    assert isinstance(result, float)


@pytest.mark.asyncio
async def test_get_northbound_flow(mock_akshare):
    """get_northbound_flow should return latest flow data."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_northbound_flow()
    assert result["sh_net"] == 12.0
    assert result["sz_net"] == 8.0


@pytest.mark.asyncio
async def test_get_stock_news(mock_akshare):
    """get_stock_news should return normalized news articles."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_stock_news("600519")
    assert len(result) == 2
    assert "title" in result[0]
    assert "publish_time" in result[0]


@pytest.mark.asyncio
async def test_get_announcements(mock_akshare):
    """get_announcements should return normalized announcement dicts."""
    from data.ak_share_client import AkShareClient

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_announcements("600519")
    assert len(result) >= 1
    assert "title" in result[0]


@pytest.mark.asyncio
async def test_failure_returns_empty_list(mock_akshare):
    """When akshare raises, methods should return empty results, not raise."""
    from data.ak_share_client import AkShareClient

    mock_akshare.stock_news_em.side_effect = RuntimeError("Upstream error")

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_stock_news("600519")
    assert result == []


@pytest.mark.asyncio
async def test_failure_returns_empty_dict(mock_akshare):
    """Dict-returning methods should return {} on failure."""
    from data.ak_share_client import AkShareClient

    mock_akshare.macro_china_shibor_all.side_effect = RuntimeError("Boom")

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_shibor()
    assert result == {}


@pytest.mark.asyncio
async def test_failure_returns_none(mock_akshare):
    """Optional-returning methods should return None on failure."""
    from data.ak_share_client import AkShareClient

    mock_akshare.macro_china_pmi.side_effect = RuntimeError("Boom")

    client = AkShareClient()
    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        result = await client.get_pmi()
    assert result is None


@pytest.mark.asyncio
async def test_semaphore_limit_respected(mock_akshare):
    """Concurrent calls should not exceed the semaphore limit."""
    import asyncio
    from data.ak_share_client import AkShareClient

    client = AkShareClient(parallel_limit=2)

    # Slow mock to keep semaphore slots occupied
    async def slow_return(*args, **kwargs):
        await asyncio.sleep(0.1)
        return mock_akshare.stock_news_em.return_value
    mock_akshare.stock_news_em = MagicMock(side_effect=slow_return)

    with patch.dict("sys.modules", {"akshare": mock_akshare}):
        tasks = [client.get_stock_news("600519") for _ in range(4)]
        results = await asyncio.gather(*tasks)

    assert len(results) == 4
    # All returned results, none crashed
    for r in results:
        assert isinstance(r, list)

