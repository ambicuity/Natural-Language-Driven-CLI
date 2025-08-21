"""
Tool Registry System
Declarative schemas for allowed commands and tools.
"""
import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class ToolArg:
    """Tool argument specification."""
    name: str
    type: str
    required: bool = False
    default: Optional[Any] = None
    description: str = ""
    validation: Optional[Callable] = None


@dataclass 
class ToolSchema:
    """Schema for a command tool."""
    name: str
    summary: str
    args: Dict[str, ToolArg]
    generator: Dict[str, Any]  # Command generation template
    danger_level: str = "read_only"  # read_only, modify, destructive
    examples: List[Dict[str, Any]] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []
        if self.keywords is None:
            self.keywords = []


class ToolRegistry:
    """
    Registry of available tools with semantic matching and command generation.
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolSchema] = {}
        self._load_builtin_tools()
    
    def register_tool(self, schema: ToolSchema) -> None:
        """Register a new tool schema."""
        self.tools[schema.name] = schema
    
    def get_tool(self, name: str) -> Optional[ToolSchema]:
        """Get tool schema by name."""
        return self.tools.get(name)
    
    def find_matching_tools(self, nl_input: str) -> List[tuple[ToolSchema, float]]:
        """
        Find tools that match the natural language input.
        Returns list of (tool, confidence_score) tuples.
        """
        matches = []
        nl_lower = nl_input.lower()
        
        for tool in self.tools.values():
            score = self._calculate_match_score(tool, nl_lower)
            if score > 0.0:
                matches.append((tool, score))
        
        # Sort by confidence score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _calculate_match_score(self, tool: ToolSchema, nl_input: str) -> float:
        """Calculate how well a tool matches the natural language input."""
        score = 0.0
        
        # Keyword matching
        for keyword in tool.keywords:
            if keyword in nl_input:
                score += 0.3
        
        # Summary matching (simple word overlap)
        summary_words = set(tool.summary.lower().split())
        input_words = set(nl_input.split())
        overlap = len(summary_words.intersection(input_words))
        if overlap > 0:
            score += 0.2 * overlap
        
        # Example matching
        for example in tool.examples:
            if "nl" in example:
                example_words = set(example["nl"].lower().split())
                overlap = len(example_words.intersection(input_words))
                if overlap > 0:
                    score += 0.4 * (overlap / len(example_words))
        
        # Tool name matching
        if tool.name.replace("_", " ") in nl_input:
            score += 0.5
        
        # Special case boosting
        if tool.name == "search_content":
            # Boost score for search-related terms that indicate text search
            content_search_patterns = [
                r'search\s+for\s+\w+',  # "search for TODO"
                r'find\s+\w+\s+in.*files',  # "find TODO in files"
                r'grep\s+for\s+\w+',  # "grep for import"
                r'containing\s+\w+',  # "containing TODO"
                r'look\s+for\s+\w+'  # "look for pattern"
            ]
            
            boost = 0
            for pattern in content_search_patterns:
                if re.search(pattern, nl_input.lower()):
                    boost += 1.0  # Strong boost for content search patterns
            
            # Boost for specific content search terms
            search_terms = ["TODO", "import", "class", "function", "def", "error", "debug"]
            for term in search_terms:
                if term.lower() in nl_input.lower():
                    boost += 0.8
            
            score += boost
        
        elif tool.name == "find_files":
            # Reduce boost for find_files when content search is clearly intended
            content_indicators = ["search for", "grep", "containing", "TODO", "import"]
            penalty = 0
            for indicator in content_indicators:
                if indicator.lower() in nl_input.lower():
                    penalty += 0.5
            
            score = max(0, score - penalty)
        
        if tool.name == "find_files":
            # Boost for file-finding terms
            find_terms = ["find", "files", "locate", "show"]
            for term in find_terms:
                if term in nl_input.lower():
                    score += 0.3
            
            # Reduce score if it's clearly a listing request
            if any(phrase in nl_input.lower() for phrase in ["list files", "show files", "ls"]):
                score = max(0, score - 0.5)
        
        elif tool.name == "list_files":
            # Boost for listing terms
            list_terms = ["list", "show", "ls", "directory", "contents"]
            for term in list_terms:
                if term in nl_input.lower():
                    score += 0.4
            
            # Extra boost for explicit listing requests
            if any(phrase in nl_input.lower() for phrase in ["list files", "show files", "ls"]):
                score += 0.6
        
        elif tool.name.startswith("brew_"):
            # Boost for brew-related commands
            if "brew" in nl_input.lower() or "homebrew" in nl_input.lower():
                score += 0.8
            # Specific command boosting
            if tool.name == "brew_search" and "search" in nl_input.lower():
                score += 0.5
            elif tool.name == "brew_info" and "info" in nl_input.lower():
                score += 0.5
            elif tool.name == "brew_list" and any(word in nl_input.lower() for word in ["list", "installed"]):
                score += 0.5
        
        elif tool.name.startswith("apt_"):
            # Boost for apt-related commands
            if "apt" in nl_input.lower():
                score += 0.8
            # Specific command boosting
            if tool.name == "apt_search" and "search" in nl_input.lower():
                score += 0.5
            elif tool.name == "apt_info" and "info" in nl_input.lower():
                score += 0.5
            elif tool.name == "apt_list" and any(word in nl_input.lower() for word in ["list", "installed"]):
                score += 0.5
        
        elif tool.name.startswith("git_"):
            # Boost for git-related commands
            if "git" in nl_input.lower():
                score += 0.8
            
            # Specific git command boosting based on exact command match
            if tool.name == "git_status" and "status" in nl_input.lower():
                score += 0.8
            elif tool.name == "git_log" and ("log" in nl_input.lower() or any(phrase in nl_input.lower() for phrase in ["last", "commits", "history"])):
                score += 0.8
            elif tool.name == "git_diff" and "diff" in nl_input.lower():
                score += 0.8
            elif tool.name == "git_branch" and "branch" in nl_input.lower():
                score += 0.8
            elif tool.name == "git_show" and "show" in nl_input.lower() and "commits" not in nl_input.lower():
                score += 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def extract_args(self, tool: ToolSchema, nl_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract arguments from natural language input for a specific tool."""
        args = {}
        nl_lower = nl_input.lower()
        
        # Apply heuristics and regex patterns for argument extraction
        for arg_name, arg_spec in tool.args.items():
            value = self._extract_arg_value(arg_name, arg_spec, nl_lower, context)
            if value is not None:
                args[arg_name] = value
            elif arg_spec.default is not None:
                args[arg_name] = arg_spec.default
        
        return args
    
    def _extract_arg_value(self, arg_name: str, arg_spec: ToolArg, nl_input: str, context: Dict[str, Any]) -> Optional[Any]:
        """Extract a specific argument value from natural language input."""
        
        # Path extraction
        if arg_name == "path":
            # Look for explicit paths
            path_patterns = [
                r'in\s+([~/][^\s]+)',
                r'under\s+([~/][^\s]+)', 
                r'from\s+([~/][^\s]+)',
                r'([~/][^\s]+)',
            ]
            for pattern in path_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    path = match.group(1)
                    # Expand ~ to home directory
                    if path.startswith("~"):
                        path = str(Path.home() / path[2:])
                    return path
            
            # Use context filters
            if "active_path" in context.get("filters", {}):
                return context["filters"]["active_path"]
            
            # Default to current directory
            return context.get("cwd", ".")
        
        # Size extraction
        elif arg_name in ("min_size", "max_size", "size"):
            size_patterns = [
                r'>(\d+(?:\.\d+)?)\s*(gb|mb|kb|g|m|k|bytes?)',
                r'larger?\s+than\s+(\d+(?:\.\d+)?)\s*(gb|mb|kb|g|m|k|bytes?)',
                r'bigger?\s+than\s+(\d+(?:\.\d+)?)\s*(gb|mb|kb|g|m|k|bytes?)',
                r'(\d+(?:\.\d+)?)\s*(gb|mb|kb|g|m|k|bytes?)\s+or\s+(larger|bigger)',
            ]
            for pattern in size_patterns:
                match = re.search(pattern, nl_input, re.IGNORECASE)
                if match:
                    size_val = match.group(1)
                    unit = match.group(2).lower()
                    # Convert to find-compatible format
                    unit_map = {
                        "gb": "G", "g": "G",
                        "mb": "M", "m": "M", 
                        "kb": "k", "k": "k",
                        "bytes": "c", "byte": "c"
                    }
                    return f"{size_val}{unit_map.get(unit, 'c')}"
        
        # Time/date extraction
        elif arg_name in ("modified_within", "time_filter", "since"):
            time_patterns = [
                (r'this\s+week', "7d"),
                (r'last\s+week', "14d"),
                (r'today', "1d"),
                (r'yesterday', "2d"),
                (r'this\s+month', "30d"),
                (r'last\s+(\d+)\s+days?', lambda m: f"{m.group(1)}d"),
                (r'(\d+)\s+days?\s+ago', lambda m: f"{m.group(1)}d"),
            ]
            for pattern, replacement in time_patterns:
                match = re.search(pattern, nl_input, re.IGNORECASE)
                if match:
                    if callable(replacement):
                        return replacement(match)
                    else:
                        return replacement
        
        # Process name/PID extraction (must come before general pattern/name extraction)
        elif arg_name == "pid":
            pid_patterns = [
                r'process\s+(\d+)',
                r'pid\s+(\d+)',
                r'kill\s+(\d+)',
            ]
            for pattern in pid_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    return int(match.group(1))
                    
        elif arg_name == "name" and any(word in nl_input.lower() for word in ["kill", "terminate", "stop"]):
            # Process name for kill/terminate commands
            name_patterns = [
                r'kill\s+process\s+([a-zA-Z0-9_-]+)',
                r'terminate\s+([a-zA-Z0-9_-]+)\s+process',
                r'terminate\s+([a-zA-Z0-9_-]+)', 
                r'stop\s+([a-zA-Z0-9_-]+)\s+process',
                r'stop\s+([a-zA-Z0-9_-]+)',
                r'kill\s+([a-zA-Z0-9_-]+)',
                r'([a-zA-Z0-9_-]+)\s+process',
            ]
            for pattern in name_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    name = match.group(1)
                    # Don't return common words that aren't process names
                    if name not in ["the", "a", "an", "process", "kill", "terminate", "stop"]:
                        return name
        
        # Pattern/name extraction (general)
        elif arg_name in ("pattern", "name", "filename"):
            # Look for quoted strings or specific patterns
            patterns_to_try = [
                r'search\s+for\s+["\']?([^"\']+?)["\']?\s+in',  # "search for TODO in"
                r'find\s+["\']?([^"\']+?)["\']?\s+in',  # "find TODO in"
                r'grep\s+for\s+["\']?([^"\']+?)["\']?',  # "grep for import"
                r'containing\s+["\']?([^"\']+?)["\']?',  # "containing TODO"
                r'"([^"]+)"',  # quoted strings
                r"'([^']+)'",  # single quoted strings
            ]
            
            for pattern in patterns_to_try:
                match = re.search(pattern, nl_input, re.IGNORECASE)
                if match:
                    result = match.group(1).strip()
                    # Don't return single characters unless they make sense
                    if len(result) > 1 or result.isupper():
                        return result
                        
            # Fallback: look for common programming terms
            programming_terms = ["TODO", "FIXME", "import", "class", "function", "def", "error", "debug", "console.log"]
            for term in programming_terms:
                if term.lower() in nl_input.lower():
                    return term
                    
        # File pattern extraction (for search_content file_pattern arg)
        elif arg_name == "file_pattern":
            file_patterns = [
                r'in\s+([*.]?\w+)\s+files',  # "in python files", "in .py files"
                r'in\s+(\*\.\w+)',  # "in *.py"
                r'(\*\.\w+)\s+files',  # "*.py files"
            ]
            
            for pattern in file_patterns:
                match = re.search(pattern, nl_input, re.IGNORECASE)
                if match:
                    file_ext = match.group(1)
                    # Convert "python" to "*.py", etc.
                    if file_ext == "python":
                        return "*.py"
                    elif file_ext == "javascript":
                        return "*.js"
                    elif file_ext == "java":
                        return "*.java"
                    elif not file_ext.startswith("*"):
                        return f"*.{file_ext}"
                    else:
                        return file_ext
        
        # Port extraction
        elif arg_name == "port":
            port_patterns = [
                r'port\s+(\d+)',
                r':(\d+)',
                r'(\d+)\s*$',  # number at end
            ]
            for pattern in port_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    port_num = int(match.group(1))
                    if 1 <= port_num <= 65535:
                        return port_num
        
        # Host/URL extraction
        elif arg_name in ("host", "url"):
            host_patterns = [
                r'ping\s+([a-zA-Z0-9.-]+)',
                r'from\s+([a-zA-Z0-9.-]+)',
                r'to\s+([a-zA-Z0-9.-]+)', 
                r'(https?://[^\s]+)',
                r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # domain.com
                r'(\d+\.\d+\.\d+\.\d+)',  # IP address
                r'(localhost)',
            ]
            for pattern in host_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    result = match.group(1)
                    # For URLs, ensure they have a protocol
                    if arg_name == "url" and not result.startswith(("http://", "https://")):
                        result = "https://" + result
                    return result

        
        # Count/limit extraction
        elif arg_name in ("count", "limit"):
            count_patterns = [
                r'last\s+(\d+)',
                r'(\d+)\s+times',
                r'(\d+)\s+pings?',
                r'(\d+)\s+commits?',
                r'top\s+(\d+)',
                r'first\s+(\d+)',
                r'limit\s+(\d+)',
            ]
            for pattern in count_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    return int(match.group(1))
        
        # Sort type extraction
        elif arg_name == "sort":
            if any(word in nl_input.lower() for word in ["memory", "mem", "ram"]):
                return "mem"
            elif any(word in nl_input.lower() for word in ["cpu", "processor"]):
                return "cpu"
            elif any(word in nl_input.lower() for word in ["time"]):
                return "time"
            elif any(word in nl_input.lower() for word in ["pid"]):
                return "pid"
        
        # HTTP method extraction
        elif arg_name == "method":
            if "post" in nl_input.lower():
                return "POST"
            elif "put" in nl_input.lower():
                return "PUT"
            elif "delete" in nl_input.lower():
                return "DELETE"
            elif "head" in nl_input.lower():
                return "HEAD"
            else:
                return "GET"
        
        # Protocol extraction
        elif arg_name == "protocol":
            if "tcp" in nl_input.lower():
                return "tcp"
            elif "udp" in nl_input.lower():
                return "udp"
        
        # DNS record type extraction
        elif arg_name == "record_type":
            record_types = {
                "mx": "MX", "mail": "MX",
                "ns": "NS", "nameserver": "NS",
                "cname": "CNAME", "alias": "CNAME",
                "aaaa": "AAAA", "ipv6": "AAAA",
                "txt": "TXT", "text": "TXT"
            }
            for keyword, record_type in record_types.items():
                if keyword in nl_input.lower():
                    return record_type
            return "A"  # Default to A record
        
        # Boolean flag extraction
        elif arg_name in ("headers", "follow", "detailed", "listening", "process", "stats", "all", "human", "reverse"):
            positive_indicators = ["with", "show", "include", "detailed", "verbose"]
            return any(indicator in nl_input.lower() for indicator in positive_indicators)
        
        # Package name extraction
        elif arg_name == "package":
            package_patterns = [
                r'brew\s+search\s+([a-zA-Z0-9_.-]+)',
                r'brew\s+info\s+([a-zA-Z0-9_.-]+)', 
                r'apt\s+search\s+([a-zA-Z0-9_.-]+)',
                r'apt\s+show\s+([a-zA-Z0-9_.-]+)',
                r'apt\s+info\s+for\s+([a-zA-Z0-9_.-]+)',
                r'search\s+for\s+([a-zA-Z0-9_.-]+)\s+package',
                r'search\s+for\s+([a-zA-Z0-9_.-]+)',
                r'info\s+(?:about\s+|for\s+)?([a-zA-Z0-9_.-]+)',
                r'show\s+([a-zA-Z0-9_.-]+)',
                r'package\s+([a-zA-Z0-9_.-]+)',
                r'([a-zA-Z0-9_.-]+)\s+package',
            ]
            for pattern in package_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    package = match.group(1)
                    # Don't return common words
                    if package not in ["for", "about", "info", "show", "search", "package", "in", "brew", "apt"]:
                        return package
        
        # Git-specific extractions
        elif arg_name == "commit":
            commit_patterns = [
                r'commit\s+([a-f0-9]{6,40})',  # commit hash
                r'show\s+([a-f0-9]{6,40})',  # show hash
                r'([a-f0-9]{6,40})',  # bare hash
            ]
            for pattern in commit_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    return match.group(1)
        
        elif arg_name == "author":
            author_patterns = [
                r'author\s+([a-zA-Z0-9_-]+)',
                r'by\s+([a-zA-Z0-9_-]+)',
                r'from\s+([a-zA-Z0-9_-]+)',
            ]
            for pattern in author_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    return match.group(1)
        
        elif arg_name == "file" and any(word in nl_input.lower() for word in ["diff", "blame"]):
            # File name for git operations
            file_patterns = [
                r'diff\s+([a-zA-Z0-9_./+-]+)',
                r'blame\s+([a-zA-Z0-9_./+-]+)',
                r'for\s+([a-zA-Z0-9_./+-]+)',
                r'file\s+([a-zA-Z0-9_./+-]+)',
            ]
            for pattern in file_patterns:
                match = re.search(pattern, nl_input)
                if match:
                    return match.group(1)
        
        return None
    
    def generate_command(self, tool: ToolSchema, args: Dict[str, Any]) -> str:
        """Generate shell command from tool schema and arguments."""
        generator = tool.generator
        
        # Start with base command template
        cmd_template = generator.get("cmd", "")
        
        # Handle specific tools with custom logic
        if tool.name == "list_files":
            return self._generate_ls_command(args)
        elif tool.name == "search_content":
            return self._generate_grep_command(args)
        elif tool.name == "disk_usage":
            return self._generate_du_command(args)
        elif tool.name == "file_info":
            return self._generate_stat_command(args)
        elif tool.name == "list_processes":
            return self._generate_ps_command(args)
        elif tool.name == "process_by_port":
            return self._generate_lsof_command(args)
        elif tool.name == "kill_process":
            return self._generate_kill_command(args)
        elif tool.name == "process_tree":
            return self._generate_pstree_command(args)
        elif tool.name == "system_resources":
            return self._generate_system_resources_command(args)
        elif tool.name == "ping_host":
            return self._generate_ping_command(args)
        elif tool.name == "http_request":
            return self._generate_curl_command(args)
        elif tool.name == "network_connections":
            return self._generate_ss_command(args)
        elif tool.name == "dns_lookup":
            return self._generate_dig_command(args)
        elif tool.name == "download_file":
            return self._generate_wget_command(args)
        elif tool.name == "network_interfaces":
            return self._generate_ip_command(args)
        elif tool.name in ("brew_search", "brew_info", "brew_list"):
            return self._generate_brew_command(tool.name, args)
        elif tool.name in ("apt_search", "apt_info", "apt_list"):
            return self._generate_apt_command(tool.name, args)
        elif tool.name in ("git_status", "git_log", "git_diff", "git_branch", "git_show", "git_remote", "git_blame"):
            return self._generate_git_command(tool.name, args)
        
        # Apply clauses based on arguments for find_files
        clauses = generator.get("clauses", {})
        clause_replacements = {}
        
        for clause_name, clause_template in clauses.items():
            if clause_name == "size_clause" and "min_size" in args:
                clause_replacements[clause_name] = clause_template.format(min_size=args["min_size"])
            elif clause_name == "time_clause" and "modified_within" in args:
                # Convert days format
                time_val = args["modified_within"]
                if time_val.endswith("d"):
                    days = time_val[:-1]
                    clause_replacements[clause_name] = clause_template.format(modified_within=days)
            elif clause_name == "name_clause" and "name" in args:
                clause_replacements[clause_name] = clause_template.format(name=args["name"])
            else:
                clause_replacements[clause_name] = ""
        
        # Replace clauses in template
        for clause_name, replacement in clause_replacements.items():
            cmd_template = cmd_template.replace(f"{{{clause_name}}}", replacement)
        
        # Format the final command with remaining arguments
        try:
            return cmd_template.format(**args)
        except KeyError as e:
            # Handle missing required arguments
            raise ValueError(f"Missing required argument: {e}")
    
    def _generate_ls_command(self, args: Dict[str, Any]) -> str:
        """Generate ls command."""
        flags = ["-l"]  # Always use long format by default
        if args.get("human", True):
            flags.append("-h")
        if args.get("all", False):
            flags.append("-a")
        
        flag_str = "".join(flags)
        path = args.get("path", ".")
        
        cmd_parts = [f"ls -{flag_str}"]
        
        if args.get("sort"):
            cmd_parts.append(f"--sort={args['sort']}")
        
        cmd_parts.append(path)
        return " ".join(cmd_parts)
    
    def _generate_grep_command(self, args: Dict[str, Any]) -> str:
        """Generate grep command."""
        flags = []
        if args.get("recursive", True):
            flags.append("-r")
        if args.get("ignore_case", False):
            flags.append("-i") 
        if args.get("line_numbers", True):
            flags.append("-n")
        
        flag_str = "".join(flags)
        pattern = args["pattern"]
        path = args.get("path", ".")
        
        cmd_parts = [f"grep -{flag_str}", f"'{pattern}'"]
        
        if args.get("file_pattern"):
            cmd_parts.append(f"--include='{args['file_pattern']}'")
        
        cmd_parts.append(path)
        return " ".join(cmd_parts)
    
    def _generate_du_command(self, args: Dict[str, Any]) -> str:
        """Generate du command."""
        flags = []
        if args.get("human", True):
            flags.append("-h")
        
        flag_str = "".join(flags)
        depth = args.get("depth", 1)
        path = args.get("path", ".")
        
        cmd = f"du -{flag_str} --max-depth={depth} {path}"
        
        if args.get("sort", True):
            cmd += " | sort -hr"
        
        return cmd
    
    def _generate_stat_command(self, args: Dict[str, Any]) -> str:
        """Generate stat command."""
        flags = []
        if args.get("follow_links", False):
            flags.append("-L")
        
        flag_str = "".join(flags)
        path = args["path"]
        
        if flag_str:
            return f"stat -{flag_str} {path}"
        else:
            return f"stat {path}"
    
    def _generate_ps_command(self, args: Dict[str, Any]) -> str:
        """Generate ps command."""
        sort_col_map = {
            "cpu": "3",
            "mem": "4", 
            "memory": "4",
            "time": "10",
            "pid": "2"
        }
        
        sort = args.get("sort", "cpu")
        sort_col = sort_col_map.get(sort, "3")
        limit = args.get("limit", 20)
        
        if args.get("port"):
            # Use lsof for port-specific processes
            return f"lsof -i :{args['port']} -P -n"
        elif args.get("name"):
            name = args["name"]
            return f"ps aux | grep '{name}' | grep -v grep"
        else:
            return f"ps aux | head -1 && ps aux | grep -v 'grep' | sort -k{sort_col} -r | head -{limit}"
    
    def _generate_lsof_command(self, args: Dict[str, Any]) -> str:
        """Generate lsof command for port lookup."""
        port = args["port"]
        return f"lsof -i :{port} -P -n"
    
    def _generate_kill_command(self, args: Dict[str, Any]) -> str:
        """Generate kill command."""
        signal = args.get("signal", "TERM")
        
        if args.get("pid"):
            target = str(args["pid"])
        elif args.get("name"):
            # Use pkill for name-based killing
            name = args["name"]
            return f"pkill -{signal} {name}"
        else:
            raise ValueError("Either pid or name must be specified for kill command")
        
        return f"kill -{signal} {target}"
    
    def _generate_pstree_command(self, args: Dict[str, Any]) -> str:
        """Generate pstree command."""
        flags = ["-p"]  # Show PIDs
        
        if args.get("user"):
            return f"pstree {args['user']}"
        elif args.get("pid"):
            return f"pstree -p {args['pid']}"
        else:
            return "pstree -p"
    
    def _generate_system_resources_command(self, args: Dict[str, Any]) -> str:
        """Generate system resource monitoring command."""
        if args.get("detailed"):
            return "top -bn1 | head -20 && echo '--- Memory ---' && free -h && echo '--- Disk ---' && df -h"
        else:
            return "top -bn1 | head -5 && free -h && df -h /"
    
    def _generate_ping_command(self, args: Dict[str, Any]) -> str:
        """Generate ping command."""
        host = args["host"]
        count = args.get("count", 4)
        timeout = args.get("timeout", 5)
        
        return f"ping -c {count} -W {timeout} {host}"
    
    def _generate_curl_command(self, args: Dict[str, Any]) -> str:
        """Generate curl command."""
        url = args["url"]
        method = args.get("method", "GET")
        timeout = args.get("timeout", 30)
        
        flags = [f"-X {method}", f"--max-time {timeout}"]
        
        if args.get("headers"):
            flags.append("-i")  # Include headers
        
        if args.get("follow", True):
            flags.append("-L")  # Follow redirects
        
        flag_str = " ".join(flags)
        return f"curl {flag_str} '{url}'"
    
    def _generate_ss_command(self, args: Dict[str, Any]) -> str:
        """Generate ss (socket statistics) command."""
        flags = ["ss"]
        
        protocol = args.get("protocol")
        if protocol == "tcp":
            flags.append("-t")
        elif protocol == "udp":
            flags.append("-u")
        else:
            flags.append("-tu")  # Both TCP and UDP
        
        if args.get("listening"):
            flags.append("-l")
        
        flags.append("-n")  # Don't resolve hostnames
        
        if args.get("process"):
            flags.append("-p")  # Show process info
        
        return " ".join(flags)
    
    def _generate_dig_command(self, args: Dict[str, Any]) -> str:
        """Generate dig command."""
        host = args["host"]
        record_type = args.get("record_type", "A")
        
        if args.get("reverse"):
            return f"dig -x {host} +short"
        else:
            return f"dig {record_type} {host} +short"
    
    def _generate_wget_command(self, args: Dict[str, Any]) -> str:
        """Generate wget command."""
        url = args["url"]
        flags = []
        
        if args.get("progress", True):
            flags.append("--progress=bar")
        
        if args.get("resume"):
            flags.append("-c")  # Continue/resume
        
        if args.get("output"):
            flags.append(f"-O {args['output']}")
        
        flag_str = " ".join(flags)
        return f"wget {flag_str} '{url}'".strip()
    
    def _generate_ip_command(self, args: Dict[str, Any]) -> str:
        """Generate ip command for network interfaces."""
        if args.get("stats"):
            return "ip -s link show"
        elif args.get("interface"):
            interface = args["interface"]
            return f"ip addr show {interface}"
        else:
            return "ip addr show"
    
    def _generate_brew_command(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Generate brew command."""
        if tool_name == "brew_search":
            package = args["package"]
            if args.get("cask"):
                return f"brew search --cask {package}"
            else:
                return f"brew search {package}"
        elif tool_name == "brew_info":
            package = args["package"]
            return f"brew info {package}"
        elif tool_name == "brew_list":
            if args.get("versions"):
                return "brew list --versions"
            else:
                return "brew list"
        
        return "brew"
    
    def _generate_apt_command(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Generate apt command."""
        if tool_name == "apt_search":
            package = args["package"]
            return f"apt search {package}"
        elif tool_name == "apt_info":
            package = args["package"]
            return f"apt show {package}"
        elif tool_name == "apt_list":
            if args.get("upgradable"):
                return "apt list --upgradable"
            else:
                return "apt list --installed"
        
        return "apt"
    
    def _generate_git_command(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Generate git command."""
        if tool_name == "git_status":
            if args.get("short"):
                return "git status -s"
            else:
                return "git status"
        elif tool_name == "git_log":
            flags = []
            if args.get("oneline"):
                flags.append("--oneline")
            if args.get("graph"):
                flags.append("--graph")
            if args.get("author"):
                flags.append(f"--author='{args['author']}'")
            
            limit = args.get("limit", 10)
            flag_str = " ".join(flags)
            return f"git log {flag_str} -{limit}".strip()
        elif tool_name == "git_diff":
            flags = []
            if args.get("staged"):
                flags.append("--staged")
            if args.get("commit"):
                flags.append(args["commit"])
            if args.get("file"):
                flags.append(args["file"])
            
            flag_str = " ".join(flags)
            return f"git diff {flag_str}".strip()
        elif tool_name == "git_branch":
            flags = []
            if args.get("remote"):
                flags.append("-r")
            elif args.get("all"):
                flags.append("-a")
            
            flag_str = " ".join(flags)
            return f"git branch {flag_str}".strip()
        elif tool_name == "git_show":
            flags = []
            if args.get("stat"):
                flags.append("--stat")
            if args.get("commit"):
                flags.append(args["commit"])
            
            flag_str = " ".join(flags)
            return f"git show {flag_str}".strip()
        elif tool_name == "git_remote":
            if args.get("verbose"):
                return "git remote -v"
            else:
                return "git remote"
        elif tool_name == "git_blame":
            file = args["file"]
            if args.get("line_start") and args.get("line_end"):
                line_range = f"-L {args['line_start']},{args['line_end']}"
                return f"git blame {line_range} {file}"
            else:
                return f"git blame {file}"
        
        return "git"
    
    def print_tools(self, console: Console) -> None:
        """Print available tools."""
        table = Table(title="Available Tools", border_style="green")
        table.add_column("Tool", style="cyan")
        table.add_column("Summary", style="white")
        table.add_column("Danger", style="yellow")
        
        for tool in self.tools.values():
            danger_style = {
                "read_only": "green",
                "modify": "yellow", 
                "destructive": "red"
            }.get(tool.danger_level, "white")
            
            table.add_row(
                tool.name,
                tool.summary,
                f"[{danger_style}]{tool.danger_level}[/{danger_style}]"
            )
        
        console.print(table)
    
    def _load_builtin_tools(self) -> None:
        """Load built-in tool schemas."""
        # Import built-in tools
        from nlcli.tools.file_tools import get_file_tools
        from nlcli.tools.process_tools import get_process_tools
        from nlcli.tools.network_tools import get_network_tools
        from nlcli.tools.package_tools import get_package_tools
        from nlcli.tools.git_tools import get_git_tools
        
        for tool in get_file_tools():
            self.register_tool(tool)
            
        for tool in get_process_tools():
            self.register_tool(tool)
            
        for tool in get_network_tools():
            self.register_tool(tool)
            
        for tool in get_package_tools():
            self.register_tool(tool)
            
        for tool in get_git_tools():
            self.register_tool(tool)


def load_tools() -> ToolRegistry:
    """Load and return the tool registry."""
    return ToolRegistry()