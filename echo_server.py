from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP(name="echo mcp server")

@mcp.tool()
def add(a: int, b:int) -> int:
    """Add two numbers."""
    return a + b

@mcp.resource("dir://test")
def test() -> list[str]:
    """test 폴더에 있는 파일 리스트"""
    test = Path.home() / "test"
    return [str(f) for f in test.iterdir()]


@mcp.resource("echo://{message}")
def echo_template(message: str) -> str:
    """Echo the input text"""
    return f"동적으로 변하는 리소스 : {message}"


@mcp.prompt("echo")
def echo_prompt(message: str) -> str:
    return f"주어지는 메시지의 지시에 따르시오.\n메시지 : {message}"

if __name__ == "__main__":
    mcp.run(transport="sse", host="localhost", port=8000, path="/mcp")