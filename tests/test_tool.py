"""Tests for Tool and ToolParameter."""
import pytest
from src.tools.tool import Tool, ToolParameter

@pytest.fixture
def sample_tool():
    async def _echo(**kwargs): return kwargs
    return Tool(
        name="test_tool", description="A test tool.",
        parameters=[
            ToolParameter("symbol","string","Stock symbol",enum=["sh000001","sz399001"]),
            ToolParameter("period","integer","Lookback",required=False,default=14),
        ],
        func=_echo, category="analysis", dependencies={"secret":"injected_value"},
    )

def test_to_openai_schema(sample_tool):
    s = sample_tool.to_openai_schema()
    assert s["type"] == "function"
    assert s["function"]["name"] == "test_tool"
    assert "symbol" in s["function"]["parameters"]["properties"]
    assert s["function"]["parameters"]["properties"]["symbol"]["enum"] == ["sh000001","sz399001"]
    assert "period" not in s["function"]["parameters"]["required"]

def test_to_mcp_tool_schema(sample_tool):
    s = sample_tool.to_mcp_tool_schema()
    assert s["name"] == "test_tool"
    assert "inputSchema" in s
    assert s["inputSchema"]["type"] == "object"

def test_validate_passes(sample_tool):
    sample_tool._validate_params(symbol="sh000001", period=14)

def test_validate_raises_type_error(sample_tool):
    with pytest.raises(TypeError):
        sample_tool._validate_params(symbol=123, period=14)

def test_validate_raises_type_error_int(sample_tool):
    with pytest.raises(TypeError):
        sample_tool._validate_params(symbol="sh000001", period="fourteen")

def test_validate_skips_missing(sample_tool):
    sample_tool._validate_params(symbol="sz399001")

@pytest.mark.asyncio
async def test_execute_merges_deps(sample_tool):
    result = await sample_tool.execute(symbol="sh000001", period=14)
    assert result["symbol"] == "sh000001"
    assert result["period"] == 14
    assert result["secret"] == "injected_value"

@pytest.mark.asyncio
async def test_execute_raises_on_bad_type(sample_tool):
    with pytest.raises(TypeError):
        await sample_tool.execute(symbol=456)

@pytest.mark.asyncio
async def test_execute_no_deps():
    async def _nop(**kw): return kw
    t = Tool("x","desc",[],_nop)
    r = await t.execute()
    assert r == {}
