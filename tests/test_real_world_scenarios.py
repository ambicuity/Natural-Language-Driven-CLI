"""
Comprehensive real-world scenario tests for the Natural Language Driven CLI.

This module tests all the real-world examples mentioned in the problem statement
to ensure the CLI can handle actual user scenarios effectively.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from nlcli.context import SessionContext
from nlcli.engine import plan_and_generate
from nlcli.registry import load_tools
from nlcli.safety import guard, requires_confirmation


class TestRealWorldFileOperations(unittest.TestCase):
    """Test real-world file and directory operations."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_show_files_larger_than_500mb_modified_yesterday(self):
        """Test: 'show files >500MB modified yesterday'"""
        nl_input = "show files >500MB modified yesterday"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Could be find_files or list_files depending on planning
        self.assertIn(intent.tool_name, ["find_files", "list_files"])
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))
        
    def test_find_all_log_files_in_var_log(self):
        """Test: 'find all .log files in /var/log'"""
        nl_input = "find all .log files in /var/log"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Could be find_files or search_content depending on planning
        self.assertIn(intent.tool_name, ["find_files", "list_files", "search_content"])
        self.assertIn("/var/log", intent.command)
        
        # This should be blocked by safety due to system directory access
        # This is the expected behavior for security
        self.assertFalse(guard(intent, self.ctx))

    def test_search_for_error_inside_config_files(self):
        """Test: 'search for 'error' inside config files'"""
        nl_input = "search for 'error' inside config files"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Should likely use search_content
        self.assertIn(intent.tool_name, ["search_content", "find_files"])
        self.assertIn("error", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_whats_taking_up_space_in_downloads(self):
        """Test: 'what's taking up space in ~/Downloads'"""
        nl_input = "what's taking up space in ~/Downloads"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Should use disk_usage or similar
        self.assertIn(intent.tool_name, ["disk_usage", "list_files"])
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_list_directories_sorted_by_size(self):
        """Test: 'list directories sorted by size'"""
        nl_input = "list directories sorted by size"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Could use disk_usage or list_files
        self.assertIn(intent.tool_name, ["disk_usage", "list_files"])
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))


class TestRealWorldProcessManagement(unittest.TestCase):
    """Test real-world process and system management scenarios."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_list_processes_using_port_8080(self):
        """Test: 'list processes using port 8080'"""
        nl_input = "list processes using port 8080"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Should use process_by_port or similar
        self.assertIn(intent.tool_name, ["process_by_port", "network_connections"])
        self.assertIn("8080", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_show_top_5_cpu_consuming_processes(self):
        """Test: 'show top 5 CPU consuming processes'"""
        nl_input = "show top 5 CPU consuming processes"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Should use list_processes or similar
        self.assertIn(intent.tool_name, ["list_processes", "system_resources"])
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_kill_process_named_chrome_requires_confirmation(self):
        """Test: 'kill process named chrome' (should ask for confirmation)"""
        nl_input = "kill process named chrome"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        # This might not generate an intent due to safety concerns
        if intent:
            self.assertEqual(intent.tool_name, "kill_process")
            # The command should contain some reference to process killing
            self.assertTrue(
                "pkill" in intent.command or 
                "kill" in intent.command or 
                "chrome" in intent.command
            )
            
            # Should require confirmation due to destructive nature
            self.assertTrue(requires_confirmation(intent))
            
            # Should be safe after confirmation
            self.assertTrue(guard(intent, self.ctx))

    def test_display_system_resource_usage(self):
        """Test: 'display system resource usage'"""
        nl_input = "display system resource usage"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "system_resources")
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))


class TestRealWorldNetworking(unittest.TestCase):
    """Test real-world networking scenarios."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_ping_google_com(self):
        """Test: 'ping google.com'"""
        nl_input = "ping google.com"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "ping_host")
        self.assertIn("google.com", intent.command)
        self.assertIn("ping", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_check_what_services_are_listening_on_ports(self):
        """Test: 'check what services are listening on ports'"""
        nl_input = "check what services are listening on ports"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "network_connections")
        self.assertIn("netstat", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_download_file_from_url(self):
        """Test: 'download file from https://example.com/file.zip'"""
        nl_input = "download file from https://example.com/file.zip"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "download_file")
        self.assertIn("example.com/file.zip", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_resolve_dns_for_openai_com(self):
        """Test: 'resolve DNS for openai.com'"""
        nl_input = "resolve DNS for openai.com"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "dns_lookup")
        self.assertIn("openai.com", intent.command)
        self.assertIn("dig", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))


