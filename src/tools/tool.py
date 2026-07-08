"""Tool - a callable capability exposed to an Agent LLM via function calling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, ClassVar


@dataclass
class ToolParameter:
    """A single parameter in a Tool JSON Schema."""

    name: str
    type: str
    description: str
    required: bool = True
    enum: list[str] | None = None
    default: Any = None


@dataclass
class Tool:
    """A callable capability exposed to an Agent LLM."""

    name: str
    description: str
    parameters: list[ToolParameter]
    func: Callable[..., Awaitable[Any]]
    category: str = ""
    dependencies: dict[str, Any] = field(default_factory=dict)

    def to_openai_schema(self) -> dict:
        properties = {}
        required_list = []
        for p in self.parameters:
            prop: dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop
            if p.required:
                required_list.append(p.name)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_list,
                },
            },
        }

    def to_mcp_tool_schema(self) -> dict:
        s = self.to_openai_schema()
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": s["function"]["parameters"],
        }

    _TYPE_MAP: ClassVar[dict[str, type | tuple[type, ...]]] = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    def _validate_params(self, **kwargs: Any) -> None:
        for p in self.parameters:
            if p.name not in kwargs:
                continue
            expected = self._TYPE_MAP.get(p.type)
            if expected is None:
                continue
            if not isinstance(kwargs[p.name], expected):
                raise TypeError(
                    f"Tool {self.name!r} parameter {p.name!r} "
                    f"expected {p.type}, got {type(kwargs[p.name]).__name__}"
                )

    async def execute(self, **kwargs: Any) -> Any:
        self._validate_params(**kwargs)
        merged: dict[str, Any] = {**self.dependencies, **kwargs}
        return await self.func(**merged)
