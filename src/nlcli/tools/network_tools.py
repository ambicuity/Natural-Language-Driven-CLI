"""
Network operation tools for the Natural Language CLI.
"""
from typing import List
from nlcli.registry import ToolSchema, ToolArg


def get_network_tools() -> List[ToolSchema]:
    """Get all network operation tool schemas."""
    return [
        # Ping host
        ToolSchema(
            name="ping_host",
            summary="Ping a host to test connectivity",
            args={
                "host": ToolArg("host", "string", required=True),
                "count": ToolArg("count", "integer", default=4),
                "timeout": ToolArg("timeout", "integer", default=5)
            },
            generator={
                "cmd": "ping -c {count} -W {timeout} {host}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "ping google.com",
                    "args": {"host": "google.com"}
                },
                {
                    "nl": "check connectivity to 8.8.8.8",
                    "args": {"host": "8.8.8.8"}
                },
                {
                    "nl": "ping localhost 10 times",
                    "args": {"host": "localhost", "count": 10}
                }
            ],
            keywords=["ping", "connectivity", "network", "host", "reachable", "connection"]
        ),
        
        # HTTP request
        ToolSchema(
            name="http_request",
            summary="Make HTTP requests to URLs",
            args={
                "url": ToolArg("url", "string", required=True),
                "method": ToolArg("method", "string", default="GET"),
                "headers": ToolArg("headers", "boolean", default=False),
                "follow": ToolArg("follow", "boolean", default=True),
                "timeout": ToolArg("timeout", "integer", default=30)
            },
            generator={
                "cmd": "curl {options} '{url}'",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "get content from example.com",
                    "args": {"url": "https://example.com"}
                },
                {
                    "nl": "curl with headers",
                    "args": {"url": "https://api.example.com", "headers": True}
                },
                {
                    "nl": "check website status",
                    "args": {"url": "https://google.com", "method": "HEAD"}
                }
            ],
            keywords=["curl", "http", "get", "post", "request", "url", "website", "api"]
        ),
        
        # Network connections
        ToolSchema(
            name="network_connections",
            summary="Show network connections and listening ports",
            args={
                "listening": ToolArg("listening", "boolean", default=False),
                "protocol": ToolArg("protocol", "string"),  # tcp, udp
                "port": ToolArg("port", "integer"),
                "process": ToolArg("process", "boolean", default=False)
            },
            generator={
                "cmd": "ss -tuln{process_flag}",
                "clauses": {}
            },
            danger_level="read_only", 
            examples=[
                {
                    "nl": "show network connections",
                    "args": {}
                },
                {
                    "nl": "listening ports",
                    "args": {"listening": True}
                },
                {
                    "nl": "tcp connections with processes",
                    "args": {"protocol": "tcp", "process": True}
                }
            ],
            keywords=["network", "connections", "ports", "listening", "tcp", "udp", "ss", "netstat"]
        ),
        
        # DNS lookup
        ToolSchema(
            name="dns_lookup",
            summary="Perform DNS lookups and reverse lookups",
            args={
                "host": ToolArg("host", "string", required=True),
                "record_type": ToolArg("record_type", "string", default="A"),  # A, AAAA, MX, NS, etc.
                "reverse": ToolArg("reverse", "boolean", default=False)
            },
            generator={
                "cmd": "dig {record_type} {host} +short",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "lookup google.com",
                    "args": {"host": "google.com"}
                },
                {
                    "nl": "mx records for example.com",
                    "args": {"host": "example.com", "record_type": "MX"}
                },
                {
                    "nl": "reverse lookup 8.8.8.8",
                    "args": {"host": "8.8.8.8", "reverse": True}
                }
            ],
            keywords=["dns", "lookup", "dig", "resolve", "domain", "ip", "mx", "records"]
        ),
        
        # Download file
        ToolSchema(
            name="download_file",
            summary="Download files from URLs",
            args={
                "url": ToolArg("url", "string", required=True),
                "output": ToolArg("output", "string"),
                "resume": ToolArg("resume", "boolean", default=False),
                "progress": ToolArg("progress", "boolean", default=True)
            },
            generator={
                "cmd": "wget {options} '{url}'",
                "clauses": {}
            },
            danger_level="modify",
            examples=[
                {
                    "nl": "download file from url",
                    "args": {"url": "https://example.com/file.pdf"}
                },
                {
                    "nl": "download and save as backup.zip",
                    "args": {"url": "https://site.com/data.zip", "output": "backup.zip"}
                }
            ],
            keywords=["download", "wget", "get", "fetch", "file", "url", "save"]
        ),
        
        # Network interface info
        ToolSchema(
            name="network_interfaces",
            summary="Show network interface information",
            args={
                "interface": ToolArg("interface", "string"),
                "stats": ToolArg("stats", "boolean", default=False)
            },
            generator={
                "cmd": "ip addr show {interface}",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "show network interfaces",
                    "args": {}
                },
                {
                    "nl": "eth0 interface info",
                    "args": {"interface": "eth0"}
                },
                {
                    "nl": "network statistics",
                    "args": {"stats": True}
                }
            ],
            keywords=["interface", "network", "ip", "ethernet", "wifi", "addr", "ifconfig"]
        )
    ]