"""
Multi-language Support Module
Provides language detection and translation capabilities.
"""
import logging
import os
import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LanguageConfig:
    """Configuration for language support."""
    default_language: str = "en"
    enabled_languages: List[str] = None
    translation_service: str = "local"  # local, google, azure
    api_key: Optional[str] = None
    
    def __post_init__(self):
        if self.enabled_languages is None:
            self.enabled_languages = ["en", "es", "fr", "de", "pt", "it", "zh", "ja", "ko"]


class LanguageDetector:
    """Simple language detection using word patterns and common phrases."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common phrases in different languages for CLI commands
        self.language_patterns = {
            "en": [
                r"\b(show|list|find|search|delete|remove|copy|move|create)\b",
                r"\b(files?|directories?|processes?|containers?)\b",
                r"\b(all|large|small|recent|old)\b"
            ],
            "es": [
                r"\b(mostrar|listar|buscar|encontrar|eliminar|borrar|copiar|mover|crear)\b",
                r"\b(archivos?|directorios?|procesos?|contenedores?)\b",
                r"\b(todos?|grandes?|pequeños?|recientes?|viejos?)\b"
            ],
            "fr": [
                r"\b(montrer|afficher|lister|chercher|trouver|supprimer|copier|déplacer|créer)\b",
                r"\b(fichiers?|répertoires?|processus|conteneurs?)\b",
                r"\b(tous?|toutes?|grands?|petits?|récents?|anciens?)\b"
            ],
            "de": [
                r"\b(zeigen|anzeigen|auflisten|suchen|finden|löschen|kopieren|verschieben|erstellen)\b",
                r"\b(dateien?|verzeichnisse?|prozesse?|container?)\b",
                r"\b(alle?|große?|kleine?|neue?|alte?)\b"
            ],
            "pt": [
                r"\b(mostrar|exibir|listar|buscar|encontrar|deletar|excluir|copiar|mover|criar)\b",
                r"\b(arquivos?|diretórios?|processos?|contêineres?)\b",
                r"\b(todos?|grandes?|pequenos?|recentes?|antigos?)\b"
            ],
            "it": [
                r"\b(mostrare|visualizzare|elencare|cercare|trovare|eliminare|copiare|spostare|creare)\b",
                r"\b(files?|directory|processi|contenitori?)\b",
                r"\b(tutti?|grandi?|piccoli?|recenti?|vecchi?)\b"
            ]
        }
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of input text.
        Returns (language_code, confidence)
        """
        text_lower = text.lower()
        scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > 0:
                scores[lang] = score / len(patterns)
        
        if not scores:
            return "en", 0.1  # Default to English with low confidence
        
        best_lang = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[best_lang] / len(text.split()) * 100
        confidence = min(confidence, 1.0)  # Cap at 1.0
        
        return best_lang, confidence


