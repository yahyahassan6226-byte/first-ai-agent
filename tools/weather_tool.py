import os

import requests
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# CONFIGURATION
# =========================================================

OPENWEATHER_API_KEY = (
    os.getenv("OPENWEATHER_API_KEY")
    or os.getenv("WEATHER_API_KEY")
)

OPENWEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)

REQUEST_TIMEOUT = 10


# =========================================================
# WEATHER TOOL
# =========================================================

def get_weather(city: str) -> str:
    """
    Soo hel cimilada hadda ee magaalo.

    Args:
        city:
            Magaca magaalada.
            Tusaale:
            "Mogadishu"
            "Garowe"
            "Nairobi"
            "Mogadishu, SO"

    Returns:
        Weather information string.
    """

    # -----------------------------------------------------
    # VALIDATE CITY
    # -----------------------------------------------------

    if not isinstance(city, str):
        return (
            "Weather error: city waa inuu noqdaa string."
        )

    city = city.strip()

    if not city:
        return (
            "Weather error: Magaca magaalada lama bixin."
        )

    # -----------------------------------------------------
    # CHECK API KEY
    # -----------------------------------------------------

    if not OPENWEATHER_API_KEY:
        return (
            "Weather error: API key lama helin.\n"
            "Ku dar .env file-ka:\n"
            "OPENWEATHER_API_KEY=your_api_key"
        )

    # -----------------------------------------------------
    # REQUEST PARAMETERS
    # -----------------------------------------------------

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    # -----------------------------------------------------
    # CALL WEATHER API
    # -----------------------------------------------------

    try:
        response = requests.get(
            OPENWEATHER_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

    except requests.Timeout:
        return (
            "Weather error: Weather API-ga "
            "waqtigii ayuu dhaafay."
        )

    except requests.ConnectionError:
        return (
            "Weather error: Internet connection "
            "lama heli karo."
        )

    except requests.RequestException as error:
        return (
            f"Weather request error: {error}"
        )

    # -----------------------------------------------------
    # HANDLE HTTP ERRORS
    # -----------------------------------------------------

    if response.status_code == 401:
        return (
            "Weather error: API key-ga ma saxna "
            "ama lama oggola."
        )

    if response.status_code == 404:
        return (
            f"Weather error: Magaalada '{city}' "
            "lama helin."
        )

    if response.status_code == 429:
        return (
            "Weather error: API request limit "
            "ayaa la gaaray."
        )

    if response.status_code != 200:
        return (
            "Weather error: API-gu wuxuu soo celiyay "
            f"HTTP {response.status_code}."
        )

    # -----------------------------------------------------
    # PARSE JSON
    # -----------------------------------------------------

    try:
        data = response.json()

    except ValueError:
        return (
            "Weather error: API response-ka "
            "JSON sax ah ma aha."
        )

    # -----------------------------------------------------
    # EXTRACT WEATHER DATA
    # -----------------------------------------------------

    try:
        location_name = data.get(
            "name",
            city,
        )

        country = (
            data.get("sys", {})
            .get("country", "")
        )

        main_data = data.get(
            "main",
            {}
        )

        temperature = main_data.get(
            "temp"
        )

        feels_like = main_data.get(
            "feels_like"
        )

        humidity = main_data.get(
            "humidity"
        )

        pressure = main_data.get(
            "pressure"
        )

        weather_items = data.get(
            "weather",
            []
        )

        if weather_items:
            description = weather_items[0].get(
                "description",
                "Unknown",
            )
        else:
            description = "Unknown"

        wind_data = data.get(
            "wind",
            {}
        )

        wind_speed = wind_data.get(
            "speed"
        )

    except (TypeError, KeyError) as error:
        return (
            "Weather parsing error: "
            f"{error}"
        )

    # -----------------------------------------------------
    # FORMAT LOCATION
    # -----------------------------------------------------

    if country:
        full_location = (
            f"{location_name}, {country}"
        )
    else:
        full_location = location_name

    # -----------------------------------------------------
    # FORMAT RESULT
    # -----------------------------------------------------

    lines = [
        f"Location: {full_location}",
    ]

    if temperature is not None:
        lines.append(
            f"Temperature: {temperature}°C"
        )

    if feels_like is not None:
        lines.append(
            f"Feels like: {feels_like}°C"
        )

    lines.append(
        f"Conditions: {description}"
    )

    if humidity is not None:
        lines.append(
            f"Humidity: {humidity}%"
        )

    if pressure is not None:
        lines.append(
            f"Pressure: {pressure} hPa"
        )

    if wind_speed is not None:
        lines.append(
            f"Wind speed: {wind_speed} m/s"
        )

    return "\n".join(lines)


# =========================================================
# OPTIONAL DIRECT TEST
# =========================================================

if __name__ == "__main__":
    print(
        get_weather(
            "Mogadishu, SO"
        )
    )