"""
Engine for planning and generating commands from natural language.
"""
import re
from typing import Optional

from nlcli.context import SessionContext, Intent
from nlcli.registry import ToolRegistry


def plan_and_generate(nl_input: str, context: SessionContext, tools: ToolRegistry) -> Optional[Intent]:
    """
    Main function to convert natural language to executable intent.
    
    Args:
        nl_input: Natural language input from user
        context: Current session context
        tools: Tool registry
    
    Returns:
        Intent object with command and metadata, or None if no match
    """
    # Preprocess input - resolve pronouns and clean up
    processed_input = context.resolve_pronouns(nl_input.strip())
    
    # Find matching tools
    matching_tools = tools.find_matching_tools(processed_input)
    
    if not matching_tools:
        return None
    
    # Use the best matching tool
    best_tool, confidence = matching_tools[0]
    
    # Extract arguments for the chosen tool
    try:
        context_info = context.get_context_for_command()
        args = tools.extract_args(best_tool, processed_input, context_info)
        
        # Generate command
        command = tools.generate_command(best_tool, args)
        
        # Create explanation
        explanation = generate_explanation(best_tool, args, processed_input)
        
        # Create intent object
        intent = Intent(
            tool_name=best_tool.name,
            args=args,
            command=command,
            explanation=explanation,
            danger_level=best_tool.danger_level,
            confidence=confidence
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
        "file_info": "I'll show file information"
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
        r"what is": "show"
    }
    
    for pattern, replacement in normalizations.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
    
    # Normalize file size units
    size_normalizations = {
        r"(\d+)\s*(gigabyte|gigabytes|giga|gb)", 
        r"(\d+)\s*(megabyte|megabytes|mega|mb)",
        r"(\d+)\s*(kilobyte|kilobytes|kilo|kb)"
    }
    
    processed = re.sub(r"(\d+)\s*(?:gigabyte|gigabytes|giga|gb)", r"\1GB", processed, flags=re.IGNORECASE)
    processed = re.sub(r"(\d+)\s*(?:megabyte|megabytes|mega|mb)", r"\1MB", processed, flags=re.IGNORECASE)
    processed = re.sub(r"(\d+)\s*(?:kilobyte|kilobytes|kilo|kb)", r"\1KB", processed, flags=re.IGNORECASE)
    
    return processed