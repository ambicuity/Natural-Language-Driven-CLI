"""
Process management tools for the Natural Language CLI.
"""

from typing import List

from nlcli.registry import ToolArg, ToolSchema


def get_process_tools() -> List[ToolSchema]:
    """Get all process management tool schemas."""
    return [
        # List processes
        ToolSchema(
            name="list_processes",
            summary="List running processes with details",
            args={
                "user": ToolArg("user", "string"),
                "name": ToolArg("name", "string"),
                "port": ToolArg("port", "integer"),
                "sort": ToolArg("sort", "string", default="cpu"),
                "limit": ToolArg("limit", "integer", default=20),
            },
            generator={
                "cmd": "ps aux | head -1 && ps aux | grep -v 'grep' | sort -k{sort_col} -r | head -{limit}",
                "clauses": {},
            },
            danger_level="read_only",
            examples=[
                {"nl": "list running processes", "args": {"sort": "cpu"}},
                {"nl": "show processes by memory usage", "args": {"sort": "mem"}},
                {"nl": "processes using port 3000", "args": {"port": 3000}},
            ],
            keywords=["process", "processes", "ps", "running", "cpu", "memory", "port"],
        ),
        # Find process by port
        ToolSchema(
            name="process_by_port",
            summary="Find processes using a specific port",
            args={
                "port": ToolArg("port", "integer", required=True),
                "protocol": ToolArg("protocol", "string", default="tcp"),
            },
            generator={"cmd": "lsof -i :{port} -P -n", "clauses": {}},
            danger_level="read_only",
            examples=[
                {"nl": "what's using port 3000", "args": {"port": 3000}},
                {"nl": "process on port 8080", "args": {"port": 8080}},
                {"nl": "find process using port 443", "args": {"port": 443}},
            ],
            keywords=["port", "using", "listening", "process", "lsof", "connection"],
        ),
        # Kill process (destructive)
        ToolSchema(
            name="kill_process",
            summary="Terminate a process by PID or name",
            args={
                "pid": ToolArg("pid", "integer"),
                "name": ToolArg("name", "string"),
                "signal": ToolArg("signal", "string", default="TERM"),
                "force": ToolArg("force", "boolean", default=False),
            },
            generator={"cmd": "kill -{signal} {target}", "clauses": {}},
            danger_level="destructive",
            examples=[
                {"nl": "kill process 1234", "args": {"pid": 1234}},
                {"nl": "terminate nginx process", "args": {"name": "nginx"}},
                {
                    "nl": "force kill chrome",
                    "args": {"name": "chrome", "signal": "KILL"},
                },
            ],
            keywords=["kill", "terminate", "stop", "end", "process"],
        ),
        # Process tree
        ToolSchema(
            name="process_tree",
            summary="Show process tree hierarchy",
            args={"pid": ToolArg("pid", "integer"), "user": ToolArg("user", "string")},
            generator={"cmd": "pstree {options}", "clauses": {}},
            danger_level="read_only",
            examples=[
                {"nl": "show process tree", "args": {}},
                {"nl": "process tree for user john", "args": {"user": "john"}},
            ],
            keywords=["tree", "hierarchy", "parent", "child", "process"],
        ),
        # System resource usage
        ToolSchema(
            name="system_resources",
            summary="Show system resource usage (CPU, memory, load)",
            args={"detailed": ToolArg("detailed", "boolean", default=False)},
            generator={
                "cmd": "top -bn1 | head -5 && free -h && df -h /",
                "clauses": {},
            },
            danger_level="read_only",
            examples=[
                {"nl": "show system resources", "args": {}},
                {"nl": "cpu and memory usage", "args": {}},
                {"nl": "system load", "args": {}},
            ],
            keywords=[
                "system",
                "cpu",
                "memory",
                "load",
                "resources",
                "usage",
                "top",
                "free",
            ],
        ),
    ]
