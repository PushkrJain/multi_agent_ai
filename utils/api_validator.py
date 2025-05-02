import requests
import os
from typing import Tuple

def validate_weather_keys() -> Tuple[bool, str]:
    owm_key = os.getenv('OWM_API_KEY')
    wa_key = os.getenv('WEATHERAPI_KEY')
    messages = []
    
    # Test OpenWeatherMap
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={'q': 'London', 'appid': owm_key, 'units': 'metric'},
            timeout=5
        )
        if response.status_code == 401:
            messages.append("OpenWeatherMap key invalid")
    except Exception as e:
        messages.append(f"OpenWeatherMap test failed: {str(e)}")
    
    # Test WeatherAPI
    try:
        response = requests.get(
            "https://api.weatherapi.com/v1/current.json",
            params={'q': 'London', 'key': wa_key},
            timeout=5
        )
        if response.status_code == 403:
            messages.append("WeatherAPI key invalid")
    except Exception as e:
        messages.append(f"WeatherAPI test failed: {str(e)}")
    
    return (len(messages) == 0, "\n".join(messages))
