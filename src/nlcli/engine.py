"""
Engine for planning and generating commands from natural language.
Enhanced with Phase 4 Production Ready features.
"""

import re
from typing import Any, Dict, Optional, Tuple

from nlcli.context import Intent, SessionContext
from nlcli.llm import LLMConfig, LocalLLM, default_llm
from nlcli.registry import ToolRegistry


def enhanced_plan_and_generate(
    nl_input: str,
    context: SessionContext,
    tools: ToolRegistry,
    llm: Optional[LocalLLM] = None,
    session_id: Optional[str] = None,
) -> Tuple[Optional[Intent], Dict[str, Any]]:
    """
    Enhanced planning and generation with Phase 4 production features.

    Args:
        nl_input: Natural language input from user
        context: Current session context
        tools: Tool registry
        llm: Optional local LLM for enhanced understanding
        session_id: Session ID for tracking

    Returns:
        Tuple of (Intent object, metadata dict)
    """
    metadata = {
        "enhanced_features_enabled": True,
        "performance_metrics": {},
        "security_violations": [],
        "error_recovery_applied": False,
        "telemetry_recorded": True,
    }

    try:
        # Import Phase 4 modules (lazy loading for backward compatibility)
        from nlcli.enterprise import get_enterprise_manager
        from nlcli.error_recovery import ErrorContext, get_error_recovery_manager
        from nlcli.performance import get_performance_profiler
        from nlcli.security import get_security_auditor
        from nlcli.telemetry import get_telemetry_manager

        profiler = get_performance_profiler()
        recovery_manager = get_error_recovery_manager()
        telemetry = get_telemetry_manager()

        # Profile the entire planning operation
        with profiler.profile_operation(
            "plan_and_generate", {"input_length": len(nl_input)}
        ) as _perf_context:  # noqa: F841

            # Record telemetry event
            telemetry.events.log_event(
                {
                    "event_type": "command_planning_started",
                    "session_id": session_id,
                    "input_length": len(nl_input),
                }
            )

            # Use basic planning with error recovery
            error_context = ErrorContext(
                operation="plan_and_generate",
                user_input=nl_input,
                session_id=session_id,
            )

            try:
                intent = plan_and_generate(nl_input, context, tools, llm)

                if intent:
                    # Enhanced security audit
                    security_auditor = get_security_auditor()
                    violations = security_auditor.audit_command(intent, context)
                    metadata["security_violations"] = [
                        {
                            "type": v.violation_type.value,
                            "severity": v.severity.value,
                            "description": v.description,
                        }
                        for v in violations
                    ]

                    # Enterprise policy check
                    enterprise = get_enterprise_manager()
                    if enterprise.config_manager.get_config_value(
                        "enterprise.enabled", False
                    ):
                        policy_result = enterprise.evaluate_command(intent.command)
                        if not policy_result.get("allowed", True):
                            metadata["policy_violations"] = policy_result.get(
                                "violations", []
                            )

                    # Record successful planning
                    telemetry.record_command_execution(
                        command=intent.command,
                        success=True,
                        duration=0,  # Will be filled by profiler
                        tool_name=intent.tool_name,
                        confidence=intent.confidence,
                    )

                return intent, metadata

            except Exception as e:
                # Apply error recovery
                recovery_result = recovery_manager.handle_error(e, error_context)
                metadata["error_recovery_applied"] = recovery_result is not None

                if recovery_result and recovery_result.get("use_fallback"):
                    # Try fallback approach (basic heuristics only)
                    intent = basic_plan_and_generate(nl_input, context, tools)
                    return intent, metadata
                else:
                    raise

    except ImportError:
        # Fallback to basic planning if Phase 4 modules not available
        intent = plan_and_generate(nl_input, context, tools, llm)
        metadata["enhanced_features_enabled"] = False
        return intent, metadata
    except Exception as e:
        # Log error but continue with basic approach
        import logging

        logging.getLogger(__name__).error(f"Enhanced planning failed: {e}")
        intent = plan_and_generate(nl_input, context, tools, llm)
        metadata["enhanced_features_enabled"] = False
        metadata["error"] = str(e)
        return intent, metadata


def basic_plan_and_generate(
    nl_input: str, context: SessionContext, tools: ToolRegistry
) -> Optional[Intent]:
    """
    Basic planning without LLM or enhanced features.
    Fallback for error recovery scenarios.
    """
    # Simple keyword-based matching
    processed_input = context.resolve_pronouns(nl_input.strip())
    matching_tools = tools.find_matching_tools(processed_input)

    if not matching_tools:
        return None

    best_tool, confidence = matching_tools[0]

    try:
        args = tools.extract_args(
            best_tool, processed_input, context.get_context_for_command()
        )
        command = tools.generate_command(best_tool, args)

        return Intent(
            tool_name=best_tool.name,
            args=args,
            command=command,
            explanation=f"Basic command generation: {command}",
            danger_level=best_tool.danger_level,
            confidence=confidence * 0.8,  # Lower confidence for fallback
        )
    except Exception:
        return None


