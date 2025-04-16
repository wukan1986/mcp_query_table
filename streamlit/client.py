"""
MCP SSE Client - A Python client for interacting with Model Context Protocol (MCP) endpoints.

This module provides a client for connecting to MCP endpoints using Server-Sent Events (SSE),
listing available tools, and invoking tools with parameters.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import CallToolResult


@dataclass
class ToolParameter:
    """Represents a parameter for a tool.

    Attributes:
        name: Parameter name
        parameter_type: Parameter type (e.g., "string", "number")
        description: Parameter description
        required: Whether the parameter is required
        default: Default value for the parameter
    """
    name: str
    parameter_type: str
    description: str
    required: bool = False
    default: Any = None


@dataclass
class ToolDef:
    """Represents a tool definition.

    Attributes:
        name: Tool name
        description: Tool description
        parameters: List of ToolParameter objects
        metadata: Optional dictionary of additional metadata
        identifier: Tool identifier (defaults to name)
    """
    name: str
    description: str
    parameters: List[ToolParameter]
    metadata: Optional[Dict[str, Any]] = None
    identifier: str = ""


@dataclass
class ToolInvocationResult:
    """Represents the result of a tool invocation.

    Attributes:
        content: Result content as a string
        error_code: Error code (0 for success, 1 for error)
    """
    content: str
    error_code: int


class MCPClient:
    """Client for interacting with Model Context Protocol (MCP) endpoints"""

    def __init__(self, endpoint: str):
        """Initialize MCP client with endpoint URL

        Args:
            endpoint: The MCP endpoint URL (must be http or https)
        """
        if urlparse(endpoint).scheme not in ("http", "https"):
            raise ValueError(f"Endpoint {endpoint} is not a valid HTTP(S) URL")
        self.endpoint = endpoint

    async def list_tools(self) -> List[ToolDef]:
        """List available tools from the MCP endpoint

        Returns:
            List of ToolDef objects describing available tools
        """
        tools = []
        async with sse_client(self.endpoint) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                tools_result = await session.list_tools()

                for tool in tools_result.tools:
                    parameters = []
                    required_params = tool.inputSchema.get("required", [])
                    for param_name, param_schema in tool.inputSchema.get("properties", {}).items():
                        parameters.append(
                            ToolParameter(
                                name=param_name,
                                parameter_type=param_schema.get("type", "string"),
                                description=param_schema.get("description", ""),
                                required=param_name in required_params,
                                default=param_schema.get("default"),
                            )
                        )
                    tools.append(
                        ToolDef(
                            name=tool.name,
                            description=tool.description,
                            parameters=parameters,
                            metadata={"endpoint": self.endpoint},
                            identifier=tool.name  # Using name as identifier
                        )
                    )
        return tools

    async def invoke_tool(self, tool_name: str, kwargs: Dict[str, Any]) -> CallToolResult:
        """Invoke a specific tool with parameters

        Args:
            tool_name: Name of the tool to invoke
            kwargs: Dictionary of parameters to pass to the tool

        Returns:
            ToolInvocationResult containing the tool's response
        """
        async with sse_client(self.endpoint) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                return await session.call_tool(tool_name, kwargs)
