# utils.py

from what3words.w3w import what3words
from qgiscommons2.settings import pluginSetting

def get_w3w_instance():
    """
    Creates and returns a what3words API instance based on the current settings.

    Returns:
        what3words: A configured what3words API instance.
    """
    apiKey = pluginSetting("apiKey", namespace="what3words")
    addressLanguage = pluginSetting("addressLanguage", namespace="what3words")
    apiBaseUrl = pluginSetting("apiBaseUrl", namespace="what3words")  # Add apiBaseUrl if applicable

    if not apiKey:
        raise ValueError("API key is not set. Please configure the plugin settings.")

    return what3words(apikey=apiKey, addressLanguage=addressLanguage, apiBaseUrl=apiBaseUrl)