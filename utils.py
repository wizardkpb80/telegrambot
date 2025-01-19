"""
utils.py

This module contains utility functions for text translation,
weather-based calculations, and daily calorie/water intake estimations.
"""
from translate import Translator
from my_api import get_weather
from logging_config import logger

def translate_text(text, src_language="ru", dest_language="en"):
    """
    Translates text from one language to another using the `translate` library.

    :param text: The text to be translated.
    :param src_language: The source language (default is Russian 'ru').
    :param dest_language: The target language (default is English 'en').
    :return: Translated text.
    """
    try:
        translator = Translator(from_lang=src_language, to_lang=dest_language)
        translated_text = translator.translate(text)
        return translated_text
    except (ValueError, RuntimeError) as e:
        logger.error("Translation error: %s", e)
        return None

async def calculate_calories(user_data):
    """
    Calculates the daily calorie intake goal for a user based on their weight, height, age,
    gender, and daily activity level.

    Args:
        user_data (dict): A dictionary containing user information with the following keys:
            - 'weight' (float or int): The user's weight in kilograms.
            - 'height' (float or int): The user's height in centimeters.
            - 'age' (int): The user's age in years.
            - 'gender' (str): The user's gender ('male' or 'female').
            - 'activity' (int): The user's daily activity duration in minutes.

    Returns:
        float: The recommended daily calorie intake, rounded to the nearest whole number.

    Notes:
        - The Basal Metabolic Rate (bmr) is calculated using the Mifflin-St Jeor Equation:
            - For males: bmr = 10 * weight + 6.25 * height - 5 * age + 5
            - For females: bmr = 10 * weight + 6.25 * height - 5 * age - 161
        - The total calorie goal includes an activity factor:
            - Less than 30 minutes: 1.2
            - 30–60 minutes: 1.375
            - 60–120 minutes: 1.55
            - 120–180 minutes: 1.725
            - More than 180 minutes: 1.9
        - Additional calories are added for training, calculated as:
            200 + (activity // 30) * 50.

    Example:
        user_data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'gender': 'male',
            'activity': 45
        }
        calorie_goal = await calculate_calories(user_data)
        print(calorie_goal)  # Outputs the calculated calorie intake goal.
    """
    weight = user_data.get('weight')
    height = user_data.get('height')
    age = user_data.get('age')
    gender = user_data.get('gender')  # мужской или женский
    activity = user_data.get('activity')  # Минуты активности в день

    # Определяем половой коэффициент
    if gender == 'male':
        gender_coefficient = 5  # Для мужчин
    else:
        gender_coefficient = -161  # Для женщин

    # Рассчитываем базовый обмен веществ (bmr)
    bmr = 10 * weight + 6.25 * height - 5 * age + gender_coefficient

    # Коэффициент активности
    if activity < 30:
        activity_factor = 1.2
    elif activity < 60:
        activity_factor = 1.375
    elif activity < 120:
        activity_factor = 1.55
    elif activity < 180:
        activity_factor = 1.725
    else:
        activity_factor = 1.9

    # Учитываем уровень активности
    daily_calories = bmr * activity_factor

    # Дополнительные калории за тренировки (например, 200-400 калорий)
    training_calories = 200 + (activity // 30) * 50  # Например, 200-400 калорий

    # Итоговая норма калорий
    total_calories = daily_calories + training_calories
    return round(total_calories,0)

async def calculate_water(user_data):
    """
    Calculates the daily water intake goal for a user based on their weight, activity level,
    and the current weather temperature.

    Args:
        user_data (dict): A dictionary containing user data with the following keys:
            - 'city' (str): The name of the user's city to get the weather data.
            - 'weight' (float or int): The user's weight in kilograms.
            - 'activity' (int): The user's daily activity duration in minutes.

    Returns:
        float: The recommended daily water intake in milliliters, rounded to the nearest whole

    Notes:
        - Water intake is calculated as 30 ml per kg of body weight plus an additional 500 ml
          for every 30 minutes of activity.
        - If the temperature in the user's city is above 25°C, an extra 50 ml is added for every
          above 25°C, up to a maximum of 1000 ml.

    Example:
        user_data = {
            'city': 'New York',
            'weight': 70,
            'activity': 60
        }
        water_goal = await calculate_water(user_data)
        print(water_goal)  # Outputs the calculated water intake goal.
    """
    city_eng = translate_text(user_data.get('city'))  # Implement or import translate_text
    temp = await get_weather(city_eng)

    # Рассчитать нормы
    weight = user_data.get('weight')
    activity = user_data.get('activity')

    water_goal = weight * 30 + (activity // 30) * 500
    if temp and temp > 25:
        # Если температура больше 25°C, увеличиваем норму воды
        extra_water = (temp - 25) * 50 + 500  # за каждый градус выше 25°C добавляем 50 мл
        water_goal += min(extra_water, 1000)  # Максимум 1000 мл добавляется

    return round(water_goal,0)
