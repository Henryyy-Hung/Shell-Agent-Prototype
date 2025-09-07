from typing import Annotated
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from mcp_shellagent.mobaxterm_client.tools import RemoteShell


def create_server() -> FastMCP:
    mcp_server = FastMCP(name="hw-mcp-demo")

    @mcp_server.tool(
        title="Write to MobaXterm",
        description="Write a command to MobaXterm and get the output"
    )
    def write_to_mobaxterm(
            cmd: Annotated[str, Field(description="The command to run in MobaXterm")],
    ) -> str:
        shell = RemoteShell(r"C:\Users\henry\Desktop")
        try:
            output = shell.send_command(cmd, timeout=5)
        finally:
            shell.close()
        return output

    return mcp_server


def main():
    print("Starting MCP server...")
    mcp = create_server()
    mcp.run()
