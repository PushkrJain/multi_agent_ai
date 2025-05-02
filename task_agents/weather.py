import os
import requests
from typing import Optional, Dict, Any
from utils.errors import WeatherAPIError

class WeatherAgent:
    def __init__(self):
        self.owm_key = os.getenv('OWM_API_KEY')
        self.weather_api_key = os.getenv('WEATHERAPI_KEY')
        self.primary_url = "https://api.openweathermap.org/data/2.5/weather"
        self.fallback_url = "https://api.weatherapi.com/v1/current.json"
        self.timeout = 5

    def get_weather(self, location: str) -> Dict[str, Any]:
        if len(location) < 2:
            raise WeatherAPIError("Location name too short")
        try:
            primary_data = self._call_owm_api(location)
            if primary_data:
                return self._format_owm_data(primary_data)

            fallback_data = self._call_weatherapi(location)
            if fallback_data:
                return self._format_wa_data(fallback_data)

            raise WeatherAPIError(f"Could not find weather for: {location}")
        except Exception as e:
            if monitor:
                monitor.report_error("weather")
            raise WeatherAPIError(str(e))

    def _call_owm_api(self, location: str) -> Optional[Dict]:
        try:
            response = requests.get(
                self.primary_url,
                params={
                    'q': location,
                    'appid': self.owm_key,
                    'units': 'metric'
                },
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None

    def _call_weatherapi(self, location: str) -> Optional[Dict]:
        try:
            response = requests.get(
                self.fallback_url,
                params={
                    'q': location,
                    'key': self.weather_api_key
                },
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None

    def _format_owm_data(self, data: Dict) -> Dict[str, Any]:
        temp_c = round(data['main']['temp'], 1)
        return {
            'location': data.get('name', 'Unknown Location'),
            'condition': data['weather'][0]['description'].capitalize(),
            'temp_c': temp_c,
            'temp_f': round((temp_c * 9/5) + 32, 1),
            'humidity': data['main']['humidity'],
            'wind': round(data['wind']['speed'] * 3.6, 1),  # m/s to km/h
            'pressure': data['main']['pressure']
        }

    def _format_wa_data(self, data: Dict) -> Dict[str, Any]:
        return {
            'location': data['location']['name'],
            'condition': data['current']['condition']['text'],
            'temp_c': data['current']['temp_c'],
            'temp_f': data['current']['temp_f'],
            'humidity': data['current']['humidity'],
            'wind': data['current']['wind_kph'],
            'pressure': data['current']['pressure_mb']
        }

# Attach monitoring
try:
    from mid_agents.monitoring.error_monitor import ErrorMonitor
    monitor = ErrorMonitor()
except:
    monitor = None
