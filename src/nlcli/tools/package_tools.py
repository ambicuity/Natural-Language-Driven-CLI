"""
Package management tools for the Natural Language CLI.
"""

from typing import List

from nlcli.registry import ToolArg, ToolSchema


def get_package_tools() -> List[ToolSchema]:
    """Get all package management tool schemas."""
    return [
        # Search packages (brew)
        ToolSchema(
            name="brew_search",
            summary="Search for packages in Homebrew",
            args={
                "package": ToolArg("package", "string", required=True),
                "cask": ToolArg("cask", "boolean", default=False),
            },
            generator={"cmd": "brew search {package}", "clauses": {}},
            danger_level="read_only",
            examples=[
                {
                    "nl": "search for python package in brew",
                    "args": {"package": "python"},
                },
                {"nl": "find docker in homebrew", "args": {"package": "docker"}},
            ],
            keywords=["brew", "homebrew", "search", "package", "formula", "cask"],
        ),
        # Package info (brew)
        ToolSchema(
            name="brew_info",
            summary="Get information about a Homebrew package",
            args={"package": ToolArg("package", "string", required=True)},
            generator={"cmd": "brew info {package}", "clauses": {}},
            danger_level="read_only",
            examples=[
                {"nl": "info about python package", "args": {"package": "python"}},
                {"nl": "brew info for nodejs", "args": {"package": "nodejs"}},
            ],
            keywords=["brew", "info", "package", "details", "information"],
        ),
        # List installed packages (brew)
        ToolSchema(
            name="brew_list",
            summary="List installed Homebrew packages",
            args={"versions": ToolArg("versions", "boolean", default=False)},
            generator={"cmd": "brew list {versions_flag}", "clauses": {}},
            danger_level="read_only",
            examples=[
                {"nl": "list installed packages", "args": {}},
                {"nl": "show brew packages with versions", "args": {"versions": True}},
            ],
            keywords=["brew", "list", "installed", "packages"],
        ),
        # Search packages (apt)
        ToolSchema(
            name="apt_search",
            summary="Search for packages in APT repositories",
            args={"package": ToolArg("package", "string", required=True)},
            generator={"cmd": "apt search {package}", "clauses": {}},
            danger_level="read_only",
            examples=[
                {"nl": "search for python in apt", "args": {"package": "python"}},
                {"nl": "find nginx package", "args": {"package": "nginx"}},
            ],
            keywords=["apt", "search", "package", "repository", "ubuntu", "debian"],
        ),
        # Package info (apt)
        ToolSchema(
            name="apt_info",
            summary="Get information about an APT package",
            args={"package": ToolArg("package", "string", required=True)},
            generator={"cmd": "apt show {package}", "clauses": {}},
            danger_level="read_only",
            examples=[
                {"nl": "apt info for python3", "args": {"package": "python3"}},
                {"nl": "package details for nginx", "args": {"package": "nginx"}},
            ],
            keywords=["apt", "show", "info", "package", "details"],
        ),
        # List installed packages (apt)
        ToolSchema(
            name="apt_list",
            summary="List installed APT packages",
            args={"upgradable": ToolArg("upgradable", "boolean", default=False)},
            generator={"cmd": "apt list --installed", "clauses": {}},
            danger_level="read_only",
            examples=[
                {"nl": "list installed apt packages", "args": {}},
                {"nl": "show upgradable packages", "args": {"upgradable": True}},
            ],
            keywords=["apt", "list", "installed", "packages", "upgradable"],
        ),
    ]
