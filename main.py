"""
main.py — MCP Server entry point with tool registration and invocation.

Implements a lightweight Model Context Protocol (MCP) server that:
  1. Registers available tools (currently: get_creator_metrics)
  2. Exposes a call_tool() method for agents to invoke tools by name
  3. Logs every invocation with timestamps for pipeline traceability

Architecture Note:
    In a production MCP deployment, this would be an HTTP/WebSocket server
    (similar to the FastAPI server in the prep_agent project). For this
    local demo, it's a direct Python import — agents call
    mcp_server.main.MCPServer().call_tool("get_creator_metrics") directly.

    The class-based design means swapping to HTTP requires changing only
    the transport layer, not the tool logic.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Optional

# IMPORTANT: Import config FIRST — it sets up UTF-8 encoding on Windows.
# Without this, the Unicode characters below (ℹ, ⚡, ✓, ⚠, ✗) would crash
# with UnicodeEncodeError on Windows terminals using cp1252 encoding.
import config  # noqa: F401 — imported for side-effect (UTF-8 setup)

# Project imports — the tool module we register with the MCP server
from mcp_server import analytics_tool


# ──────────────────────────────────────────────────────────────────────────────
# Console Styling Helpers
# ──────────────────────────────────────────────────────────────────────────────
# Each log line from the MCP server is prefixed with a colored icon and
# the label "MCP" so you can visually distinguish MCP output from agent
# output in the terminal during demos.
#
# Log levels and their icons:
#   INFO  → ℹ (cyan)    — Server startup, tool registration
#   CALL  → ⚡ (green)   — Tool invocation started
#   OK    → ✓ (green)   — Tool returned successfully
#   WARN  → ⚠ (yellow)  — Non-fatal warnings
#   ERROR → ✗ (red)     — Tool failures or unknown tool names

_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _log(level: str, msg: str) -> None:
    """Print a timestamped MCP server log message with colored level icon."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Map log level to a colored prefix string
    prefix = {
        "INFO":  f"{_CYAN}i MCP{_RESET}",
        "CALL":  f"{_GREEN}> MCP{_RESET}",
        "OK":    f"{_GREEN}+ MCP{_RESET}",
        "WARN":  f"{_YELLOW}! MCP{_RESET}",
        "ERROR": f"{_RED}x MCP{_RESET}",
    }.get(level, f"  MCP")
    print(f"     {_DIM}{timestamp}{_RESET}  {prefix}  {msg}")


# ──────────────────────────────────────────────────────────────────────────────
# MCP Server Class
# ──────────────────────────────────────────────────────────────────────────────
# The Model Context Protocol (MCP) is a standard for AI agents to interact
# with external tools and data sources. Instead of agents making direct API
# calls, they go through the MCP server, which:
#
#   1. REGISTERS tools at startup (like plugins)
#   2. VALIDATES tool calls before execution
#   3. LOGS every invocation for audit trail / debugging
#   4. WRAPS responses in a standard envelope format
#
# Think of it like a switchboard operator — agents say "I need creator
# metrics" and the MCP server routes that to the right tool function.
#
# DESIGN PATTERN: This uses the Registry Pattern (also called Service
# Locator). Tools are registered by name, and callers look them up by
# name at runtime. This decouples agents from specific tool implementations.

class MCPServer:
    """
    Lightweight Model Context Protocol server.

    Manages a registry of callable tools. Agents interact with external data
    sources exclusively through this server — never directly. This provides:
      - Centralized logging of all data access
      - A single point to swap mock tools for real API integrations
      - MCP-compliant tool discovery via list_tools()

    Usage:
        server = MCPServer()
        result = server.call_tool("get_creator_metrics")
    """

    def __init__(self) -> None:
        """Initialize the MCP server and register all available tools."""
        # Tool registry: maps tool_name → (callable_function, schema_dict)
        # The schema follows MCP's tool definition format so agents can
        # discover what tools are available and what parameters they accept.
        self._tools: dict[str, tuple[Callable, dict]] = {}

        # Tracks total invocations across all tools — used for unique
        # invocation IDs in response envelopes (useful for debugging)
        self._invocation_count: int = 0

        # ── Auto-register built-in tools on startup ──────────────────────
        self._register_builtin_tools()
        _log("INFO", f"Server initialized with {len(self._tools)} tool(s)")

    def _register_builtin_tools(self) -> None:
        """Register all tools defined in the mcp_server package."""
        self.register_tool(
            name="get_creator_metrics",
            handler=analytics_tool.get_creator_metrics,
            schema=analytics_tool.get_tool_schema(),
        )

    def register_tool(
        self,
        name: str,
        handler: Callable,
        schema: dict,
    ) -> None:
        """
        Register a new tool with the MCP server.

        Args:
            name:    Unique tool identifier (e.g., "get_creator_metrics").
            handler: Callable that implements the tool logic.
            schema:  MCP-compliant tool schema dict.
        """
        self._tools[name] = (handler, schema)
        _log("INFO", f"Registered tool: {_BOLD}{name}{_RESET}")

    def list_tools(self) -> list[dict]:
        """
        List all registered tools and their schemas.

        Returns:
            list[dict]: Array of tool schema objects for agent discovery.
        """
        return [schema for _, (_, schema) in self._tools.items()]

    def call_tool(self, tool_name: str, **kwargs: Any) -> dict:
        """
        Invoke a registered tool by name.

        This is the primary method agents use to interact with the MCP server.
        Every invocation is logged with timestamp and result summary.

        Args:
            tool_name: Name of the tool to call.
            **kwargs:  Arguments to pass to the tool handler.

        Returns:
            dict: Structured response envelope:
                {
                    "status": "success" | "error",
                    "tool": "get_creator_metrics",
                    "data": { ... },
                    "invocation_id": 1,
                    "timestamp": "2026-06-25T14:00:00+00:00"
                }

        Raises:
            ValueError: If the tool_name is not registered.
        """
        if tool_name not in self._tools:
            available = ", ".join(self._tools.keys())
            _log("ERROR", f"Unknown tool '{tool_name}'. Available: {available}")
            raise ValueError(
                f"MCP Error: Tool '{tool_name}' not found. "
                f"Available tools: [{available}]"
            )

        handler, schema = self._tools[tool_name]
        self._invocation_count += 1
        invocation_id = self._invocation_count

        _log("CALL", f"Invoking {_BOLD}{tool_name}{_RESET}  (invocation #{invocation_id})")

        try:
            # Execute the tool handler
            result = handler(**kwargs)

            _log("OK", f"{tool_name} returned successfully")

            return {
                "status": "success",
                "tool": tool_name,
                "data": result,
                "invocation_id": invocation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            _log("ERROR", f"{tool_name} failed: {exc}")
            return {
                "status": "error",
                "tool": tool_name,
                "error": str(exc),
                "invocation_id": invocation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# ──────────────────────────────────────────────────────────────────────────────
# Module-level Singleton Instance
# ──────────────────────────────────────────────────────────────────────────────
# DESIGN PATTERN: Singleton via module-level variable.
#
# Python modules are only executed once (on first import). So this MCPServer
# instance is created exactly once, no matter how many agents import it.
# All agents share the same server instance, which means:
#   - Tool registry is consistent across all agents
#   - Invocation count is global (tracks total calls from all agents)
#   - Logging shows the complete audit trail
#
# Usage from any agent:
#   from mcp_server.main import mcp_server
#   result = mcp_server.call_tool("get_creator_metrics")
mcp_server = MCPServer()
