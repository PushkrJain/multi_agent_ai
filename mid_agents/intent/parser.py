import re
from enum import Enum
from typing import Dict, Any
from .errors import IntentParseError, SecurityViolationError
from task_agents.translation import TranslationAgent

class UrgencyLevel(Enum):
    NORMAL = 0
    ELEVATED = 1
    CRITICAL = 2

class IntentParser:
    def __init__(self):
        self.country_map = {
            'india': 'New Delhi',
            'usa': 'New York',
            'uk': 'London',
            'france': 'Paris',
            'germany': 'Berlin',
            'italy': 'Rome',
            'japan': 'Tokyo',
            'australia': 'Sydney'
        }
        self.sensitive_phrases = ["drop table", "sudo", "rm -rf", "password"]
        self.banned_content = [
            "porn", "masturbate", "sex", "nude", "nsfw", "xxx", "adult"
        ]
        self.translator = TranslationAgent()
        self.news_categories = [
            'business', 'technology', 'sports', 
            'entertainment', 'health', 'science'
        ]

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse user input with comprehensive intent detection"""
        text = text.strip()
        if not text:
            raise IntentParseError("Please enter a query")

        # Security checks
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in self.sensitive_phrases):
            raise SecurityViolationError("Potential malicious input detected")
        if any(phrase in text_lower for phrase in self.banned_content):
            raise SecurityViolationError("Content violates acceptable use policy")

        # Normalize and detect intent
        if self._is_weather_query(text_lower):
            return self._parse_weather_intent(text)
        elif self._is_news_query(text_lower):
            return self._parse_news_intent(text)
        elif self._is_translation_query(text_lower):
            return self._parse_translation_intent(text)
        
        raise IntentParseError(
            "Could not determine intent. Try:\n"
            "- 'weather in London'\n"
            "- 'technology news'\n"
            "- 'translate hello to french'"
        )

    # ... [rest of the existing methods remain the same] ...
    def _is_weather_query(self, text: str) -> bool:
        weather_keywords = {'weather', 'temperature', 'forecast', 'humid', 'wind'}
        return any(keyword in text for keyword in weather_keywords)

    def _is_news_query(self, text: str) -> bool:
        news_keywords = {'news', 'headline', 'update', 'current event'}
        category_keywords = {'business', 'tech', 'sport', 'entertain', 'health'}
        return (any(keyword in text for keyword in news_keywords) or
                any(category in text for category in category_keywords))

    def _is_translation_query(self, text: str) -> bool:
        translate_keywords = {'translate', 'translation', 'how to say', 'in english'}
        return (any(keyword in text for keyword in translate_keywords) or
                ('how' in text and 'say' in text and 'in' in text))

    def _parse_weather_intent(self, text: str) -> Dict[str, Any]:
        """Extract location from weather queries"""
        patterns = [
            r'(?:weather|temperature|forecast).*?(?:in|for|at|of)\s+([^\?]+)',
            r'(.+?)\s+(?:weather|temperature|forecast)'
        ]
        
        location = None
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                location = match.group(1).strip()
                break

        if not location:
            raise IntentParseError("Please specify a location (e.g. 'London weather')")

        # Clean location and map countries
        location = re.sub(r'[^\w\s]', '', location).strip()
        if len(location) < 2:
            raise IntentParseError("Location name too short")
        
        location = self.country_map.get(location.lower(), location)
        
        return {
            'intent': 'weather',
            'target': ' '.join(word.capitalize() for word in location.split()),
            'urgency': UrgencyLevel.NORMAL.name
        }

    def _parse_news_intent(self, text: str) -> Dict[str, Any]:
        """Extract query, category and country from news requests"""
        query = None
        category = None
        country = None
        
        # Extract potential country first
        for country_name in self.country_map:
            if country_name in text.lower():
                country = country_name
                text = text.replace(country_name, '').strip()
                break
        
        # Then look for category
        for cat in self.news_categories:
            if cat in text.lower():
                category = cat
                break
                
        # Remaining text is treated as query
        query = text.strip() if text.strip() else None
                
        return {
            'intent': 'news',
            'query': query,
            'category': category,
            'country': country,
            'urgency': UrgencyLevel.NORMAL.name
        }

    def _parse_translation_intent(self, text: str) -> Dict[str, Any]:
        """Extract text and target language for translation"""
        patterns = [
            r'translate\s+"?(?P<text>.+?)"?\s+(?:to|into)\s+(?P<target>\w+)',
            r'how\s+(?:to|do\s+you)\s+say\s+"?(?P<text>.+?)"?\s+in\s+(?P<target>\w+)'
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                try:
                    target_lang = self.translator._validate_language(
                        match.group('target'), 
                        "target"
                    )
                    return {
                        'intent': 'translate',
                        'text': match.group('text').strip('"'),
                        'target_lang': target_lang,
                        'urgency': UrgencyLevel.NORMAL.name
                    }
                except TranslationAPIError as e:
                    raise IntentParseError(str(e))
        
        raise IntentParseError(
            "Please specify text and target language\n"
            "Examples:\n"
            "- 'translate hello to french'\n"
            "- 'how to say thank you in spanish'"
        )

    def get_supported_languages(self) -> Dict[str, str]:
        """Return supported translation languages"""
        return self.translator.get_supported_languages()
