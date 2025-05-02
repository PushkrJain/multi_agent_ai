import os
import requests
from typing import List, Dict, Any
from mid_agents.intent.errors import NewsAPIError

# Try to attach monitoring (safe import)
try:
    from mid_agents.monitoring.error_monitor import ErrorMonitor
    monitor = ErrorMonitor()
except Exception:
    monitor = None

class NewsAgent:
    def __init__(self):
        self.api_key = os.getenv('NEWSAPI_KEY') or "your_api_key_here"
        self.base_url = "https://newsapi.org/v2/top-headlines"
        self.timeout = 10
        self.country_codes = {
            'india': 'in', 'indian': 'in',
            'us': 'us', 'usa': 'us', 'american': 'us',
            'uk': 'gb', 'british': 'gb', 'england': 'gb',
            'france': 'fr', 'french': 'fr',
            'germany': 'de', 'german': 'de',
            'japan': 'jp', 'japanese': 'jp',
            'china': 'cn', 'chinese': 'cn',
            'australia': 'au', 'canada': 'ca',
            'greece': 'gr', 'netherlands': 'nl'
        }

    def get_news(self, query: str = None, category: str = None, country: str = None) -> List[Dict[str, Any]]:
        if not self.api_key or self.api_key == "your_api_key_here":
            if monitor: monitor.report_error("news")
            raise NewsAPIError("NewsAPI service not configured")

        try:
            params = {
                'apiKey': self.api_key,
                'pageSize': 5,
                'language': 'en'
            }

            if country:
                params['country'] = self._normalize_country(country)

            if query:
                params['q'] = query[:100]

            if category:
                category = category.lower()
                if category in ['technology', 'tech']:
                    category = 'technology'
                params['category'] = category

            articles = self._get_articles(params)

            if not articles:
                # Fallback to general news
                params.pop('q', None)
                params['category'] = 'general'
                articles = self._get_articles(params)

            if not articles:
                if monitor: monitor.report_error("news")
                raise NewsAPIError("No news articles available")

            return self._format_news_data(articles)

        except requests.exceptions.RequestException as e:
            if monitor: monitor.report_error("news")
            raise NewsAPIError(f"Failed to connect to news service: {str(e)}")
        except Exception as e:
            if monitor: monitor.report_error("news")
            raise NewsAPIError(f"News service error: {str(e)}")

    def _get_articles(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        response = requests.get(self.base_url, params=params, timeout=self.timeout)
        if response.status_code == 401:
            raise NewsAPIError("Invalid NewsAPI key")
        elif response.status_code == 429:
            raise NewsAPIError("NewsAPI rate limit exceeded")
        elif response.status_code != 200:
            raise NewsAPIError(f"NewsAPI error: {response.json().get('message', 'Unknown error')}")

        data = response.json()
        return data.get('articles', [])

    def _normalize_country(self, country: str) -> str:
        return self.country_codes.get(country.lower().strip(), country.lower())

    def _format_news_data(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        return [{
            'title': a['title'],
            'source': a['source']['name'],
            'description': a.get('description', 'No description available'),
            'url': a['url'],
            'published_at': a['publishedAt']
        } for a in articles]