def plan_and_generate(
    nl_input: str,
    context: SessionContext,
    tools: ToolRegistry,
    llm: Optional[LocalLLM] = None,
) -> Optional[Intent]:
    """
    Main function to convert natural language to executable intent.

    Args:
        nl_input: Natural language input from user
        context: Current session context
        tools: Tool registry
        llm: Optional local LLM for enhanced understanding

    Returns:
        Intent object with command and metadata, or None if no match
    """
    if llm is None:
        llm = default_llm

    # Preprocess input - resolve pronouns and clean up
    processed_input = context.resolve_pronouns(nl_input.strip())

    # Use LLM for enhanced intent understanding if available
    if llm.is_available():
        llm_response = llm.enhance_intent_understanding(
            processed_input, context.get_context_for_command()
        )
        if llm_response.success:
            processed_input = llm_response.text

    # Find matching tools
    matching_tools = tools.find_matching_tools(processed_input)

    if not matching_tools:
        return None

    # Use the best matching tool
    best_tool, confidence = matching_tools[0]

    # Use LLM for tool selection validation if available
    if llm.is_available() and len(matching_tools) > 1:
        tool_names = [tool.name for tool, _ in matching_tools[:5]]  # Top 5 candidates
        # LLM suggestion for future enhancement
        _llm_suggestion = llm.suggest_tool_selection(  # noqa: F841
            processed_input, tool_names
        )
        # For now, we still use the heuristic selection, but this could be enhanced

    # Extract arguments for the chosen tool
    try:
        context_info = context.get_context_for_command()
        args = tools.extract_args(best_tool, processed_input, context_info)

        # Generate command
        command = tools.generate_command(best_tool, args)

        # Create explanation (potentially enhanced by LLM)
        if llm.is_available():
            explanation = llm.explain_command(command, context_info)
        else:
            explanation = generate_explanation(best_tool, args, processed_input)

        # Create intent object
        intent = Intent(
            tool_name=best_tool.name,
            args=args,
            command=command,
            explanation=explanation,
            danger_level=best_tool.danger_level,
            confidence=confidence,
        )

        return intent

    except Exception as e:
        # Log error in practice, for now return None
        print(f"Error generating command: {e}")
        return None


def explain(intent: Intent) -> str:
    """
    Generate natural language explanation of what the command will do.

    Args:
        intent: Intent object with command details

    Returns:
        Human-readable explanation string
    """
    if not intent:
        return "No valid command could be generated."

    return intent.explanation