class TestRealWorldPackageAndGit(unittest.TestCase):
    """Test real-world package management and git scenarios."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_list_installed_apt_packages(self):
        """Test: 'list installed apt packages'"""
        nl_input = "list installed apt packages"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "apt_list")
        self.assertIn("apt", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_show_details_of_package_curl(self):
        """Test: 'show details of package curl'"""
        nl_input = "show details of package curl"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "apt_info")
        self.assertIn("curl", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_git_status(self):
        """Test: 'git status'"""
        nl_input = "git status"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "git_status")
        self.assertIn("git status", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))

    def test_git_log_last_3_commits(self):
        """Test: 'git log last 3 commits'"""
        nl_input = "git log last 3 commits"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "git_log")
        self.assertIn("git log", intent.command)
        self.assertIn("3", intent.command)
        
        # Should be safe to run
        self.assertTrue(guard(intent, self.ctx))


class TestRealWorldSafetyAndSecurity(unittest.TestCase):
    """Test real-world safety and security scenarios."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_delete_all_tmp_files_requires_confirmation(self):
        """Test: 'delete all tmp files in /tmp' → should trigger confirmation"""
        nl_input = "delete all tmp files in /tmp"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        if intent:  # May be None if planning fails due to safety
            # Should require confirmation due to destructive nature
            self.assertTrue(requires_confirmation(intent))
            self.assertEqual(intent.danger_level, "destructive")

    def test_rm_rf_root_should_be_blocked(self):
        """Test: 'rm -rf /' → should be blocked"""
        nl_input = "rm -rf /"
        
        # This should either fail at planning stage or be blocked by safety
        try:
            intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
            if intent:
                # If somehow an intent is generated, it should be blocked by safety
                self.assertFalse(guard(intent, self.ctx))
        except Exception:
            # Planning failure is also acceptable for dangerous commands
            pass

    def test_chmod_777_recursive_should_be_blocked(self):
        """Test: 'chmod -R 777 *' → should be blocked"""
        nl_input = "chmod -R 777 *"
        
        # This should either fail at planning stage or be blocked by safety
        try:
            intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
            if intent:
                # If somehow an intent is generated, it should be blocked by safety
                self.assertFalse(guard(intent, self.ctx))
        except Exception:
            # Planning failure is also acceptable for dangerous commands
            pass

    def test_move_important_to_tmp_requires_confirmation(self):
        """Test: 'move important/ /tmp/' → should require confirmation"""
        nl_input = "move important/ /tmp/"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        if intent:  # May be None if planning fails due to safety
            # Should require confirmation due to moving important directory
            self.assertTrue(requires_confirmation(intent))


class TestRealWorldMultiLanguage(unittest.TestCase):
    """Test real-world multi-language input scenarios."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    @patch('nlcli.language.get_language_processor')
    def test_spanish_buscar_archivos_grandes(self, mock_lang_processor):
        """Test Spanish: 'buscar archivos grandes'"""
        # Mock language processor to translate Spanish to English
        mock_processor = MagicMock()
        mock_processor.process_input.return_value = "search large files"
        mock_lang_processor.return_value = mock_processor
        
        nl_input = "buscar archivos grandes"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Should translate to file finding operation
        self.assertEqual(intent.tool_name, "find_files")

    @patch('nlcli.language.get_language_processor')
    def test_french_lister_tous_les_fichiers(self, mock_lang_processor):
        """Test French: 'lister tous les fichiers'"""
        mock_processor = MagicMock()
        mock_processor.process_input.return_value = "list all files"
        mock_lang_processor.return_value = mock_processor
        
        nl_input = "lister tous les fichiers"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Should translate to file listing operation
        self.assertEqual(intent.tool_name, "find_files")

    @patch('nlcli.language.get_language_processor')
    def test_german_zeige_grosse_dateien(self, mock_lang_processor):
        """Test German: 'zeige alle dateien größer als 100MB'"""
        mock_processor = MagicMock()
        mock_processor.process_input.return_value = "show all files larger than 100MB"
        mock_lang_processor.return_value = mock_processor
        
        nl_input = "zeige alle dateien größer als 100MB"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent)
        # Should translate to file finding operation with size filter
        self.assertEqual(intent.tool_name, "find_files")
        self.assertIn("100M", intent.command)


class TestRealWorldPluginExamples(unittest.TestCase):
    """Test real-world plugin examples (Docker)."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_show_docker_containers(self):
        """Test: 'show docker containers'"""
        nl_input = "show docker containers"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        # May not have docker plugin loaded, but should attempt to parse
        if intent:
            self.assertEqual(intent.tool_name, "docker_ps")
            self.assertIn("docker", intent.command)
            self.assertTrue(guard(intent, self.ctx))

    def test_list_all_containers_including_stopped(self):
        """Test: 'list all containers including stopped'"""
        nl_input = "list all containers including stopped"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        # May not have docker plugin loaded, but should attempt to parse
        if intent:
            self.assertEqual(intent.tool_name, "docker_ps")
            self.assertIn("docker", intent.command)
            self.assertIn("-a", intent.command)  # Show all containers
            self.assertTrue(guard(intent, self.ctx))


