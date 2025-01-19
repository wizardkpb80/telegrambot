"""
This module contains functions to fetch weather information and food data using various APIs.
It includes asynchronous and synchronous functions for interacting with OpenWeatherMap,
Nutritionix, and Edamam APIs.
"""
import aiohttp
import requests
import random
from logging_config import logger

API_KEY_WEATHER = "9d23a146cb4a5b56900953777a1fb758"
API_BASE_FOOD = "https://world.openfoodfacts.org/api/v0/product/"

async def get_weather(city: str) -> float:
    """
    Fetches the current temperature for a given city using the OpenWeatherMap API.

    Args:
        city (str): The city name for which the weather is to be fetched.

    Returns:
        float: The temperature in Celsius if the request is successful, None if there's an error.
    """
    try:
   #     city_eng = translate_text(city)  # Implement or import translate_text
        async with aiohttp.ClientSession() as session:
            url = (f"http://api.openweathermap.org/data/2.5/weather?q={city}"
                   f"&appid={API_KEY_WEATHER}&units=metric")
            async with session.get(url) as response:
                data = await response.json()
                if response.status == 200:
                    return data['main']['temp']
                else:
                    logger.error(f"Ошибка при получении погоды: {data}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {e}")
        return None

def get_food_info(product_name):
    """
    Fetches calorie information for a given product from the Nutritionix API.

    Args:
        product_name (str): The name of the food product.

    Returns:
        dict: A dictionary containing the product's name and calorie information
    """
    api_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    app_id = "75f0c9f7"  # Replace with your Nutritionix App ID
    app_key = "a65eba23e5ec71c31c96c87c1835b4af"  # Replace with your Nutritionix App Key

    headers = {
        "x-app-id": app_id,
        "x-app-key": app_key,
        "Content-Type": "application/json"
    }

    data = {"query": product_name, "timezone": "US/Eastern"}

    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        if "foods" in response_data and len(response_data["foods"]) > 0:
            food_data = response_data["foods"][0]
            calories = food_data.get("nf_calories", 0)
            return {
                'name': product_name.capitalize(),
                'calories': round(calories, 2)
            }
        else:
            logger.error(f"No calorie data found for {product_name}.")
            return None
    else:
        logger.error(f"Failed to fetch data: {response.status_code} - {response.text}")
        return None

def get_random_10_foods():
    """
    Fetches a list of low-calorie foods using the Edamam API and returns a random selection.

    Returns:
        list: A list of up to 3 low-calorie foods with their calorie information.
    """
    app_id = 'd8acac44'
    app_key = 'cb104b3fb3684a250aab4992947d4bba'

    food_query = 'apple'  # Change this to any food item you're interested in

    url = f'https://api.edamam.com/api/food-database/v2/parser'
    params = {
        'app_id': app_id,
        'app_key': app_key,
        'ingr': food_query
    }

    response = requests.get(url, params=params)
    data = response.json()

    low_calorie_foods = [
        {'name': food['food']['label'], 'calories': food['food']['nutrients'].get('ENERC_KCAL', 0)}
        for food in data['hints'] if food['food']['nutrients'].get('ENERC_KCAL', 0) < 100
    ]

    logger.info(f"User recommended foods {low_calorie_foods}")
    return random.sample(low_calorie_foods, min(3, len(low_calorie_foods)))
