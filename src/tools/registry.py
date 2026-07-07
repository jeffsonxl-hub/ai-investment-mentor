"""ToolRegistry - centralized Tool registration and dispatch."""

from __future__ import annotations

from typing import Any

from .tool import Tool


class ToolRegistry:
    """Central registry of all tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name!r} already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def get_for_agent(self, tool_names: list[str]) -> list[Tool]:
        missing = set(tool_names) - set(self._tools)
        if missing:
            raise KeyError(f"Unknown tools: {sorted(missing)}")
        return [self._tools[name] for name in tool_names]

    def export_for_llm(self, tool_names: list[str]) -> list[dict]:
        return [t.to_openai_schema() for t in self.get_for_agent(tool_names)]

    async def execute(self, name: str, **kwargs: Any) -> Any:
        tool = self.get(name)
        return await tool.execute(**kwargs)

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    @property
    def tool_names(self) -> list[str]:
        return sorted(self._tools)

    def by_category(self, category: str) -> list[Tool]:
        return [t for t in self._tools.values() if t.category == category]
