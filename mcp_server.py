from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather", port=5001)

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""

    # 항상 맑음으로 리턴한다.
    # 실제로는 api를 조회하여 결과를 가져오게 하면 된다.

    return f"{location}은 항상 맑아요~~"


def run_server(transport: str = "stdio"):
    """MCP 서버를 실행합니다.

    Args:
        transport: 통신 방식 ("stdio" 또는 "sse")
    """
    mcp.run(transport=transport)