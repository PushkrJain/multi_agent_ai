import os
import requests
from typing import Dict, Any
from mid_agents.intent.errors import TranslationAPIError

# Try to attach monitoring
try:
    from mid_agents.monitoring.error_monitor import ErrorMonitor
    monitor = ErrorMonitor()
except Exception:
    monitor = None

class TranslationAgent:
    def __init__(self):
        self.deepl_key = os.getenv('DEEPL_API_KEY')
        if not self.deepl_key or self.deepl_key == "your_api_key_here":
            if monitor:
                monitor.report_error("translation")
            raise TranslationAPIError("DeepL API key missing or not configured.")
        self.timeout = 10
        self.supported_languages = {
            'bulgarian': 'BG', 'bg': 'BG',
            'czech': 'CS', 'cs': 'CS',
            'danish': 'DA', 'da': 'DA',
            'german': 'DE', 'de': 'DE',
            'greek': 'EL', 'el': 'EL',
            'english': 'EN', 'en': 'EN',
            'spanish': 'ES', 'es': 'ES',
            'estonian': 'ET', 'et': 'ET',
            'finnish': 'FI', 'fi': 'FI',
            'french': 'FR', 'fr': 'FR',
            'hungarian': 'HU', 'hu': 'HU',
            'italian': 'IT', 'it': 'IT',
            'japanese': 'JA', 'ja': 'JA',
            'lithuanian': 'LT', 'lt': 'LT',
            'latvian': 'LV', 'lv': 'LV',
            'dutch': 'NL', 'nl': 'NL',
            'polish': 'PL', 'pl': 'PL',
            'portuguese': 'PT', 'pt': 'PT',
            'romanian': 'RO', 'ro': 'RO',
            'russian': 'RU', 'ru': 'RU',
            'slovak': 'SK', 'sk': 'SK',
            'slovenian': 'SL', 'sl': 'SL',
            'swedish': 'SV', 'sv': 'SV',
            'chinese': 'ZH', 'zh': 'ZH'
        }

    def translate_text(self, text: str, target_lang: str, source_lang: str = None) -> Dict[str, Any]:
        try:
            text = text.strip()
            if not text:
                raise TranslationAPIError("Text cannot be empty")
            if len(text) > 5000:
                raise TranslationAPIError("Text too long (max 5000 characters)")

            target_lang = self._normalize_language_code(target_lang)
            if source_lang:
                source_lang = self._normalize_language_code(source_lang)

            return self._call_deepl(text, target_lang, source_lang)

        except TranslationAPIError:
            if monitor: monitor.report_error("translation")
            raise
        except Exception as e:
            if monitor: monitor.report_error("translation")
            raise TranslationAPIError(f"Translation failed: {str(e)}")

    def _call_deepl(self, text: str, target_lang: str, source_lang: str = None) -> Dict[str, Any]:
        params = {
            'auth_key': self.deepl_key,
            'text': text,
            'target_lang': target_lang,
            'preserve_formatting': '1'
        }
        if source_lang:
            params['source_lang'] = source_lang

        try:
            response = requests.post("https://api-free.deepl.com/v2/translate", data=params, timeout=self.timeout)
            data = response.json()

            if response.status_code == 200 and 'translations' in data:
                return {
                    'text': data['translations'][0]['text'],
                    'source_lang': data['translations'][0].get('detected_source_language', source_lang or 'auto'),
                    'target_lang': target_lang,
                    'service': 'DeepL'
                }
            elif response.status_code == 403:
                raise TranslationAPIError("Invalid DeepL API key")
            elif response.status_code == 456:
                raise TranslationAPIError("Translation quota exceeded")
            else:
                error = data.get('message', f"HTTP {response.status_code}")
                raise TranslationAPIError(f"API error: {error}")
        except requests.exceptions.RequestException as e:
            raise TranslationAPIError(f"Connection failed: {str(e)}")

    def _normalize_language_code(self, lang: str) -> str:
        lang = lang.lower().strip()
        if lang in self.supported_languages:
            return self.supported_languages[lang]
        raise TranslationAPIError(f"Unsupported language: {lang}")

    def get_supported_languages(self) -> Dict[str, str]:
        return {k: v for k, v in self.supported_languages.items() if len(k) > 2}
