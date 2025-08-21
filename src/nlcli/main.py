"""
Natural Language Driven CLI - Main entry point and REPL
"""
import sys
from typing import Optional

import click
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from nlcli.engine import plan_and_generate, explain, create_llm_from_config
from nlcli.safety import guard
from nlcli.context import SessionContext
from nlcli.registry import load_tools
from nlcli.executor import execute


console = Console()


def print_welcome():
    """Print welcome message and basic usage instructions."""
    welcome_text = Text()
    welcome_text.append("Natural Language Driven CLI", style="bold blue")
    welcome_text.append("\n\nTurn natural language into safe system commands.")
    welcome_text.append("\n\nExamples:")
    welcome_text.append("\n  › show files >1GB modified this week")
    welcome_text.append("\n  › find all .py files containing TODO")
    welcome_text.append("\n  › list processes using port 3000")
    welcome_text.append("\n\nType 'help' for more commands, 'quit' or Ctrl+D to exit.")
    
    console.print(Panel(welcome_text, title="Welcome", border_style="blue"))


def print_help():
    """Print help information."""
    help_text = Text()
    help_text.append("Commands:", style="bold")
    help_text.append("\n  help          Show this help message")
    help_text.append("\n  quit, exit    Exit the CLI")
    help_text.append("\n  clear         Clear session context")
    help_text.append("\n  context       Show current session context")
    help_text.append("\n  tools         List available tools")
    help_text.append("\n\nNatural Language Examples:")
    help_text.append("\n  • Files: 'find large files', 'show .py files modified today'")
    help_text.append("\n  • Processes: 'list running processes', 'show memory usage'")
    help_text.append("\n  • Network: 'check port 3000', 'ping google.com'")
    help_text.append("\n\nSafety Features:")
    help_text.append("\n  • All commands are shown before execution (dry-run)")
    help_text.append("\n  • Confirmation required for destructive operations")
    help_text.append("\n  • Context-aware suggestions and undo hints")
    
    console.print(Panel(help_text, title="Help", border_style="green"))


def repl() -> None:
    """Main REPL loop."""
    print_welcome()
    
    # Initialize components
    ctx = SessionContext()
    tools = load_tools()
    llm = create_llm_from_config()  # Initialize LLM (may be disabled)
    history = FileHistory(".nlcli_history")
    
    # Show LLM status if enabled
    if llm.is_available():
        console.print("🧠 Local LLM integration is enabled", style="dim green")
    else:
        console.print("💡 Tip: Set NLCLI_LLM_ENABLED=true to enable local LLM integration", style="dim yellow")
    
    while True:
        try:
            # Get user input with history and auto-suggestions
            nl_input = prompt(
                "› ",
                history=history,
                auto_suggest=AutoSuggestFromHistory(),
                multiline=False
            ).strip()
            
            if not nl_input:
                continue
                
            # Handle special commands
            if nl_input.lower() in ("quit", "exit"):
                console.print("Goodbye! 👋", style="blue")
                break
            elif nl_input.lower() == "help":
                print_help()
                continue
            elif nl_input.lower() == "clear":
                ctx.clear()
                console.print("Session context cleared.", style="yellow")
                continue
            elif nl_input.lower() == "context":
                ctx.print_context(console)
                continue
            elif nl_input.lower() == "tools":
                tools.print_tools(console)
                continue
            
            # Process natural language input
            try:
                # Plan and generate command
                intent = plan_and_generate(nl_input, ctx, tools, llm)
                
                if intent is None:
                    console.print("❌ Sorry, I couldn't understand that request.", style="red")
                    console.print("Try being more specific or type 'help' for examples.")
                    continue
                
                # Show explanation and command
                explanation = explain(intent)
                console.print(f"\n💡 {explanation}", style="cyan")
                console.print(f"📝 Command: [bold]{intent.command}[/bold]")
                
                # Safety check
                if not guard(intent, ctx):
                    console.print("❌ Command blocked by safety checks.", style="red")
                    continue
                
                # Confirmation for destructive operations
                if intent.danger_level in ("destructive", "modify"):
                    confirmation = prompt(f"⚠️  This will modify your system. Continue? [y/N] ").lower()
                    if confirmation not in ("y", "yes"):
                        console.print("Operation cancelled.", style="yellow")
                        continue
                
                # Execute command
                result = execute(intent.command, ctx)
                
                if result.success:
                    console.print("✅ Command executed successfully", style="green")
                    if result.output:
                        console.print(result.output)
                    # Update context with results
                    ctx.update_from_intent(intent)
                    ctx.update_from_result(result)
                else:
                    console.print(f"❌ Command failed: {result.error}", style="red")
                    
            except KeyboardInterrupt:
                console.print("\nOperation cancelled.", style="yellow")
                continue
            except Exception as e:
                console.print(f"❌ Error: {e}", style="red")
                continue
                
        except KeyboardInterrupt:
            console.print("\nGoodbye! 👋", style="blue")
            break
        except EOFError:
            console.print("\nGoodbye! 👋", style="blue")
            break


@click.command()
@click.option("--dry-run", is_flag=True, help="Show commands without executing")
@click.option("--explain", is_flag=True, help="Show explanations for commands")
@click.option("--lang", default="en", help="Language for natural language input")
@click.version_option(version="0.1.0")
def main(dry_run: bool, explain: bool, lang: str) -> None:
    """Natural Language Driven CLI - Turn natural language into safe system commands."""
    if dry_run:
        console.print("🔍 Dry-run mode enabled - commands will be shown but not executed", style="yellow")
    
    if lang != "en":
        console.print(f"🌐 Language set to: {lang}", style="blue")
        console.print("Note: Only English is fully supported in this version", style="yellow")
    
    try:
        repl()
    except Exception as e:
        console.print(f"Fatal error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()