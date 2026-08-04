import os

import requests


GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city: str) -> str:
    """Soo qaad cimilada hadda jirta ee magaalada la siiyay."""

    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return "Error: WEATHER_API_KEY lama helin."

    city = city.strip()

    if not city:
        return "Error: Magaca magaalada lama bixin."

    try:
        # 1. Magaca magaalada u beddel latitude iyo longitude.
        geocoding_response = requests.get(
            GEOCODING_URL,
            params={
                "q": city,
                "limit": 1,
                "appid": api_key,
            },
            timeout=10,
        )
        geocoding_response.raise_for_status()

        locations = geocoding_response.json()

        if not locations:
            return f"Error: Magaalada '{city}' lama helin."

        location = locations[0]
        latitude = location["lat"]
        longitude = location["lon"]
        location_name = location["name"]
        country = location.get("country", "Unknown")

        # 2. Coordinates-ka ku soo qaad cimilada hadda jirta.
        weather_response = requests.get(
            CURRENT_WEATHER_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "appid": api_key,
                "units": "metric",
            },
            timeout=10,
        )
        weather_response.raise_for_status()

        data = weather_response.json()

        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]

        return (
            f"Location: {location_name}, {country}\n"
            f"Temperature: {temperature}°C\n"
            f"Feels like: {feels_like}°C\n"
            f"Condition: {description}\n"
            f"Humidity: {humidity}%\n"
            f"Wind speed: {wind_speed} m/s"
        )

    except requests.Timeout:
        return "Error: Weather API-ga waqtigii ayuu dhaafay."

    except requests.HTTPError as error:
        status_code = error.response.status_code

        if status_code == 401:
            return "Error: Weather API key-ga ma shaqaynayo."

        if status_code == 429:
            return "Error: Weather API request limit ayaa la gaaray."

        return f"Weather API error: HTTP {status_code}"

    except requests.RequestException as error:
        return f"Network error: {error}"

    except (KeyError, IndexError, TypeError):
        return "Error: Weather API wuxuu soo celiyay xog aan la filayn."