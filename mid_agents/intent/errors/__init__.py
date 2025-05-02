class WeatherAPIError(Exception):
    """Error raised when weather API fails"""
    pass

class NewsAPIError(Exception):
    """Error raised when news API fails"""
    pass

class TranslationAPIError(Exception):
    """Error raised when translation API fails"""
    pass

class IntentParseError(Exception):
    """Error raised when intent parsing fails"""
    pass

class SecurityViolationError(Exception):
    """Error raised when security check fails"""
    pass
