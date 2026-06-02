"""Git 操作辅助工具"""

import os
import subprocess
from pathlib import Path
from langchain_core.tools import Tool


def _run_git(repo_path: str, *args: str) -> str:
    """在指定仓库路径执行 git 命令。"""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if result.returncode == 0 else f"Git 错误: {output}"
    except FileNotFoundError:
        return "错误: 未找到 git，请确认已安装 Git"
    except subprocess.TimeoutExpired:
        return "错误: Git 命令超时"
    except Exception as e:
        return f"Git 执行异常: {e}"


def git_log_func(params: str) -> str:
    """查看 Git 提交日志。params 格式: repo_path 或 repo_path,n"""
    parts = params.split(",")
    repo_path = parts[0].strip()
    n = parts[1].strip() if len(parts) > 1 else "10"
    return _run_git(repo_path, "log", f"-{n}", "--oneline", "--decorate")


def git_status_func(repo_path: str) -> str:
    """查看 Git 仓库状态。"""
    return _run_git(repo_path.strip(), "status", "--short")


def git_diff_func(params: str) -> str:
    """查看 Git diff。params: repo_path 或 repo_path,file"""
    parts = params.split(",")
    repo_path = parts[0].strip()
    file_filter = parts[1].strip() if len(parts) > 1 else ""
    args = ["diff", "--stat"]
    if file_filter:
        args.append(file_filter)
    return _run_git(repo_path, *args)


# LangChain 工具封装
git_log_tool = Tool(
    name="git_log",
    description="查看 Git 提交日志。输入: repo_path,n（n为条数，默认10）",
    func=git_log_func,
)

git_status_tool = Tool(
    name="git_status",
    description="查看 Git 工作区状态。输入: 仓库路径",
    func=git_status_func,
)

git_diff_tool = Tool(
    name="git_diff",
    description="查看 Git 变更差异。输入: repo_path,file（file可选）",
    func=git_diff_func,
)

GIT_TOOLS = [git_log_tool, git_status_tool, git_diff_tool]
