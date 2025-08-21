"""
Natural Language Driven CLI - Main entry point and REPL
"""
import sys
from typing import Optional
from pathlib import Path

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
    help_text.append("\n  context advanced Show advanced context analysis")
    help_text.append("\n  tools         List available tools")
    help_text.append("\n  plugins       Show loaded plugins")
    help_text.append("\n  reload plugins Reload all plugins")
    help_text.append("\n  lang status   Show language support status")
    help_text.append("\n  cloud status  Show cloud LLM provider status")
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
            elif nl_input.lower() == "plugins":
                # Show plugin information
                from nlcli.plugins import get_plugin_manager
                plugin_manager = get_plugin_manager()
                plugin_list = plugin_manager.get_plugin_list()
                
                if not plugin_list:
                    console.print("No plugins loaded.", style="yellow")
                else:
                    from rich.table import Table
                    table = Table(title="Loaded Plugins", border_style="blue")
                    table.add_column("Name", style="cyan")
                    table.add_column("Version", style="white")
                    table.add_column("Tools", justify="right")
                    table.add_column("Status", justify="center")
                    
                    for plugin in plugin_list:
                        status = "✅ Enabled" if plugin["enabled"] else "❌ Disabled"
                        table.add_row(
                            plugin["name"],
                            plugin["version"],
                            str(plugin["tools_count"]),
                            status
                        )
                    console.print(table)
                continue
            elif nl_input.lower().startswith("reload plugins"):
                # Reload plugins
                tools.reload_plugins()
                console.print("Plugins reloaded.", style="green")
                continue
            elif nl_input.lower() == "lang status":
                # Show language support status
                try:
                    from nlcli.language import get_language_processor
                    lang_processor = get_language_processor()
                    console.print(f"🌐 Default language: {lang_processor.config.default_language}", style="blue")
                    console.print(f"📝 Enabled languages: {', '.join(lang_processor.config.enabled_languages)}", style="blue")
                    console.print(f"🔄 Auto-detect: {ctx.preferences.get('auto_detect_language', True)}", style="blue")
                except ImportError:
                    console.print("❌ Language support not available", style="red")
                continue
            elif nl_input.lower() == "cloud status":
                # Show cloud LLM status
                try:
                    from nlcli.cloud_llm import get_cloud_llm_service
                    cloud_llm = get_cloud_llm_service()
                    status = cloud_llm.get_provider_status()
                    
                    from rich.table import Table
                    table = Table(title="Cloud LLM Status", border_style="blue")
                    table.add_column("Provider", style="cyan")
                    table.add_column("Status", justify="center")
                    table.add_column("Model")
                    
                    for provider, info in status.items():
                        status_emoji = "✅" if info["configured"] else "❌"
                        status_text = "Configured" if info["configured"] else "Not configured"
                        table.add_row(provider.title(), f"{status_emoji} {status_text}", info["model"])
                    
                    console.print(table)
                except ImportError:
                    console.print("❌ Cloud LLM support not available", style="red")
                continue
            elif nl_input.lower() == "context advanced":
                # Show advanced context information
                try:
                    from nlcli.advanced_context import get_advanced_context_manager
                    advanced_ctx = get_advanced_context_manager()
                    
                    # Show conversation patterns
                    patterns = advanced_ctx.analyze_patterns()
                    
                    console.print("📊 Advanced Context Analysis:", style="bold blue")
                    console.print(f"Success rate: {patterns['patterns']['success_rate']:.1%}")
                    console.print(f"Total conversations: {patterns['patterns']['total_turns']}")
                    
                    if patterns['insights']:
                        console.print("💡 Insights:")
                        for insight in patterns['insights']:
                            console.print(f"  • {insight}")
                except ImportError:
                    console.print("❌ Advanced context support not available", style="red")
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
@click.option("--batch", type=click.Path(exists=True, path_type=Path), help="Execute batch script file")
@click.option("--batch-commands", multiple=True, help="Execute multiple commands in batch mode")
@click.option("--stop-on-error", is_flag=True, default=True, help="Stop batch execution on first error")
@click.version_option(version="0.1.0")
def main(dry_run: bool, explain: bool, lang: str, batch: Optional[Path], 
         batch_commands: tuple, stop_on_error: bool) -> None:
    """Natural Language Driven CLI - Turn natural language into safe system commands."""
    if dry_run:
        console.print("🔍 Dry-run mode enabled - commands will be shown but not executed", style="yellow")
    
    if lang != "en":
        console.print(f"🌐 Language set to: {lang}", style="blue")
        # Initialize language processor
        try:
            from nlcli.language import get_language_processor
            lang_processor = get_language_processor()
            console.print(f"✅ Multi-language support enabled", style="green")
        except ImportError:
            console.print("⚠️  Multi-language support not available", style="yellow")
    
    # Initialize components
    ctx = SessionContext()
    tools = load_tools()
    llm = create_llm_from_config()
    
    # Handle batch mode
    if batch or batch_commands:
        from nlcli.batch import BatchModeManager
        batch_manager = BatchModeManager(ctx, tools, llm)
        
        try:
            if batch:
                console.print(f"🔄 Executing batch script: {batch}", style="blue")
                results = batch_manager.execute_script_file(batch, dry_run=dry_run, stop_on_error=stop_on_error)
            else:
                console.print(f"🔄 Executing {len(batch_commands)} batch commands", style="blue")
                results = batch_manager.execute_commands(list(batch_commands), dry_run=dry_run, stop_on_error=stop_on_error)
            
            # Print results
            formatted_results = batch_manager.format_results(results)
            console.print(formatted_results)
            
            # Exit after batch execution
            success_count = sum(1 for r in results if r.success)
            if success_count == len(results):
                sys.exit(0)
            else:
                sys.exit(1)
                
        except Exception as e:
            console.print(f"❌ Batch execution failed: {e}", style="red")
            sys.exit(1)
    
    # Continue with interactive mode
    try:
        repl()
    except Exception as e:
        console.print(f"Fatal error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()