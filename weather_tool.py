"""
Weather tool — real weather lookup via the free Open-Meteo API (no API key).
"""

import requests

# Open-Meteo WMO weather codes → plain-English descriptions.
_WMO_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def get_weather(city: str) -> str:
    """Look up the current weather for *city* using Open-Meteo.

    Returns a natural-language sentence suitable for TTS playback.
    """
    try:
        # 1. Geocode city name → lat/lon.
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city, "count": 1}, timeout=10)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        results = geo_data.get("results")
        if not results:
            return f"Sorry, I couldn't find a city called {city}."

        location = results[0]
        lat = location["latitude"]
        lon = location["longitude"]
        resolved_name = location.get("name", city)
        country = location.get("country", "")

        # 2. Fetch current weather.
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_resp = requests.get(
            weather_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
            },
            timeout=10,
        )
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        current = weather_data.get("current_weather", {})
        temp = current.get("temperature", "unknown")
        wind = current.get("windspeed", "unknown")
        code = current.get("weathercode", -1)
        condition = _WMO_CODES.get(code, "unknown conditions")

        location_str = f"{resolved_name}, {country}" if country else resolved_name
        return (
            f"Right now in {location_str} it's {temp}°C with {condition}. "
            f"Wind speed is {wind} km/h."
        )

    except requests.RequestException as e:
        return f"Sorry, I couldn't fetch the weather right now. Network error: {e}"
    except Exception as e:
        return f"Sorry, something went wrong looking up the weather. {e}"


def get_weather_forecast(city: str, days_ahead: int = 1) -> str:
    """Look up the weather forecast for *city* for a future day using Open-Meteo.

    Args:
        city: City name.
        days_ahead: Number of days ahead (1 = tomorrow, 2 = day after tomorrow, etc.). Default is 1.

    Returns a natural spoken sentence describing the forecast.
    """
    # Groq sometimes sends days_ahead as a string (e.g. "0" instead of 0).
    try:
        days_ahead = int(days_ahead)
    except (TypeError, ValueError):
        days_ahead = 1

    try:
        # 1. Geocode city name → lat/lon.
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city, "count": 1}, timeout=10)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        results = geo_data.get("results")
        if not results:
            return f"Sorry, I couldn't find a city called {city}."

        location = results[0]
        lat = location["latitude"]
        lon = location["longitude"]
        resolved_name = location.get("name", city)
        country = location.get("country", "")

        # 2. Fetch daily forecast.
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_resp = requests.get(
            weather_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                "timezone": "auto",
            },
            timeout=10,
        )
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        daily = weather_data.get("daily", {})
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        codes = daily.get("weathercode", [])

        idx = max(0, min(days_ahead, len(dates) - 1)) if dates else 0
        if not dates or idx >= len(dates):
            return f"Sorry, forecast data is not available for {days_ahead} days ahead."

        high = max_temps[idx] if idx < len(max_temps) else "unknown"
        low = min_temps[idx] if idx < len(min_temps) else "unknown"
        code = codes[idx] if idx < len(codes) else -1
        condition = _WMO_CODES.get(code, "unknown conditions")

        if days_ahead == 0:
            day_label = "Today"
        elif days_ahead == 1:
            day_label = "Tomorrow"
        else:
            day_label = f"In {days_ahead} days"
        location_str = f"{resolved_name}, {country}" if country else resolved_name

        return (
            f"{day_label} in {location_str} expect a high of {high}°C, "
            f"a low of {low}°C, with {condition}."
        )

    except requests.RequestException as e:
        return f"Sorry, I couldn't fetch the forecast right now. Network error: {e}"
    except Exception as e:
        return f"Sorry, something went wrong looking up the forecast. {e}"
