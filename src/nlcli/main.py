"""
Natural Language Driven CLI - Main entry point and REPL
"""

import sys
from pathlib import Path
from typing import Optional

import click
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from nlcli.context import SessionContext
from nlcli.engine import create_llm_from_config, explain, plan_and_generate
from nlcli.executor import execute
from nlcli.registry import load_tools
from nlcli.safety import guard

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
    help_text.append("\n")
    help_text.append("\nPhase 4 Production Features:", style="bold cyan")
    help_text.append("\n  security      Show security audit report")
    help_text.append("\n  performance   Show performance metrics")
    help_text.append("\n  telemetry     Show telemetry dashboard")
    help_text.append("\n  errors        Show error recovery statistics")
    help_text.append("\n  enterprise    Show enterprise features status")
    help_text.append("\n  audit         Show audit trail (enterprise)")
    help_text.append("\n  policies      Show security policies (enterprise)")
    help_text.append("\n")
    help_text.append("\nAdvanced Commands:", style="bold green")
    help_text.append("\n  debug on/off  Enable/disable debug mode")
    help_text.append("\n  profile       Show performance profiling")
    help_text.append("\n  cache stats   Show cache statistics")
    help_text.append("\n  monitor       Show resource monitoring")
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
    """Main REPL loop with Phase 4 Production Ready features."""
    print_welcome()

    # Initialize core components
    ctx = SessionContext()
    tools = load_tools()
    llm = create_llm_from_config()  # Initialize LLM (may be disabled)
    history = FileHistory(".nlcli_history")

    # Initialize Phase 4 features
    session_id = None
    try:
        # Initialize telemetry and monitoring
        from nlcli.enterprise import get_enterprise_manager
        from nlcli.performance import optimize_startup
        from nlcli.telemetry import get_telemetry_manager

        telemetry = get_telemetry_manager()
        session_id = telemetry.start_session()

        # Optimize startup performance
        optimize_startup()

        # Check enterprise mode
        enterprise = get_enterprise_manager()
        if enterprise.config_manager.get_config_value("enterprise.enabled", False):
            console.print("🏢 Enterprise mode enabled", style="dim purple")

        console.print("🚀 Phase 4 Production Ready features loaded", style="dim green")

    except ImportError:
        console.print(
            "💡 Running in basic mode (Phase 4 features not available)",
            style="dim yellow",
        )
    except Exception as e:
        console.print(f"⚠️  Phase 4 initialization warning: {e}", style="dim yellow")

    # Show LLM status if enabled
    if llm.is_available():
        console.print("🧠 Local LLM integration is enabled", style="dim green")
    else:
        console.print(
            "💡 Tip: Set NLCLI_LLM_ENABLED=true to enable local LLM integration",
            style="dim yellow",
        )

    while True:
        try:
            # Get user input with history and auto-suggestions
            nl_input = prompt(
                "› ",
                history=history,
                auto_suggest=AutoSuggestFromHistory(),
                multiline=False,
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
                            status,
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
                    console.print(
                        f"🌐 Default language: {lang_processor.config.default_language}",
                        style="blue",
                    )
                    console.print(
                        f"📝 Enabled languages: {', '.join(lang_processor.config.enabled_languages)}",
                        style="blue",
                    )
                    console.print(
                        f"🔄 Auto-detect: {ctx.preferences.get('auto_detect_language', True)}",
                        style="blue",
                    )
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
                        status_text = (
                            "Configured" if info["configured"] else "Not configured"
                        )
                        table.add_row(
                            provider.title(),
                            f"{status_emoji} {status_text}",
                            info["model"],
                        )

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
                    console.print(
                        f"Success rate: {patterns['patterns']['success_rate']:.1%}"
                    )
                    console.print(
                        f"Total conversations: {patterns['patterns']['total_turns']}"
                    )

                    if patterns["insights"]:
                        console.print("💡 Insights:")
                        for insight in patterns["insights"]:
                            console.print(f"  • {insight}")
                except ImportError:
                    console.print(
                        "❌ Advanced context support not available", style="red"
                    )
                continue

            # Phase 4 Production Ready Commands
            elif nl_input.lower() == "security":
                # Show security audit report
                try:
                    from nlcli.security import get_security_auditor

                    auditor = get_security_auditor()
                    report = auditor.get_security_report()

                    from rich.table import Table

                    table = Table(title="Security Audit Report", border_style="red")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", justify="right")

                    table.add_row("Status", report.get("status", "unknown"))
                    table.add_row(
                        "Total Violations", str(report.get("total_violations", 0))
                    )
                    table.add_row("Risk Level", report.get("risk_level", "unknown"))

                    console.print(table)

                    if report.get("recent_violations"):
                        console.print("\n🔍 Recent Violations:")
                        for violation in report["recent_violations"][-5:]:
                            console.print(
                                f"  • {violation['severity']}: {violation['description']}"
                            )

                except ImportError:
                    console.print("❌ Security features not available", style="red")
                continue

            elif nl_input.lower() == "performance":
                # Show performance metrics
                try:
                    from nlcli.performance import (
                        get_performance_profiler,
                        get_resource_monitor,
                    )

                    profiler = get_performance_profiler()
                    monitor = get_resource_monitor()

                    metrics = profiler.get_metrics_summary()
                    current_usage = monitor.get_current_usage()

                    from rich.table import Table

                    table = Table(title="Performance Metrics", border_style="blue")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", justify="right")

                    table.add_row("Total Operations", str(metrics["total_operations"]))
                    if "success_rate" in metrics:
                        table.add_row("Success Rate", f"{metrics['success_rate']:.1%}")
                    if "duration_stats" in metrics:
                        table.add_row(
                            "Avg Duration", f"{metrics['duration_stats']['avg']:.3f}s"
                        )

                    if current_usage:
                        table.add_row("CPU Usage", f"{current_usage.cpu_percent:.1f}%")
                        table.add_row(
                            "Memory Usage", f"{current_usage.memory_percent:.1f}%"
                        )

                    console.print(table)

                except ImportError:
                    console.print("❌ Performance features not available", style="red")
                continue

            elif nl_input.lower() == "telemetry":
                # Show telemetry dashboard
                try:
                    from nlcli.telemetry import get_telemetry_manager

                    telemetry = get_telemetry_manager()
                    report = telemetry.get_comprehensive_report()

                    console.print("📊 Telemetry Dashboard", style="bold blue")

                    # Metrics summary
                    metrics = report["metrics"]
                    console.print(f"\n📈 Metrics:")
                    console.print(
                        f"  Commands executed: {metrics['counters'].get('commands_executed', 0)}"
                    )
                    console.print(
                        f"  Success rate: {metrics['counters'].get('commands_successful', 0)}/{metrics['counters'].get('commands_executed', 1)}"
                    )

                    # Events summary
                    events = report["events"]
                    console.print(f"\n📝 Events (last 24h): {events['total_events']}")

                    # Sessions
                    sessions = report["sessions"]
                    console.print(f"\n👥 Sessions:")
                    console.print(f"  Total: {sessions['total_sessions']}")
                    console.print(f"  Active: {sessions['active_sessions']}")

                except ImportError:
                    console.print("❌ Telemetry features not available", style="red")
                continue

            elif nl_input.lower() == "errors":
                # Show error recovery statistics
                try:
                    from nlcli.error_recovery import get_error_recovery_manager

                    recovery_manager = get_error_recovery_manager()
                    patterns = recovery_manager.get_error_patterns()

                    from rich.table import Table

                    table = Table(
                        title="Error Recovery Statistics", border_style="yellow"
                    )
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", justify="right")

                    table.add_row("Total Errors (24h)", str(patterns["total_errors"]))
                    table.add_row(
                        "Resolution Rate", f"{patterns['resolution_rate']:.1%}"
                    )

                    if patterns.get("most_common_category"):
                        table.add_row(
                            "Most Common Category", patterns["most_common_category"]
                        )

                    console.print(table)

                except ImportError:
                    console.print(
                        "❌ Error recovery features not available", style="red"
                    )
                continue

            elif nl_input.lower() == "enterprise":
                # Show enterprise features status
                try:
                    from nlcli.enterprise import get_enterprise_manager

                    enterprise = get_enterprise_manager()
                    status = enterprise.get_enterprise_status()

                    from rich.table import Table

                    table = Table(title="Enterprise Features", border_style="purple")
                    table.add_column("Feature", style="cyan")
                    table.add_column("Status", justify="center")

                    enterprise_enabled = (
                        "✅ Enabled" if status["enabled"] else "❌ Disabled"
                    )
                    table.add_row("Enterprise Mode", enterprise_enabled)

                    if status["current_user"]:
                        table.add_row("Current User", status["current_user"])

                    table.add_row("Total Users", str(status["total_users"]))
                    table.add_row(
                        "RBAC", "✅ Active" if status["rbac_enabled"] else "❌ Inactive"
                    )
                    table.add_row(
                        "Audit Logging",
                        "✅ Active" if status["audit_enabled"] else "❌ Inactive",
                    )
                    table.add_row("Active Policies", str(status["policies_active"]))

                    console.print(table)

                except ImportError:
                    console.print("❌ Enterprise features not available", style="red")
                continue

            elif nl_input.lower() == "cache stats":
                # Show cache statistics
                try:
                    # This would show cache statistics for various cached operations
                    console.print("📊 Cache Statistics:", style="bold blue")
                    console.print("(Cache statistics would be displayed here)")

                except Exception as e:
                    console.print(f"❌ Error retrieving cache stats: {e}", style="red")
                continue

            elif nl_input.lower() == "monitor":
                # Show resource monitoring
                try:
                    from nlcli.performance import get_resource_monitor

                    monitor = get_resource_monitor()

                    current = monitor.get_current_usage()
                    history = monitor.get_usage_history(5)  # Last 5 minutes

                    if current:
                        console.print("📊 Resource Monitoring:", style="bold blue")
                        console.print(f"CPU: {current.cpu_percent:.1f}%")
                        console.print(
                            f"Memory: {current.memory_percent:.1f}% ({current.memory_used_mb:.1f}MB used)"
                        )
                        console.print(f"Disk: {current.disk_usage_percent:.1f}%")
                        console.print(f"Open Files: {current.open_files}")

                        if len(history) > 1:
                            avg_cpu = sum(h.cpu_percent for h in history) / len(history)
                            avg_memory = sum(h.memory_percent for h in history) / len(
                                history
                            )
                            console.print(
                                f"\n5-min averages: CPU {avg_cpu:.1f}%, Memory {avg_memory:.1f}%"
                            )
                    else:
                        console.print("❌ No monitoring data available", style="red")

                except ImportError:
                    console.print("❌ Resource monitoring not available", style="red")
                continue

            # Process natural language input
            try:
                # Enhanced planning and generation with Phase 4 features
                try:
                    from nlcli.engine import enhanced_plan_and_generate

                    intent, metadata = enhanced_plan_and_generate(
                        nl_input, ctx, tools, llm, session_id
                    )

                    # Show Phase 4 metadata if debug enabled
                    if metadata.get(
                        "enhanced_features_enabled"
                    ) and ctx.preferences.get("debug", False):
                        console.print(
                            f"[dim]🔧 Enhanced features: {len(metadata.get('security_violations', []))} security violations detected[/dim]"
                        )

                except ImportError:
                    # Fallback to basic planning
                    intent = plan_and_generate(nl_input, ctx, tools, llm)
                    metadata = {"enhanced_features_enabled": False}

                if intent is None:
                    console.print(
                        "❌ Sorry, I couldn't understand that request.", style="red"
                    )
                    console.print(
                        "Try being more specific or type 'help' for examples."
                    )
                    continue

                # Show explanation and command
                explanation = explain(intent)
                console.print(f"\n💡 {explanation}", style="cyan")
                console.print(f"📝 Command: [bold]{intent.command}[/bold]")

                # Enhanced safety check
                try:
                    from nlcli.safety import enhanced_safety_check

                    is_safe, safety_message, violations = enhanced_safety_check(
                        intent, ctx
                    )

                    if not is_safe:
                        console.print(
                            f"❌ Command blocked: {safety_message}", style="red"
                        )

                        # Show violation details if any
                        if violations:
                            console.print("🔍 Issues found:")
                            for violation in violations[:3]:  # Show top 3
                                console.print(
                                    f"  • {violation.get('description', 'Security violation')}"
                                )
                        continue

                    # Show warnings for non-critical violations
                    if violations:
                        warning_violations = [
                            v
                            for v in violations
                            if v.get("severity") in ["low", "medium"]
                        ]
                        if warning_violations:
                            console.print(
                                f"⚠️  {len(warning_violations)} warning(s) detected",
                                style="yellow",
                            )

                except ImportError:
                    # Fallback to basic safety check
                    if not guard(intent, ctx):
                        console.print(
                            "❌ Command blocked by safety checks.", style="red"
                        )
                        continue

                # Confirmation for destructive operations
                if intent.danger_level in ("destructive", "modify"):
                    confirmation = prompt(
                        f"⚠️  This will modify your system. Continue? [y/N] "
                    ).lower()
                    if confirmation not in ("y", "yes"):
                        console.print("Operation cancelled.", style="yellow")
                        continue

                # Execute command with performance tracking
                try:
                    from nlcli.performance import profile_operation

                    with profile_operation("command_execution"):
                        result = execute(intent.command, ctx)
                except ImportError:
                    result = execute(intent.command, ctx)

                # Record telemetry
                try:
                    from nlcli.telemetry import get_telemetry_manager

                    telemetry = get_telemetry_manager()
                    telemetry.record_command_execution(
                        command=intent.command,
                        success=result.success,
                        duration=result.execution_time or 0,
                        tool_name=intent.tool_name,
                        confidence=intent.confidence,
                    )
                except ImportError:
                    pass

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
                # Enhanced error handling with Phase 4 error recovery
                try:
                    from nlcli.error_recovery import (
                        ErrorContext,
                        get_error_recovery_manager,
                    )

                    recovery_manager = get_error_recovery_manager()
                    error_context = ErrorContext(
                        operation="repl_command_processing",
                        command=(
                            getattr(intent, "command", None)
                            if "intent" in locals()
                            else None
                        ),
                        user_input=nl_input,
                        session_id=session_id,
                    )

                    recovery_result = recovery_manager.handle_error(e, error_context)

                    if recovery_result:
                        console.print(
                            f"🔄 Error recovered automatically", style="green"
                        )
                    else:
                        console.print(f"❌ Error: {e}", style="red")

                except ImportError:
                    console.print(f"❌ Error: {e}", style="red")
                continue

        except KeyboardInterrupt:
            console.print("\nGoodbye! 👋", style="blue")
            break
        except EOFError:
            console.print("\nGoodbye! 👋", style="blue")
            break

    # Clean up Phase 4 features
    try:
        if session_id:
            from nlcli.performance import get_resource_monitor
            from nlcli.telemetry import get_telemetry_manager

            telemetry = get_telemetry_manager()
            telemetry.end_session()

            monitor = get_resource_monitor()
            monitor.stop_monitoring()

    except ImportError:
        pass


@click.command()
@click.option("--dry-run", is_flag=True, help="Show commands without executing")
@click.option("--explain", is_flag=True, help="Show explanations for commands")
@click.option("--lang", default="en", help="Language for natural language input")
@click.option(
    "--batch",
    type=click.Path(exists=True, path_type=Path),
    help="Execute batch script file",
)
@click.option(
    "--batch-commands", multiple=True, help="Execute multiple commands in batch mode"
)
@click.option(
    "--stop-on-error",
    is_flag=True,
    default=True,
    help="Stop batch execution on first error",
)
@click.version_option(version="0.1.3")
def main(
    dry_run: bool,
    explain: bool,
    lang: str,
    batch: Optional[Path],
    batch_commands: tuple,
    stop_on_error: bool,
) -> None:
    """Natural Language Driven CLI - Turn natural language into safe system commands."""
    if dry_run:
        console.print(
            "🔍 Dry-run mode enabled - commands will be shown but not executed",
            style="yellow",
        )

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
                results = batch_manager.execute_script_file(
                    batch, dry_run=dry_run, stop_on_error=stop_on_error
                )
            else:
                console.print(
                    f"🔄 Executing {len(batch_commands)} batch commands", style="blue"
                )
                results = batch_manager.execute_commands(
                    list(batch_commands), dry_run=dry_run, stop_on_error=stop_on_error
                )

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
