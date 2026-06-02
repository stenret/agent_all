"""Python 代码沙箱工具"""

from langchain_core.tools import Tool
from langchain_experimental.tools.python.tool import PythonREPLTool


_python_repl = PythonREPLTool(
    name="python_repl",
    description="Python 代码执行沙箱。用于数学计算、数据处理、算法实现等。",
)
_python_repl.handle_validation_error = True

python_repl_tool = _python_repl
