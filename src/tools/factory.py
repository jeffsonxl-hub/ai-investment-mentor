"""Factory - creates a fully-initialized ToolRegistry with all 34 Tools."""
from __future__ import annotations
from typing import TYPE_CHECKING
from .registry import ToolRegistry
from .data_tools import register_data_tools
from .analysis_tools import register_analysis_tools
from .memory_tools import register_memory_tools
from .llm_tools import register_llm_tools
from .synthesis_tools import register_synthesis_tools
if TYPE_CHECKING:
    from data.provider import DataProvider
    from memory.repository import MemoryRepository

def create_tool_registry(provider: "DataProvider", memory: "MemoryRepository", llm_client=None) -> ToolRegistry:
    registry = ToolRegistry()
    register_data_tools(registry, provider)
    register_analysis_tools(registry)
    register_memory_tools(registry, memory)
    register_llm_tools(registry)
    _inject(registry, llm_client, ["summarize_article","classify_sentiment","extract_keywords","classify_event_type"])
    register_synthesis_tools(registry, provider, memory)
    _inject(registry, llm_client, ["generate_narrative"])
    return registry

def _inject(registry, llm_client, tool_names):
    if llm_client is None: return
    for name in tool_names:
        try:
            registry.get(name).dependencies["llm_client"] = llm_client
        except KeyError:
            continue