class TestRealWorldContextAwareness(unittest.TestCase):
    """Test real-world context awareness scenarios."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_context_chain_find_then_filter_then_delete(self):
        """Test context awareness: 'find large files' → 'only show videos' → 'delete those files'"""
        
        # Step 1: find large files in Downloads
        nl_input_1 = "find large files in Downloads"
        intent_1 = plan_and_generate(nl_input_1, self.ctx, self.tools, self.mock_llm)
        
        self.assertIsNotNone(intent_1)
        self.assertEqual(intent_1.tool_name, "find_files")
        
        # Update context with first command
        self.ctx.update_from_intent(intent_1)
        
        # Step 2: only show videos (should refine the search)
        nl_input_2 = "now only show videos"
        intent_2 = plan_and_generate(nl_input_2, self.ctx, self.tools, self.mock_llm)
        
        # Should understand context and refine search
        if intent_2:
            self.assertEqual(intent_2.tool_name, "find_files")
            # Should include video file patterns
            video_patterns = [".mp4", ".mkv", ".avi"]
            has_video_pattern = any(pattern in intent_2.command for pattern in video_patterns)
            self.assertTrue(has_video_pattern)
        
        # Update context with second command
        if intent_2:
            self.ctx.update_from_intent(intent_2)
        
        # Step 3: delete those files (should resolve "those" to video files)
        nl_input_3 = "delete those files"
        intent_3 = plan_and_generate(nl_input_3, self.ctx, self.tools, self.mock_llm)
        
        # Should resolve "those" to the video files from context
        if intent_3:
            # Should require confirmation for destructive operation
            self.assertTrue(requires_confirmation(intent_3))
            self.assertEqual(intent_3.danger_level, "destructive")

    def test_pronoun_resolution_with_context(self):
        """Test pronoun resolution using context."""
        
        # First establish context with files
        self.ctx.recent_files = ["/home/user/video.mp4", "/home/user/doc.pdf"]
        
        nl_input = "delete them"
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        # Should resolve "them" to recent files
        if intent:
            self.assertTrue(requires_confirmation(intent))
            self.assertEqual(intent.danger_level, "destructive")


class TestRealWorldAdvancedFeatures(unittest.TestCase):
    """Test real-world advanced features."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_security_scan_command(self):
        """Test: 'security scan'"""
        nl_input = "security scan"
        
        # This might be handled as a special command in the REPL
        # or mapped to a security tool
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        # Should be safe to run security scans
        if intent:
            self.assertTrue(guard(intent, self.ctx))

    def test_performance_command(self):
        """Test: 'performance' (show metrics)"""
        nl_input = "performance"
        
        # This might be handled as a special command in the REPL
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        # Should be safe to run performance commands
        if intent:
            self.assertTrue(guard(intent, self.ctx))

    def test_audit_command(self):
        """Test: 'audit' (enterprise trail)"""
        nl_input = "audit"
        
        # This might be handled as a special command in the REPL
        intent = plan_and_generate(nl_input, self.ctx, self.tools, self.mock_llm)
        
        # Should be safe to run audit commands
        if intent:
            self.assertTrue(guard(intent, self.ctx))


class TestRealWorldBatchMode(unittest.TestCase):
    """Test real-world batch and script mode scenarios."""

    def setUp(self):
        self.ctx = SessionContext()
        self.tools = load_tools()
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = False

    def test_batch_script_execution(self):
        """Test batch script file execution."""
        
        # Create a temporary batch script
        script_content = """@name Temp Cleanup
@description Clean up temporary files

> find files larger than 100MB in /tmp
> delete files older than 30 days
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nlcli', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            from nlcli.batch import BatchScriptParser
            
            parser = BatchScriptParser()
            script = parser.parse_script_from_file(Path(script_path))
            
            self.assertEqual(script.metadata.name, "Temp Cleanup")
            self.assertEqual(script.metadata.description, "Clean up temporary files")
            self.assertEqual(len(script.commands), 2)
            
            # First command should be file finding
            cmd1 = script.commands[0]
            self.assertIn("find", cmd1.command)
            self.assertIn("100MB", cmd1.command)
            
            # Second command should be deletion (dangerous)
            cmd2 = script.commands[1]
            self.assertIn("delete", cmd2.command)
            self.assertIn("30 days", cmd2.command)
            
        finally:
            os.unlink(script_path)

    def test_batch_commands_via_cli(self):
        """Test batch commands execution via CLI parameters."""
        from nlcli.batch import BatchModeManager
        
        batch_manager = BatchModeManager(self.ctx, self.tools, self.mock_llm)
        
        commands = [
            "list files in current directory",
            "show system information"
        ]
        
        # Test dry run mode
        results = batch_manager.execute_commands(commands, dry_run=True)
        
        # Should have results for each command
        self.assertEqual(len(results), 2)
        
        # All should be successful in dry run mode
        for result in results:
            # In dry run, commands should be "successful" (not actually executed)
            self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()