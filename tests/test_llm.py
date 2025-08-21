"""
Tests for Local LLM integration functionality.
"""

import os
import unittest
from unittest.mock import Mock, patch  # noqa: F401

from nlcli.engine import create_llm_from_config
from nlcli.llm import LLMConfig, LocalLLM, create_llm, default_llm


class TestLocalLLM(unittest.TestCase):
    """Test Local LLM integration."""

    def setUp(self):
        self.config = LLMConfig(enabled=False)
        self.llm = LocalLLM(self.config)

    def test_disabled_llm(self):
        """Test that disabled LLM returns expected responses."""
        self.assertFalse(self.llm.is_available())

        response = self.llm.enhance_intent_understanding("test input", {})
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Neither local nor cloud LLM available")

    def test_enabled_llm_placeholder(self):
        """Test enabled LLM with placeholder functionality."""
        config = LLMConfig(enabled=True)
        _llm = LocalLLM(config)  # noqa: F841

        # Since we don't have actual models, this will still be disabled
        # but the config is marked as enabled
        self.assertTrue(config.enabled)

    def test_create_llm_function(self):
        """Test LLM creation function."""
        llm = create_llm()
        self.assertIsInstance(llm, LocalLLM)
        self.assertFalse(llm.is_available())

    def test_default_llm_instance(self):
        """Test default LLM instance."""
        self.assertIsInstance(default_llm, LocalLLM)
        self.assertFalse(default_llm.is_available())

    @patch.dict(os.environ, {"NLCLI_LLM_ENABLED": "true"})
    def test_create_llm_from_config_enabled(self):
        """Test creating LLM from environment config."""
        llm = create_llm_from_config()
        self.assertTrue(llm.config.enabled)

    @patch.dict(os.environ, {"NLCLI_LLM_ENABLED": "false"})
    def test_create_llm_from_config_disabled(self):
        """Test creating LLM from environment config when disabled."""
        llm = create_llm_from_config()
        self.assertFalse(llm.config.enabled)

    def test_explain_command(self):
        """Test command explanation functionality."""
        explanation = self.llm.explain_command("ls -la", {})
        self.assertIn("ls -la", explanation)
        self.assertTrue(isinstance(explanation, str))


if __name__ == "__main__":
    unittest.main()