class SimpleTranslator:
    """Simple translation service using lookup tables for common CLI phrases."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Translation dictionaries for common CLI terms
        self.translations = {
            "es": {
                "mostrar": "show", "listar": "list", "buscar": "find", "encontrar": "find",
                "eliminar": "delete", "borrar": "delete", "copiar": "copy", "mover": "move",
                "crear": "create", "archivos": "files", "archivo": "file",
                "directorios": "directories", "directorio": "directory",
                "procesos": "processes", "proceso": "process",
                "contenedores": "containers", "contenedor": "container",
                "todos": "all", "todas": "all", "grandes": "large", "pequeños": "small",
                "recientes": "recent", "viejos": "old", "nuevo": "new", "antigua": "old"
            },
            "fr": {
                "montrer": "show", "afficher": "show", "lister": "list",
                "chercher": "find", "trouver": "find", "supprimer": "delete",
                "copier": "copy", "déplacer": "move", "créer": "create",
                "fichiers": "files", "fichier": "file",
                "répertoires": "directories", "répertoire": "directory",
                "processus": "processes", "conteneurs": "containers",
                "conteneur": "container", "tous": "all", "toutes": "all",
                "grands": "large", "petits": "small", "récents": "recent",
                "anciens": "old", "nouveau": "new", "ancienne": "old"
            },
            "de": {
                "zeigen": "show", "anzeigen": "show", "auflisten": "list",
                "suchen": "find", "finden": "find", "löschen": "delete",
                "kopieren": "copy", "verschieben": "move", "erstellen": "create",
                "dateien": "files", "datei": "file",
                "verzeichnisse": "directories", "verzeichnis": "directory",
                "prozesse": "processes", "prozess": "process",
                "container": "containers", "alle": "all",
                "große": "large", "kleine": "small", "neue": "recent",
                "alte": "old", "neu": "new", "alt": "old"
            },
            "pt": {
                "mostrar": "show", "exibir": "show", "listar": "list",
                "buscar": "find", "encontrar": "find", "deletar": "delete",
                "excluir": "delete", "copiar": "copy", "mover": "move",
                "criar": "create", "arquivos": "files", "arquivo": "file",
                "diretórios": "directories", "diretório": "directory",
                "processos": "processes", "processo": "process",
                "contêineres": "containers", "contêiner": "container",
                "todos": "all", "grandes": "large", "pequenos": "small",
                "recentes": "recent", "antigos": "old", "novo": "new"
            },
            "it": {
                "mostrare": "show", "visualizzare": "show", "elencare": "list",
                "cercare": "find", "trovare": "find", "eliminare": "delete",
                "copiare": "copy", "spostare": "move", "creare": "create",
                "files": "files", "file": "file", "directory": "directories",
                "processi": "processes", "processo": "process",
                "contenitori": "containers", "contenitore": "container",
                "tutti": "all", "grandi": "large", "piccoli": "small",
                "recenti": "recent", "vecchi": "old", "nuovo": "new"
            }
        }
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate text from source language to English."""
        if source_lang == "en" or source_lang not in self.translations:
            return text
        
        words = text.lower().split()
        translated_words = []
        
        translation_dict = self.translations[source_lang]
        
        for word in words:
            # Remove punctuation for lookup
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in translation_dict:
                translated_words.append(translation_dict[clean_word])
            else:
                translated_words.append(word)  # Keep original if no translation
        
        return " ".join(translated_words)


class MultiLanguageProcessor:
    """Main processor for multi-language support."""
    
    def __init__(self, config: Optional[LanguageConfig] = None):
        self.config = config or LanguageConfig()
        self.detector = LanguageDetector()
        self.translator = SimpleTranslator()
        self.logger = logging.getLogger(__name__)
    
    def process_input(self, text: str, user_preferred_lang: Optional[str] = None) -> Dict[str, any]:
        """
        Process multi-language input.
        Returns dict with original text, detected language, translated text, etc.
        """
        result = {
            "original_text": text,
            "detected_language": "en",
            "confidence": 1.0,
            "translated_text": text,
            "needs_translation": False,
            "supported": True
        }
        
        # If user has specified language preference, use it
        if user_preferred_lang and user_preferred_lang in self.config.enabled_languages:
            detected_lang = user_preferred_lang
            confidence = 1.0
        else:
            # Detect language
            detected_lang, confidence = self.detector.detect_language(text)
        
        result["detected_language"] = detected_lang
        result["confidence"] = confidence
        
        # Check if language is supported
        if detected_lang not in self.config.enabled_languages:
            result["supported"] = False
            self.logger.warning(f"Unsupported language detected: {detected_lang}")
            return result
        
        # Translate if not English
        if detected_lang != "en":
            translated_text = self.translator.translate_to_english(text, detected_lang)
            result["translated_text"] = translated_text
            result["needs_translation"] = True
            
            self.logger.info(f"Translated '{text}' from {detected_lang} to '{translated_text}'")
        
        return result
    
    def get_response_language(self, user_lang: str) -> str:
        """Get appropriate language for responses."""
        if user_lang in self.config.enabled_languages:
            return user_lang
        return self.config.default_language
    
    def localize_response(self, text: str, target_lang: str) -> str:
        """Localize response text to target language."""
        if target_lang == "en":
            return text
        
        # For now, keep responses in English
        # In a full implementation, this would translate responses back
        return text


def create_language_processor() -> MultiLanguageProcessor:
    """Create language processor from configuration."""
    config = LanguageConfig()
    
    # Load from environment variables
    if "NLCLI_DEFAULT_LANG" in os.environ:
        config.default_language = os.environ["NLCLI_DEFAULT_LANG"]
    
    if "NLCLI_ENABLED_LANGUAGES" in os.environ:
        config.enabled_languages = os.environ["NLCLI_ENABLED_LANGUAGES"].split(",")
    
    return MultiLanguageProcessor(config)


# Global processor instance
_language_processor: Optional[MultiLanguageProcessor] = None


def get_language_processor() -> MultiLanguageProcessor:
    """Get the global language processor instance."""
    global _language_processor
    if _language_processor is None:
        _language_processor = create_language_processor()
    return _language_processor