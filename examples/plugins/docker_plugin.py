"""
Docker Plugin for NLCLI
Provides Docker container management commands.
"""
from nlcli.registry import ToolSchema, ToolArg


def get_tools():
    """Return list of Docker tools."""
    return [
        ToolSchema(
            name="docker_ps",
            summary="List Docker containers",
            args={
                "all": ToolArg("all", "boolean", default=False, description="Show all containers including stopped"),
                "quiet": ToolArg("quiet", "boolean", default=False, description="Only show container IDs")
            },
            generator={
                "cmd": "docker ps{all_flag}{quiet_flag}",
                "clauses": {
                    "all_flag": " -a",
                    "quiet_flag": " -q"
                }
            },
            danger_level="read_only",
            examples=[
                {"nl": "show docker containers", "args": {"all": False, "quiet": False}},
                {"nl": "list all docker containers", "args": {"all": True, "quiet": False}},
                {"nl": "show running containers", "args": {"all": False, "quiet": False}}
            ],
            keywords=["docker", "containers", "ps", "list"]
        ),
        ToolSchema(
            name="docker_images",
            summary="List Docker images",
            args={
                "quiet": ToolArg("quiet", "boolean", default=False, description="Only show image IDs")
            },
            generator={
                "cmd": "docker images{quiet_flag}",
                "clauses": {
                    "quiet_flag": " -q"
                }
            },
            danger_level="read_only",
            examples=[
                {"nl": "show docker images", "args": {"quiet": False}},
                {"nl": "list docker images", "args": {"quiet": False}}
            ],
            keywords=["docker", "images", "list"]
        ),
        ToolSchema(
            name="docker_stop",
            summary="Stop a Docker container",
            args={
                "container": ToolArg("container", "string", required=True, description="Container ID or name to stop")
            },
            generator={
                "cmd": "docker stop {container}"
            },
            danger_level="modify",
            examples=[
                {"nl": "stop docker container nginx", "args": {"container": "nginx"}},
                {"nl": "stop container abc123", "args": {"container": "abc123"}}
            ],
            keywords=["docker", "stop", "container"]
        )
    ]


def get_plugin_info():
    """Return plugin metadata."""
    return {
        "name": "docker",
        "version": "1.0.0",
        "description": "Docker container management tools for NLCLI",
        "author": "NLCLI Team",
        "website": "https://github.com/ambicuity/Natural-Language-Driven-CLI",
        "dependencies": ["docker"],
        "min_nlcli_version": "0.1.0"
    }