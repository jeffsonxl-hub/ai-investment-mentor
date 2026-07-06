# Tests for TuShareClient component.
import os, sys, pytest
from unittest.mock import MagicMock, patch
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _make_df(records: list[dict]):
    """Helper to create a DataFrame for TuShare mock returns."""
    return pd.DataFrame(records)


@pytest.fixture
def mock_tushare():
    """Provide a mock tushare module with a pro_api() function."""
    mock = MagicMock(name="tushare")
    pro = MagicMock(name="pro_api")

    pro.daily.return_value = _make_df([
        {"ts_code": "000001.SZ", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2,
         "pre_close": 10.0, "change": 0.2, "pct_chg": 2.0, "vol": 1e8, "amount": 1e9},
    ])

    pro.stock_basic.return_value = _make_df([
        {"ts_code": "000001.SZ", "name": "Ping An Bank", "industry": "银行", "market": "主板", "list_date": "19910403"},
        {"ts_code": "600519.SH", "name": "Kweichow Moutai", "industry": "白酒", "market": "主板", "list_date": "20010827"},
    ])

    pro.daily_basic.return_value = _make_df([
        {"ts_code": "000001.SZ", "pe": 5.2, "pb": 0.8, "total_mv": 200000, "turnover_rate": 1.5},
    ])

    pro.income.return_value = _make_df([
        {"ts_code": "000001.SZ", "end_date": "20260630", "revenue": 5e10, "n_income": 1e10},
    ])

    pro.index_daily.return_value = _make_df([
        {"ts_code": "000001.SH", "trade_date": "20260706", "open": 3500.0, "high": 3520.0,
         "low": 3480.0, "close": 3510.0, "vol": 2e8, "amount": 3e11},
    ])

    mock.set_token = MagicMock()
    mock.pro_api.return_value = pro
    return mock


@pytest.mark.asyncio
async def test_get_daily(mock_tushare):
    from data.tu_share_client import TuShareClient
    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        result = await client.get_daily("20260706")
    assert len(result) == 1
    assert result[0]["ts_code"] == "000001.SZ"


@pytest.mark.asyncio
async def test_get_stock_basic(mock_tushare):
    from data.tu_share_client import TuShareClient
    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        result = await client.get_stock_basic()
    assert len(result) == 2
    assert result[0]["name"] == "Ping An Bank"


@pytest.mark.asyncio
async def test_get_daily_basic(mock_tushare):
    from data.tu_share_client import TuShareClient
    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        result = await client.get_daily_basic("20260706")
    assert len(result) == 1
    assert result[0]["pe"] == 5.2


@pytest.mark.asyncio
async def test_get_income(mock_tushare):
    from data.tu_share_client import TuShareClient
    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        result = await client.get_income(["000001.SZ"], "20260630")
    assert len(result) == 1
    assert result[0]["revenue"] == 5e10


@pytest.mark.asyncio
async def test_get_index_daily(mock_tushare):
    from data.tu_share_client import TuShareClient
    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        result = await client.get_index_daily("000001.SH", "20260701", "20260706")
    assert len(result) == 1
    assert result[0]["close"] == 3510.0


@pytest.mark.asyncio
async def test_raises_datafetch_error_on_failure(mock_tushare):
    from data.tu_share_client import TuShareClient
    from data.exceptions import DataFetchError

    mock_tushare.pro_api.return_value.daily.side_effect = RuntimeError("API down")

    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        with pytest.raises(DataFetchError, match="tushare"):
            await client.get_daily("20260706")


@pytest.mark.asyncio
async def test_sequential_access_enforced(mock_tushare):
    """Two concurrent calls should run sequentially due to semaphore=1."""
    import asyncio, time
    from data.tu_share_client import TuShareClient

    call_order = []

    def slow_daily(**kwargs):
        call_order.append("start")
        time.sleep(0.05)
        call_order.append("end")
        return _make_df([{"ts_code": "000001.SZ"}])

    mock_tushare.pro_api.return_value.daily = MagicMock(side_effect=slow_daily)

    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        t1 = asyncio.create_task(client.get_daily("20260706"))
        t2 = asyncio.create_task(client.get_daily("20260706"))
        await asyncio.gather(t1, t2)

    # Sequential execution: start, end, start, end (interleaved would be start, start)
    assert call_order == ["start", "end", "start", "end"]


@pytest.mark.asyncio
async def test_empty_dataframe_returns_empty_list(mock_tushare):
    from data.tu_share_client import TuShareClient

    import pandas as pd
    mock_tushare.pro_api.return_value.daily.return_value = pd.DataFrame()

    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        result = await client.get_daily("20260706")
    assert result == []


@pytest.mark.asyncio
async def test_none_dataframe_returns_empty_list(mock_tushare):
    from data.tu_share_client import TuShareClient

    mock_tushare.pro_api.return_value.daily.return_value = None

    client = TuShareClient("fake_token")
    with patch.dict("sys.modules", {"tushare": mock_tushare}):
        result = await client.get_daily("20260706")
    assert result == []

