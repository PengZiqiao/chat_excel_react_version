# 工具描述与字典
from langchain_experimental.tools.python.tool import PythonAstREPLTool
import pandas as pd
tools_description = [
    {
        "type": "function",
        "function": {
            "name": "dataframe_repl",
            "description": "一个Python shell。有一个本地变量名为`df`的dataframe对象，不需要重新import pandas。使用这个工具来执行Python关于df操作的命令。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_input": {
                        "description": "一个有效的Python命令，不要忘记使用print()打印结果",
                        "type": "str"
                    }
                },
                "required": [
                    "tool_input"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plot_repl",
            "description": "一个Python shell。可以使用matplotlib库来进行图像可视化。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_input": {
                        "description": "用于绘制图像的代码，将图片保存到当前目录下，文件名为`plot.png`。matplotlib的字体请使用本地simhei.ttf",
                        "type": "str"
                    }
                },
                "required": [
                    "tool_input"
                ]
            }
        }
    }
]


def generate_tools_map(df):
    python_repl_ast = PythonAstREPLTool(locals={'df': df})
    
    def plot_repl(tool_input):
        python_repl_ast.run(tool_input)
        return '代码已执行，图片文件已保存。'
    
    tools_map = {
        "dataframe_repl": python_repl_ast.run,
        "plot_repl": plot_repl
    }
    
    return tools_map