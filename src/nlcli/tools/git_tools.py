"""
Git read-only operation tools for the Natural Language CLI.
"""
from typing import List
from nlcli.registry import ToolSchema, ToolArg


def get_git_tools() -> List[ToolSchema]:
    """Get all git read-only operation tool schemas."""
    return [
        # Git status
        ToolSchema(
            name="git_status",
            summary="Show git repository status",
            args={
                "short": ToolArg("short", "boolean", default=False)
            },
            generator={
                "cmd": "git status {short_flag}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "git status",
                    "args": {}
                },
                {
                    "nl": "show git status short",
                    "args": {"short": True}
                }
            ],
            keywords=["git", "status", "repository", "changes", "working"]
        ),
        
        # Git log
        ToolSchema(
            name="git_log",
            summary="Show git commit history",
            args={
                "limit": ToolArg("limit", "integer", default=10),
                "oneline": ToolArg("oneline", "boolean", default=False),
                "graph": ToolArg("graph", "boolean", default=False),
                "author": ToolArg("author", "string")
            },
            generator={
                "cmd": "git log {flags} -{limit}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "git log",
                    "args": {}
                },
                {
                    "nl": "show last 5 commits",
                    "args": {"limit": 5}
                },
                {
                    "nl": "git log oneline",
                    "args": {"oneline": True}
                }
            ],
            keywords=["git", "log", "commits", "history", "author"]
        ),
        
        # Git diff
        ToolSchema(
            name="git_diff",
            summary="Show git differences",
            args={
                "staged": ToolArg("staged", "boolean", default=False),
                "file": ToolArg("file", "string"),
                "commit": ToolArg("commit", "string")
            },
            generator={
                "cmd": "git diff {staged_flag} {commit} {file}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "git diff",
                    "args": {}
                },
                {
                    "nl": "show staged changes",
                    "args": {"staged": True}
                },
                {
                    "nl": "diff for specific file",
                    "args": {"file": "README.md"}
                }
            ],
            keywords=["git", "diff", "changes", "staged", "differences"]
        ),
        
        # Git branch
        ToolSchema(
            name="git_branch",
            summary="Show git branches",
            args={
                "remote": ToolArg("remote", "boolean", default=False),
                "all": ToolArg("all", "boolean", default=False)
            },
            generator={
                "cmd": "git branch {flags}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "git branches",
                    "args": {}
                },
                {
                    "nl": "show remote branches",
                    "args": {"remote": True}
                },
                {
                    "nl": "list all branches",
                    "args": {"all": True}
                }
            ],
            keywords=["git", "branch", "branches", "remote", "local"]
        ),
        
        # Git show
        ToolSchema(
            name="git_show",
            summary="Show git commit details",
            args={
                "commit": ToolArg("commit", "string"),
                "stat": ToolArg("stat", "boolean", default=False)
            },
            generator={
                "cmd": "git show {stat_flag} {commit}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "git show latest commit",
                    "args": {}
                },
                {
                    "nl": "show commit abc123",
                    "args": {"commit": "abc123"}
                }
            ],
            keywords=["git", "show", "commit", "details"]
        ),
        
        # Git remote
        ToolSchema(
            name="git_remote",
            summary="Show git remote repositories",
            args={
                "verbose": ToolArg("verbose", "boolean", default=False)
            },
            generator={
                "cmd": "git remote {verbose_flag}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "git remotes",
                    "args": {}
                },
                {
                    "nl": "show remote details",
                    "args": {"verbose": True}
                }
            ],
            keywords=["git", "remote", "remotes", "origin", "upstream"]
        ),
        
        # Git blame
        ToolSchema(
            name="git_blame",
            summary="Show git blame information for a file",
            args={
                "file": ToolArg("file", "string", required=True),
                "line_start": ToolArg("line_start", "integer"),
                "line_end": ToolArg("line_end", "integer")
            },
            generator={
                "cmd": "git blame {line_range} {file}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "git blame README.md",
                    "args": {"file": "README.md"}
                },
                {
                    "nl": "blame lines 10-20 of main.py",
                    "args": {"file": "main.py", "line_start": 10, "line_end": 20}
                }
            ],
            keywords=["git", "blame", "annotate", "author", "file"]
        )
    ]