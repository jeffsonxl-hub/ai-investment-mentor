"""Analysis Tools - pure math, no LLM, no external calls."""
from __future__ import annotations
import statistics
from .tool import Tool, ToolParameter

def register_analysis_tools(registry) -> None:
    registry.register(Tool(
        name="calculate_rsi",
        description="Calculate RSI for a price series. Uses Wilder smoothing.",
        parameters=[
            ToolParameter("prices","array","List of closing prices, oldest first"),
            ToolParameter("period","integer","Lookback period",required=False,default=14),
        ],
        func=_rsi_impl,
        category="analysis",
    ))
    registry.register(Tool(
        name="calculate_macd",
        description="Calculate MACD line, signal line, and histogram.",
        parameters=[
            ToolParameter("prices","array","List of closing prices"),
            ToolParameter("fast","integer","Fast EMA",required=False,default=12),
            ToolParameter("slow","integer","Slow EMA",required=False,default=26),
            ToolParameter("signal","integer","Signal line",required=False,default=9),
        ],
        func=_macd_impl,
        category="analysis",
    ))
    registry.register(Tool(
        name="calculate_moving_averages",
        description="Calculate simple moving averages for multiple periods.",
        parameters=[
            ToolParameter("prices","array","List of closing prices"),
            ToolParameter("periods","array","MA periods",required=False),
        ],
        func=_ma_impl,
        category="analysis",
    ))
    registry.register(Tool(
        name="calculate_bollinger_bands",
        description="Calculate Bollinger Bands: upper, middle, lower.",
        parameters=[
            ToolParameter("prices","array","List of closing prices"),
            ToolParameter("period","integer","SMA period",required=False,default=20),
            ToolParameter("std_dev","number","Std dev multiplier",required=False,default=2),
        ],
        func=_bollinger_impl,
        category="analysis",
    ))
    registry.register(Tool(
        name="calculate_volume_profile",
        description="Calculate volume distribution across price levels.",
        parameters=[
            ToolParameter("prices","array","List of prices"),
            ToolParameter("volumes","array","List of volumes"),
            ToolParameter("bins","integer","Price bins",required=False,default=10),
        ],
        func=_volume_profile_impl,
        category="analysis",
    ))
    registry.register(Tool(
        name="calculate_returns",
        description="Calculate period-over-period returns.",
        parameters=[
            ToolParameter("prices","array","List of prices"),
            ToolParameter("period","integer","Return period in days",required=False,default=1),
        ],
        func=_returns_impl,
        category="analysis",
    ))

async def _rsi_impl(prices, period=14, **kw) -> dict:
    if len(prices) < period + 1:
        return {"rsi": None, "error": f"Need {period + 1} prices, got {len(prices)}"}
    gains, losses = [], []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return {"rsi": 100.0}
    rs = avg_gain / avg_loss
    return {"rsi": round(100.0 - (100.0 / (1.0 + rs)), 2)}

async def _macd_impl(prices, fast=12, slow=26, signal=9, **kw) -> dict:
    if len(prices) < slow + signal:
        return {"error": f"Need {slow + signal} prices, got {len(prices)}"}
    def _ema(data, period):
        result, mult = [data[0]], 2.0 / (period + 1)
        for i in range(1, len(data)):
            result.append((data[i] - result[-1]) * mult + result[-1])
        return result
    ema_fast, ema_slow = _ema(prices, fast), _ema(prices, slow)
    macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]
    signal_line = _ema(macd_line, signal)
    histogram = [macd_line[i] - signal_line[i] for i in range(len(prices))]
    return {"macd": round(macd_line[-1], 4), "signal": round(signal_line[-1], 4), "histogram": round(histogram[-1], 4)}

async def _ma_impl(prices, periods=None, **kw) -> dict:
    if periods is None:
        periods = [5, 10, 20, 60]
    result = {}
    for p in periods:
        result[f"ma{p}"] = round(sum(prices[-p:]) / p, 2) if len(prices) >= p else None
    return result

async def _bollinger_impl(prices, period=20, std_dev=2, **kw) -> dict:
    if len(prices) < period:
        return {"error": f"Need {period} prices, got {len(prices)}"}
    import statistics
    window = prices[-period:]
    middle = sum(window) / period
    stdev = statistics.stdev(window)
    return {"upper": round(middle + std_dev * stdev, 2), "middle": round(middle, 2), "lower": round(middle - std_dev * stdev, 2)}

async def _volume_profile_impl(prices, volumes, bins=10, **kw) -> dict:
    if len(prices) != len(volumes):
        return {"error": "prices and volumes must have same length"}
    if not prices:
        return {"profile": []}
    lo, hi = min(prices), max(prices)
    if lo == hi:
        return {"profile": [{"price_level": round(lo, 2), "volume": sum(volumes)}]}
    bin_width = (hi - lo) / bins
    profile = [{"price_level": 0.0, "volume": 0.0} for _ in range(bins)]
    for p, v in zip(prices, volumes):
        idx = min(int((p - lo) / bin_width), bins - 1)
        profile[idx]["volume"] += v
        profile[idx]["price_level"] = round(lo + bin_width * (idx + 0.5), 2)
    return {"profile": profile}

async def _returns_impl(prices, period=1, **kw) -> dict:
    if len(prices) < period + 1:
        return {"error": f"Need {period + 1} prices, got {len(prices)}"}
    returns = []
    for i in range(period, len(prices)):
        ret = None if prices[i - period] == 0 else (prices[i] - prices[i - period]) / prices[i - period] * 100
        returns.append(round(ret, 4) if ret is not None else None)
    return {"current_return": returns[-1] if returns else None, "returns": returns}
