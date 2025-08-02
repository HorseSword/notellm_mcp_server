""" 
MCP tool as calculator (example)
"""

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransform

mcp = FastMCP("My MCP Server")


@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ToolError("Division by zero is not allowed.")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers.")
    return a / b

#%%

@mcp.tool
def calculate(query: str):
    """Common calculator."""
    try:    
        return eval(query)
    except Exception as e:
        raise ToolError(f"ERROR = {e}")

# rewrite info
python_calculator = Tool.from_tool(
    calculate, 
    name = 'python_calculator',
    description = 'Calculate your python expression and return final result.',
    transform_args={
        "query": ArgTransform(
            name = 'expression',
            description=(
                "The expression string that you want python to calculate."
            )
        )
    }
)
mcp.add_tool(python_calculator)
calculate.disable()

#%%
if __name__ == "__main__":
    mcp.run()
