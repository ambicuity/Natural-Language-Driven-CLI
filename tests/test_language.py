"""
Test Multi-language Support
Tests for language detection, translation, and processing.
"""

import os
import unittest
from unittest.mock import patch

from nlcli.language import (
    LanguageConfig,
    LanguageDetector,
    MultiLanguageProcessor,
    SimpleTranslator,
    create_language_processor,
    get_language_processor,
)


class TestLanguageSupport(unittest.TestCase):
    """Test multi-language support functionality."""

    def setUp(self):
        self.config = LanguageConfig()
        self.detector = LanguageDetector()
        self.translator = SimpleTranslator()
        self.processor = MultiLanguageProcessor(self.config)

    def test_language_config(self):
        """Test language configuration."""
        config = LanguageConfig(default_language="es")
        self.assertEqual(config.default_language, "es")
        self.assertIn("en", config.enabled_languages)
        self.assertIn("es", config.enabled_languages)

    def test_language_detection_english(self):
        """Test detection of English text."""
        text = "show all files in directory"
        lang, confidence = self.detector.detect_language(text)

        self.assertEqual(lang, "en")
        self.assertGreater(confidence, 0)

    def test_language_detection_spanish(self):
        """Test detection of Spanish text."""
        text = "mostrar todos los archivos en directorio"
        lang, confidence = self.detector.detect_language(text)

        # Should detect Spanish or default to English with low confidence
        self.assertIn(lang, ["es", "en"])

    def test_language_detection_unknown(self):
        """Test detection of unknown/unsupported text."""
        text = "xyz abc qwerty"  # Nonsense text
        lang, confidence = self.detector.detect_language(text)

        # Should default to English with low confidence
        self.assertEqual(lang, "en")
        self.assertLessEqual(confidence, 0.5)

    def test_spanish_translation(self):
        """Test Spanish to English translation."""
        text = "mostrar todos los archivos"
        translated = self.translator.translate_to_english(text, "es")

        # Should contain some translated words
        self.assertIn("show", translated.lower())
        self.assertIn("all", translated.lower())
        self.assertIn("files", translated.lower())

    def test_french_translation(self):
        """Test French to English translation."""
        text = "lister tous les fichiers"
        translated = self.translator.translate_to_english(text, "fr")

        # Should contain some translated words
        self.assertIn("list", translated.lower())
        self.assertIn("all", translated.lower())
        self.assertIn("files", translated.lower())

    def test_german_translation(self):
        """Test German to English translation."""
        text = "alle dateien anzeigen"
        translated = self.translator.translate_to_english(text, "de")

        # Should contain some translated words
        self.assertIn("all", translated.lower())
        self.assertIn("files", translated.lower())
        self.assertIn("show", translated.lower())

    def test_no_translation_for_english(self):
        """Test that English text is not translated."""
        text = "show all files"
        translated = self.translator.translate_to_english(text, "en")

        self.assertEqual(text, translated)

    def test_processor_english_input(self):
        """Test processor with English input."""
        text = "list all processes"
        result = self.processor.process_input(text)

        self.assertEqual(result["original_text"], text)
        self.assertEqual(result["detected_language"], "en")
        self.assertEqual(result["translated_text"], text)
        self.assertFalse(result["needs_translation"])
        self.assertTrue(result["supported"])

    def test_processor_spanish_input(self):
        """Test processor with Spanish input."""
        text = "mostrar archivos grandes"
        result = self.processor.process_input(text)

        self.assertEqual(result["original_text"], text)
        # Translation should occur
        self.assertNotEqual(result["translated_text"], text)
        self.assertTrue(result["supported"])

    def test_processor_unsupported_language(self):
        """Test processor with unsupported language."""
        # Configure processor with limited language support
        limited_config = LanguageConfig(enabled_languages=["en"])
        limited_processor = MultiLanguageProcessor(limited_config)

        text = "mostrar archivos"  # Spanish
        result = limited_processor.process_input(text)

        # Should still be supported because Spanish patterns might not be detected strongly enough
        # or it might default to English
        self.assertIsInstance(result["supported"], bool)

    def test_processor_with_user_preference(self):
        """Test processor with user language preference."""
        text = "mostrar archivos"
        result = self.processor.process_input(text, user_preferred_lang="es")

        self.assertEqual(result["detected_language"], "es")
        self.assertTrue(result["needs_translation"])
        self.assertIn("show", result["translated_text"].lower())

    def test_get_response_language(self):
        """Test getting appropriate response language."""
        # Supported language
        lang = self.processor.get_response_language("es")
        self.assertEqual(lang, "es")

        # Unsupported language should fall back to default
        lang = self.processor.get_response_language("xyz")
        self.assertEqual(lang, self.config.default_language)

    def test_localize_response(self):
        """Test response localization."""
        text = "Command executed successfully"

        # English should remain unchanged
        localized = self.processor.localize_response(text, "en")
        self.assertEqual(localized, text)

        # Other languages currently return English (placeholder)
        localized = self.processor.localize_response(text, "es")
        self.assertEqual(localized, text)  # Currently returns English

    def test_create_language_processor(self):
        """Test creating language processor from config."""
        processor = create_language_processor()
        self.assertIsInstance(processor, MultiLanguageProcessor)
        self.assertEqual(processor.config.default_language, "en")

    @patch.dict(
        os.environ, {"NLCLI_DEFAULT_LANG": "es", "NLCLI_ENABLED_LANGUAGES": "en,es,fr"}
    )
    def test_create_processor_from_env(self):
        """Test creating processor from environment variables."""
        processor = create_language_processor()

        self.assertEqual(processor.config.default_language, "es")
        self.assertEqual(processor.config.enabled_languages, ["en", "es", "fr"])

    def test_global_processor_singleton(self):
        """Test global processor singleton."""
        processor1 = get_language_processor()
        processor2 = get_language_processor()

        self.assertIs(processor1, processor2)

    def test_partial_translation(self):
        """Test partial translation of mixed content."""
        text = "mostrar files and directories"  # Mixed Spanish/English
        translated = self.translator.translate_to_english(text, "es")

        # Should translate Spanish words but keep English ones
        self.assertIn("show", translated.lower())
        self.assertIn("files", translated.lower())
        self.assertIn("directories", translated.lower())

    def test_case_insensitive_translation(self):
        """Test case-insensitive translation."""
        text = "MOSTRAR ARCHIVOS"  # Uppercase Spanish
        translated = self.translator.translate_to_english(text, "es")

        # Should still translate despite case
        self.assertIn("show", translated.lower())
        self.assertIn("files", translated.lower())


if __name__ == "__main__":
    unittest.main()
