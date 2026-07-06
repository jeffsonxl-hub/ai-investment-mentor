"""Smoke tests against real AkShare and TuShare libraries.

Requires TUSHARE_TOKEN in .env. Skipped if token is missing.
Run: python -m pytest tests/test_integration.py -v
"""

import math, os, sys, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(scope="module")
def real_ak_client():
    from data.ak_share_client import AkShareClient
    return AkShareClient()


@pytest.fixture(scope="module")
def real_ts_client():
    from config import load_config
    config = load_config()
    if not config.tushare_token:
        pytest.skip("TUSHARE_TOKEN not set")
    from data.tu_share_client import TuShareClient
    return TuShareClient(token=config.tushare_token)


# -- TuShare integration tests --

@pytest.mark.integration
@pytest.mark.asyncio
async def test_tushare_lazy_import_does_not_crash(real_ts_client):
    """_get_pro() should create a working pro_api without PermissionError."""
    pro = real_ts_client._get_pro()
    assert pro is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tushare_stock_basic_returns_data(real_ts_client):
    """get_stock_basic should return a real stock list."""
    from data.exceptions import DataFetchError
    try:
        result = await real_ts_client.get_stock_basic()
        assert isinstance(result, list)
        assert len(result) > 100
        assert "ts_code" in result[0]
        assert "name" in result[0]
    except DataFetchError as e:
        if "频率超限" in str(e):
            pytest.skip("TuShare rate limit reached (1/hour for stock_basic)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tushare_daily_returns_data(real_ts_client):
    """get_daily should work for a recent trading date."""
    result = await real_ts_client.get_daily("20260703")
    assert isinstance(result, list)


# -- AkShare integration tests --

@pytest.mark.integration
@pytest.mark.asyncio
async def test_akshare_lazy_import_does_not_crash(real_ak_client):
    """_get_ak() should import akshare without error."""
    ak = real_ak_client._get_ak()
    assert ak is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_akshare_shibor_returns_data(real_ak_client):
    """get_shibor should return a dict."""
    result = await real_ak_client.get_shibor()
    assert isinstance(result, dict)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_akshare_pmi_returns_clean_float(real_ak_client):
    """get_pmi should return float or None, never nan/inf."""
    result = await real_ak_client.get_pmi()
    if result is not None:
        assert isinstance(result, float)
        assert not math.isnan(result)
        assert not math.isinf(result)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_akshare_cpi_returns_clean_float(real_ak_client):
    """get_cpi should return float or None, never nan/inf."""
    result = await real_ak_client.get_cpi()
    if result is not None:
        assert isinstance(result, float)
        assert not math.isnan(result)
        assert not math.isinf(result)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_akshare_stock_news_returns_data(real_ak_client):
    """get_stock_news should not raise TypeError (parameter name check)."""
    result = await real_ak_client.get_stock_news("600519", limit=3)
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_akshare_northbound_flow_returns_data(real_ak_client):
    """get_northbound_flow should return a dict."""
    result = await real_ak_client.get_northbound_flow()
    assert isinstance(result, dict)