def generate_explanation(tool_schema, args: dict, original_input: str) -> str:
    """
    Generate explanation based on tool and arguments.

    Args:
        tool_schema: ToolSchema object
        args: Extracted arguments
        original_input: Original user input

    Returns:
        Natural language explanation
    """
    base_action = {
        "find_files": "I'll search for files",
        "list_files": "I'll list directory contents",
        "search_content": "I'll search for text content",
        "disk_usage": "I'll show disk usage information",
        "file_info": "I'll show file information",
        "list_processes": "I'll show running processes",
        "process_by_port": "I'll find processes using the specified port",
        "kill_process": "I'll terminate the specified process",
        "process_tree": "I'll show the process tree hierarchy",
        "system_resources": "I'll show system resource usage",
        "ping_host": "I'll ping the specified host",
        "http_request": "I'll make an HTTP request",
        "network_connections": "I'll show network connections",
        "dns_lookup": "I'll perform a DNS lookup",
        "download_file": "I'll download the file",
        "network_interfaces": "I'll show network interface information",
    }.get(tool_schema.name, "I'll execute a command")

    # Build explanation based on arguments
    explanation_parts = [base_action]

    # Add location information
    if "path" in args and args["path"] != ".":
        if args["path"].startswith("~"):
            explanation_parts.append(f"in your home directory ({args['path']})")
        else:
            explanation_parts.append(f"in {args['path']}")
    elif "path" in args and args["path"] == ".":
        explanation_parts.append("in the current directory")

    # Add filtering conditions
    filters = []

    if "min_size" in args:
        filters.append(f"larger than {args['min_size']}")

    if "max_size" in args:
        filters.append(f"smaller than {args['max_size']}")

    if "modified_within" in args:
        time_val = args["modified_within"]
        if time_val == "1d":
            filters.append("modified today")
        elif time_val == "7d":
            filters.append("modified this week")
        elif time_val.endswith("d"):
            days = time_val[:-1]
            filters.append(f"modified in the last {days} days")
        else:
            filters.append(f"modified within {time_val}")

    if "name" in args:
        filters.append(f"matching pattern '{args['name']}'")

    if "pattern" in args:
        filters.append(f"containing '{args['pattern']}'")

    if "file_pattern" in args:
        filters.append(f"in {args['file_pattern']} files")

    # Add network/process-specific conditions
    if "host" in args:
        filters.append(f"for host {args['host']}")

    if "port" in args:
        filters.append(f"on port {args['port']}")

    if "count" in args and tool_schema.name == "ping_host":
        count = args["count"]
        if count == 1:
            filters.append("once")
        else:
            filters.append(f"{count} times")

    if "method" in args and args["method"] != "GET":
        filters.append(f"using {args['method']} method")

    if "record_type" in args and args["record_type"] != "A":
        filters.append(f"for {args['record_type']} records")

    if "sort" in args and tool_schema.name == "list_processes":
        sort_type = args["sort"]
        if sort_type == "mem":
            filters.append("sorted by memory usage")
        elif sort_type == "cpu":
            filters.append("sorted by CPU usage")
        else:
            filters.append(f"sorted by {sort_type}")

    if "signal" in args and tool_schema.name == "kill_process":
        signal = args["signal"]
        if signal == "KILL":
            filters.append("using force")
        elif signal != "TERM":
            filters.append(f"using {signal} signal")

    # Combine filters with appropriate conjunctions
    if filters:
        if len(filters) == 1:
            explanation_parts.append(filters[0])
        elif len(filters) == 2:
            explanation_parts.append(f"{filters[0]} and {filters[1]}")
        else:
            explanation_parts.append(", ".join(filters[:-1]) + f", and {filters[-1]}")

    # Add action-specific details
    if tool_schema.name == "list_files":
        if args.get("all"):
            explanation_parts.append("(including hidden files)")
        if args.get("sort"):
            explanation_parts.append(f"sorted by {args['sort']}")

    elif tool_schema.name == "disk_usage":
        if args.get("depth", 1) > 1:
            explanation_parts.append(f"with {args['depth']} levels of depth")

    elif tool_schema.name in ("ping_host", "http_request", "dns_lookup"):
        # These tools already have their target in the filters
        pass

    elif tool_schema.name == "network_connections":
        if args.get("listening"):
            explanation_parts.append("showing only listening ports")
        if args.get("process"):
            explanation_parts.append("including process information")

    elif tool_schema.name == "download_file":
        if args.get("output"):
            explanation_parts.append(f"saving as {args['output']}")
        if args.get("resume"):
            explanation_parts.append("resuming previous download")

    elif tool_schema.name == "kill_process":
        if args.get("pid"):
            explanation_parts.append(f"with PID {args['pid']}")
        elif args.get("name"):
            explanation_parts.append(f"named '{args['name']}'")

    elif tool_schema.name == "system_resources":
        if args.get("detailed"):
            explanation_parts.append("with detailed information")

    # Join all parts into a coherent explanation
    explanation = " ".join(explanation_parts)

    # Add a period if not already there
    if not explanation.endswith("."):
        explanation += "."

    return explanation


def preprocess_input(text: str) -> str:
    """
    Preprocess natural language input for better parsing.

    Args:
        text: Raw user input

    Returns:
        Cleaned and normalized text
    """
    # Convert to lowercase for processing (preserve original for display)
    processed = text.strip()

    # Normalize common phrases
    normalizations = {
        r"show me": "show",
        r"find me": "find",
        r"list me": "list",
        r"search for": "search",
        r"look for": "find",
        r"what are": "show",
        r"what is": "show",
    }

    for pattern, replacement in normalizations.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

    # Normalize file size units
    _size_normalizations = {  # noqa: F841
        r"(\d+)\s*(gigabyte|gigabytes|giga|gb)",
        r"(\d+)\s*(megabyte|megabytes|mega|mb)",
        r"(\d+)\s*(kilobyte|kilobytes|kilo|kb)",
    }

    processed = re.sub(
        r"(\d+)\s*(?:gigabyte|gigabytes|giga|gb)",
        r"\1GB",
        processed,
        flags=re.IGNORECASE,
    )
    processed = re.sub(
        r"(\d+)\s*(?:megabyte|megabytes|mega|mb)",
        r"\1MB",
        processed,
        flags=re.IGNORECASE,
    )
    processed = re.sub(
        r"(\d+)\s*(?:kilobyte|kilobytes|kilo|kb)",
        r"\1KB",
        processed,
        flags=re.IGNORECASE,
    )

    return processed


def create_llm_from_config() -> LocalLLM:
    """
    Create LLM instance from configuration.
    Checks environment variables and config files for LLM settings.

    Returns:
        LocalLLM instance (may be disabled)
    """
    import os

    # Check for LLM configuration in environment
    llm_enabled = os.getenv("NLCLI_LLM_ENABLED", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    model_path = os.getenv("NLCLI_LLM_MODEL_PATH")
    model_type = os.getenv("NLCLI_LLM_MODEL_TYPE", "huggingface")

    config = LLMConfig(
        enabled=llm_enabled, model_path=model_path, model_type=model_type
    )

    return LocalLLM(config)
