"""
File operation tools for the Natural Language CLI.
"""

from typing import List

from nlcli.registry import ToolArg, ToolSchema


def get_file_tools() -> List[ToolSchema]:
    """Get all file operation tool schemas."""
    return [
        # Find files tool
        ToolSchema(
            name="find_files",
            summary="Find files by size, time, name, or path",
            args={
                "path": ToolArg("path", "string", default="."),
                "min_size": ToolArg("min_size", "string"),
                "max_size": ToolArg("max_size", "string"),
                "modified_within": ToolArg("modified_within", "string"),
                "name": ToolArg("name", "string"),
                "type": ToolArg("type", "string", default="f"),
            },
            generator={
                "cmd": "find {path} -type {type} {size_clause} {time_clause} {name_clause} -print0 | xargs -0 ls -lh",
                "clauses": {
                    "size_clause": "-size +{min_size}",
                    "time_clause": "-mtime -{modified_within}",
                    "name_clause": "-name '{name}'",
                },
                "conversions": {"modified_within": "days"},
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "files >1GB changed this week",
                    "args": {"min_size": "1G", "modified_within": "7d"},
                },
                {
                    "nl": "show large files in Downloads",
                    "args": {"path": "~/Downloads", "min_size": "100M"},
                },
                {
                    "nl": "find .py files modified today",
                    "args": {"name": "*.py", "modified_within": "1d"},
                },
            ],
            keywords=["find", "files", "search", "large", "size", "modified", "recent"],
        ),
        # List directory contents
        ToolSchema(
            name="list_files",
            summary="List directory contents with details",
            args={
                "path": ToolArg("path", "string", default="."),
                "all": ToolArg("all", "boolean", default=False),
                "long": ToolArg("long", "boolean", default=True),
                "human": ToolArg("human", "boolean", default=True),
                "sort": ToolArg("sort", "string"),
            },
            generator={
                "cmd": "ls {long_flag}{human_flag}{all_flag} {sort_flag} {path}",
                "clauses": {},
            },
            danger_level="read_only",
            examples=[
                {"nl": "list files in current directory", "args": {"path": "."}},
                {"nl": "show all files including hidden", "args": {"all": True}},
                {"nl": "list files sorted by size", "args": {"sort": "size"}},
            ],
            keywords=["list", "ls", "show", "directory", "contents", "files"],
        ),
        # File content search
        ToolSchema(
            name="search_content",
            summary="Search for text content within files",
            args={
                "pattern": ToolArg("pattern", "string", required=True),
                "path": ToolArg("path", "string", default="."),
                "file_pattern": ToolArg("file_pattern", "string"),
                "recursive": ToolArg("recursive", "boolean", default=True),
                "ignore_case": ToolArg("ignore_case", "boolean", default=False),
                "line_numbers": ToolArg("line_numbers", "boolean", default=True),
            },
            generator={
                "cmd": "grep {flags} '{pattern}' {file_pattern_clause} {path}",
                "clauses": {
                    "flags": "{recursive_flag}{ignore_case_flag}{line_numbers_flag}",
                    "recursive_flag": "-r",
                    "ignore_case_flag": "-i",
                    "line_numbers_flag": "-n",
                    "file_pattern_clause": "--include='{file_pattern}'",
                },
                "conversions": {
                    "recursive": lambda x: "-r" if x else "",
                    "ignore_case": lambda x: "-i" if x else "",
                    "line_numbers": lambda x: "-n" if x else "",
                },
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "search for TODO in all python files",
                    "args": {"pattern": "TODO", "file_pattern": "*.py"},
                },
                {
                    "nl": "find 'import pandas' in project files",
                    "args": {"pattern": "import pandas", "path": "./src"},
                },
                {
                    "nl": "grep for error messages ignoring case",
                    "args": {"pattern": "error", "ignore_case": True},
                },
            ],
            keywords=[
                "search",
                "grep",
                "find",
                "content",
                "text",
                "contains",
                "containing",
                "pattern",
                "TODO",
                "import",
            ],
        ),
        # Directory size analysis
        ToolSchema(
            name="disk_usage",
            summary="Show disk usage for directories and files",
            args={
                "path": ToolArg("path", "string", default="."),
                "depth": ToolArg("depth", "integer", default=1),
                "human": ToolArg("human", "boolean", default=True),
                "sort": ToolArg("sort", "boolean", default=True),
            },
            generator={
                "cmd": "du {flags} --max-depth={depth} {path} | {sort_cmd}",
                "clauses": {
                    "flags": "{human_flag}",
                    "human_flag": "-h",
                    "sort_cmd": "sort -hr",
                },
                "conversions": {
                    "human": lambda x: "-h" if x else "",
                    "sort": lambda x: "sort -hr" if x else "cat",
                },
            },
            danger_level="read_only",
            examples=[
                {"nl": "show directory sizes", "args": {"path": "."}},
                {
                    "nl": "disk usage for home directory",
                    "args": {"path": "~", "depth": 2},
                },
                {"nl": "what's taking up space", "args": {"sort": True}},
            ],
            keywords=["disk", "usage", "space", "size", "directory", "du", "storage"],
        ),
        # File information
        ToolSchema(
            name="file_info",
            summary="Get detailed information about files",
            args={
                "path": ToolArg("path", "string", required=True),
                "follow_links": ToolArg("follow_links", "boolean", default=False),
            },
            generator={
                "cmd": "stat {flags} {path}",
                "clauses": {"flags": "{follow_flag}", "follow_flag": "-L"},
                "conversions": {"follow_links": lambda x: "-L" if x else ""},
            },
            danger_level="read_only",
            examples=[
                {"nl": "file info for README.md", "args": {"path": "README.md"}},
                {"nl": "get details about that file", "args": {"path": "{context}"}},
            ],
            keywords=["info", "stat", "details", "metadata", "properties"],
        ),
    ]
