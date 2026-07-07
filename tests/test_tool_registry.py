"""Tests for ToolRegistry."""
import pytest
from src.tools.tool import Tool, ToolParameter
from src.tools.registry import ToolRegistry

@pytest.fixture
def registry():
    async def _echo(**kw): return kw
    r = ToolRegistry()
    r.register(Tool("alpha","Alpha tool",[],_echo,"data"))
    r.register(Tool("beta","Beta tool",[],_echo,"analysis"))
    r.register(Tool("gamma","Gamma tool",[],_echo,"memory"))
    return r

def test_register_tool(registry):
    assert registry.tool_count == 3

def test_register_duplicate_raises(registry):
    with pytest.raises(ValueError, match="already registered"):
        async def _nop(**kw): return None
        registry.register(Tool("alpha","dup",[],_nop))

def test_get_tool(registry):
    assert registry.get("alpha").name == "alpha"

def test_get_unknown_raises(registry):
    with pytest.raises(KeyError):
        registry.get("nonexistent")

def test_get_for_agent(registry):
    tools = registry.get_for_agent(["alpha","beta"])
    assert len(tools) == 2
    assert {t.name for t in tools} == {"alpha","beta"}

def test_get_for_agent_unknown_raises(registry):
    with pytest.raises(KeyError, match="Unknown tools"):
        registry.get_for_agent(["alpha","nonexistent"])

def test_export_for_llm(registry):
    schemas = registry.export_for_llm(["alpha"])
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "alpha"

@pytest.mark.asyncio
async def test_execute_dispatches(registry):
    result = await registry.execute("alpha")
    assert result == {}

@pytest.mark.asyncio
async def test_execute_unknown(registry):
    with pytest.raises(KeyError):
        await registry.execute("nonexistent")

def test_tool_names(registry):
    assert registry.tool_names == ["alpha","beta","gamma"]

def test_by_category(registry):
    assert len(registry.by_category("data")) == 1
    assert registry.by_category("data")[0].name == "alpha"
