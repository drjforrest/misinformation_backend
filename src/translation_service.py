#!/usr/bin/env python3
"""
Translation service for multilingual health misinformation detection
Supports multiple translation backends with caching and fallback mechanisms
"""

import json
import hashlib
from typing import Dict, Optional, List
from pathlib import Path
import time
from loguru import logger

# Translation backends - using deep-translator which is more reliable
# Note: googletrans 4.0+ has async issues, so we'll use deep-translator instead
GOOGLE_AVAILABLE = False  # Disabled due to async compatibility issues

try:
    from deep_translator import GoogleTranslator as DeepGoogleTranslator
    from deep_translator import MyMemoryTranslator

    # Remove LibreTranslator to avoid potential issues

    DEEP_TRANSLATOR_AVAILABLE = True
    logger.info("Deep-translator backends loaded successfully")
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    logger.warning("Deep-translator not available")


class TranslationCache:
    """Simple file-based cache for translations to avoid repeated API calls"""

    def __init__(self, cache_dir: str = "data/translation_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "translations.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load existing cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load translation cache: {e}")
        return {}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save translation cache: {e}")

    def _generate_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key from text and language pair"""
        content = f"{text}:{source_lang}:{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Get cached translation"""
        key = self._generate_key(text, source_lang, target_lang)
        return self.cache.get(key)

    def set(self, text: str, source_lang: str, target_lang: str, translation: str):
        """Cache a translation"""
        key = self._generate_key(text, source_lang, target_lang)
        self.cache[key] = {
            "translation": translation,
            "timestamp": time.time(),
            "source_lang": source_lang,
            "target_lang": target_lang,
        }

        # Save every 10 new translations to avoid excessive I/O
        if len(self.cache) % 10 == 0:
            self._save_cache()


class TranslationService:
    """
    Multilingual translation service with multiple backends and caching
    """

    # Target languages based on product requirements
    # Note: Using backend-compatible language codes
    TARGET_LANGUAGES = {
        "en": "English",
        "tl": "Tagalog",  # Compatible with both backends
        "zh-CN": "Chinese (Simplified)",  # Use specific code for compatibility
        "zh-TW": "Chinese (Traditional)",
        "pa": "Punjabi",
        "es": "Spanish",
        "fr": "French",  # Canadian French
    }

    def __init__(self, cache_enabled: bool = True):
        self.cache = TranslationCache() if cache_enabled else None
        self.google_translator = None
        self.deep_translators = {}

        # Initialize translation backends
        self._initialize_backends()

        logger.info(
            f"Translation service initialized with {len(self._get_available_backends())} backends"
        )

    def _initialize_backends(self):
        """Initialize available translation backends"""

        # Google Translate (googletrans)
        if GOOGLE_AVAILABLE:
            try:
                self.google_translator = GoogleTranslator()
                logger.info("Google Translate (googletrans) initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Google Translate: {e}")

        # Deep Translator backends
        if DEEP_TRANSLATOR_AVAILABLE:
            try:
                # Google via deep-translator (often more reliable)
                self.deep_translators["google"] = DeepGoogleTranslator
                logger.info("Deep Translator (Google) initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Deep Google Translator: {e}")

            try:
                # MyMemory translator (free, no API key needed)
                self.deep_translators["mymemory"] = MyMemoryTranslator
                logger.info("MyMemory Translator initialized")
            except Exception as e:
                logger.warning(f"Could not initialize MyMemory Translator: {e}")

    def _get_available_backends(self) -> List[str]:
        """Get list of available translation backends"""
        backends = []
        if self.google_translator:
            backends.append("googletrans")
        backends.extend(self.deep_translators.keys())
        return backends

    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        Falls back to 'unknown' if detection fails
        """
        if not text or len(text.strip()) < 10:
            return "unknown"

        # Use langdetect directly - more reliable than google translator for this purpose
        try:
            from langdetect import detect

            detected = detect(text)

            # Map langdetect codes to our standard codes
            if detected == "zh-cn":
                return "zh-CN"
            elif detected == "zh-tw":
                return "zh-TW"

            return detected
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "unknown"

    def translate_text(
        self, text: str, target_lang: str = "en", source_lang: str = "auto"
    ) -> Dict:
        """
        Translate text with fallback across multiple backends

        Returns:
            Dict with 'translation', 'source_lang', 'target_lang', 'backend_used', 'confidence'
        """
        if not text or not text.strip():
            return {
                "translation": text,
                "source_lang": "unknown",
                "target_lang": target_lang,
                "backend_used": "none",
                "confidence": 0.0,
                "error": "Empty text",
            }

        # Check cache first
        if self.cache and source_lang != "auto":
            cached = self.cache.get(text, source_lang, target_lang)
            if cached:
                return {
                    "translation": cached["translation"],
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "backend_used": "cache",
                    "confidence": 1.0,
                }

        # Detect source language if needed
        if source_lang == "auto":
            source_lang = self.detect_language(text)
            if source_lang == "unknown":
                return {
                    "translation": text,
                    "source_lang": "unknown",
                    "target_lang": target_lang,
                    "backend_used": "none",
                    "confidence": 0.0,
                    "error": "Could not detect language",
                }

        # Skip translation if source and target are the same
        if source_lang == target_lang:
            return {
                "translation": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "backend_used": "passthrough",
                "confidence": 1.0,
            }

        # Try translation backends in order of preference
        backends_to_try = [
            ("deep_google", self._translate_deep_google),
            ("mymemory", self._translate_mymemory),
        ]

        for backend_name, translate_func in backends_to_try:
            try:
                result = translate_func(text, source_lang, target_lang)
                if result and result.get("translation"):
                    # Cache successful translation
                    if self.cache:
                        self.cache.set(
                            text, source_lang, target_lang, result["translation"]
                        )

                    result["backend_used"] = backend_name
                    return result

            except Exception as e:
                logger.warning(f"Translation failed with {backend_name}: {e}")
                continue

        # All backends failed
        return {
            "translation": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "backend_used": "failed",
            "confidence": 0.0,
            "error": "All translation backends failed",
        }

    def _translate_googletrans(
        self, text: str, source_lang: str, target_lang: str
    ) -> Dict:
        """Translate using googletrans library"""
        if not self.google_translator:
            raise Exception("Google Translate not available")

        # Handle both sync and async versions of googletrans
        try:
            result = self.google_translator.translate(
                text, src=source_lang, dest=target_lang
            )

            # Check if result is a coroutine (async version)
            if hasattr(result, "__await__"):
                # Skip googletrans for now if it's async - fallback to other backends
                raise Exception(
                    "googletrans 4.0+ requires async handling - using fallback"
                )

            return {
                "translation": result.text,
                "source_lang": result.src,
                "target_lang": target_lang,
                "confidence": getattr(result, "confidence", 0.8),  # Estimate confidence
            }
        except Exception as e:
            # Log the specific error for debugging but re-raise to let fallback handle it
            logger.debug(f"GoogleTrans error: {e}")
            raise

    def _translate_deep_google(
        self, text: str, source_lang: str, target_lang: str
    ) -> Dict:
        """Translate using deep-translator Google backend"""
        if "google" not in self.deep_translators:
            raise Exception("Deep Google Translator not available")

        translator = self.deep_translators["google"](
            source=source_lang, target=target_lang
        )
        translation = translator.translate(text)

        return {
            "translation": translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "confidence": 0.8,  # Estimate confidence
        }

    def _translate_mymemory(
        self, text: str, source_lang: str, target_lang: str
    ) -> Dict:
        """Translate using MyMemory backend"""
        if "mymemory" not in self.deep_translators:
            raise Exception("MyMemory Translator not available")

        translator = self.deep_translators["mymemory"](
            source=source_lang, target=target_lang
        )
        translation = translator.translate(text)

        return {
            "translation": translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "confidence": 0.7,  # MyMemory tends to be less reliable
        }

    def translate_health_keywords(self) -> Dict[str, Dict[str, str]]:
        """
        Translate health keywords to all target languages
        Returns nested dict: {language: {english_keyword: translated_keyword}}
        """
        from config.settings import ResearchConfig

        # Core health keywords from research config
        keywords = ResearchConfig.PRIMARY_KEYWORDS + ResearchConfig.COLLOQUIAL_TERMS

        translations = {}

        for lang_code, lang_name in self.TARGET_LANGUAGES.items():
            if lang_code == "en":  # Skip English
                continue

            logger.info(f"Translating keywords to {lang_name}...")
            translations[lang_code] = {}

            for keyword in keywords:
                try:
                    result = self.translate_text(
                        keyword, target_lang=lang_code, source_lang="en"
                    )
                    if result.get("translation") and not result.get("error"):
                        translations[lang_code][keyword] = result["translation"]
                        logger.debug(f"  {keyword} -> {result['translation']}")
                    else:
                        logger.warning(
                            f"  Failed to translate '{keyword}' to {lang_name}"
                        )
                        translations[lang_code][
                            keyword
                        ] = keyword  # Fallback to English

                    # Rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error translating '{keyword}' to {lang_name}: {e}")
                    translations[lang_code][keyword] = keyword  # Fallback

        # Save translations to file
        translation_file = Path("data/health_keywords_translations.json")
        translation_file.parent.mkdir(parents=True, exist_ok=True)

        with open(translation_file, "w", encoding="utf-8") as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)

        logger.info(f"Health keyword translations saved to {translation_file}")
        return translations

    def get_health_keywords_multilingual(self) -> List[str]:
        """
        Get all health keywords in all languages
        Returns a flat list of keywords for matching
        """
        keywords = []

        # Start with English keywords
        from config.settings import ResearchConfig

        keywords.extend(ResearchConfig.PRIMARY_KEYWORDS)
        keywords.extend(ResearchConfig.COLLOQUIAL_TERMS)

        # Load translated keywords if available
        translation_file = Path("data/health_keywords_translations.json")
        if translation_file.exists():
            try:
                with open(translation_file, "r", encoding="utf-8") as f:
                    translations = json.load(f)

                for lang_translations in translations.values():
                    keywords.extend(lang_translations.values())

            except Exception as e:
                logger.warning(f"Could not load translated keywords: {e}")

        # Remove duplicates and return
        return list(set(keywords))

    def close(self):
        """Clean up and save cache"""
        if self.cache:
            self.cache._save_cache()
            logger.info("Translation cache saved")


# Global translation service instance
_translation_service = None


def get_translation_service() -> TranslationService:
    """Get global translation service instance"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


# Convenience functions
def translate_to_english(text: str, source_lang: str = "auto") -> str:
    """Quick function to translate any text to English"""
    service = get_translation_service()
    result = service.translate_text(text, target_lang="en", source_lang=source_lang)
    return result.get("translation", text)


def detect_language(text: str) -> str:
    """Quick function to detect language"""
    service = get_translation_service()
    return service.detect_language(text)


if __name__ == "__main__":
    # Test the translation service
    print("🌐 Testing Translation Service")
    print("=" * 40)

    service = TranslationService()

    # Test language detection
    test_texts = [
        "Hello, I'm new to Canada and need health information",
        "Hola, soy nuevo en Canadá y necesito información de salud",
        "你好，我是加拿大新移民，需要健康信息",
        "Kamusta, bago ako sa Canada at kailangan ko ng health information",
    ]

    for text in test_texts:
        lang = service.detect_language(text)
        translation = service.translate_text(text, target_lang="en")
        print(f"Text: {text}")
        print(f"Language: {lang}")
        print(f"Translation: {translation['translation']}")
        print(f"Backend: {translation['backend_used']}")
        print()

    # Test keyword translation
    print("🔑 Translating health keywords...")
    translations = service.translate_health_keywords()

    print(f"✅ Translated keywords to {len(translations)} languages")
    for lang, trans in translations.items():
        print(f"{lang}: {len(trans)} keywords")

    service.close()
