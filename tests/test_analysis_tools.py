"""Tests for Analysis Tools - pure math."""
import pytest
from src.tools.analysis_tools import _rsi_impl, _macd_impl, _ma_impl, _bollinger_impl, _volume_profile_impl, _returns_impl

@pytest.mark.asyncio
async def test_rsi_uptrend():
    prices = [100.0 + i * 0.5 for i in range(20)]
    result = await _rsi_impl(prices, period=14)
    assert result["rsi"] is not None
    assert result["rsi"] >= 95.0

@pytest.mark.asyncio
async def test_rsi_insufficient():
    result = await _rsi_impl([100.0, 101.0], period=14)
    assert "error" in result

@pytest.mark.asyncio
async def test_macd_basic():
    prices = [100.0 + i * 0.1 for i in range(40)]
    result = await _macd_impl(prices)
    assert "macd" in result
    assert "signal" in result
    assert "histogram" in result

@pytest.mark.asyncio
async def test_macd_insufficient():
    result = await _macd_impl([100.0, 101.0, 102.0])
    assert "error" in result

@pytest.mark.asyncio
async def test_ma_basic():
    prices = list(range(1, 101))
    result = await _ma_impl(prices, periods=[5, 10])
    assert result["ma5"] == 98.0
    assert result["ma10"] == 95.5

@pytest.mark.asyncio
async def test_ma_default_periods():
    prices = list(range(1, 101))
    result = await _ma_impl(prices)
    assert "ma5" in result
    assert "ma60" in result

@pytest.mark.asyncio
async def test_ma_insufficient():
    result = await _ma_impl([1.0, 2.0, 3.0], periods=[10])
    assert result["ma10"] is None

@pytest.mark.asyncio
async def test_bollinger_flat():
    prices = [50.0] * 25
    result = await _bollinger_impl(prices, period=20)
    assert result["upper"] == 50.0
    assert result["middle"] == 50.0
    assert result["lower"] == 50.0

@pytest.mark.asyncio
async def test_bollinger_spread():
    prices = [90.0 + i for i in range(25)]
    result = await _bollinger_impl(prices, period=20)
    assert result["upper"] > result["middle"] > result["lower"]

@pytest.mark.asyncio
async def test_bollinger_insufficient():
    result = await _bollinger_impl([100.0], period=20)
    assert "error" in result

@pytest.mark.asyncio
async def test_volume_profile_basic():
    prices = [10.0, 11.0, 12.0, 13.0, 14.0]
    volumes = [1000, 2000, 3000, 2000, 1000]
    result = await _volume_profile_impl(prices, volumes, bins=3)
    assert len(result["profile"]) == 3
    assert sum(b["volume"] for b in result["profile"]) == 9000

@pytest.mark.asyncio
async def test_volume_profile_mismatch():
    result = await _volume_profile_impl([1.0, 2.0], [100.0])
    assert "error" in result

@pytest.mark.asyncio
async def test_returns_basic():
    prices = [100.0, 102.0, 105.0, 103.0, 108.0]
    result = await _returns_impl(prices, period=1)
    assert result["current_return"] == pytest.approx(4.8544, rel=1e-3)
    assert len(result["returns"]) == 4

@pytest.mark.asyncio
async def test_returns_insufficient():
    result = await _returns_impl([100.0], period=1)
    assert "error" in result
