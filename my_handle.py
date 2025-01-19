"""
This module contains functions to fetch handle
"""
from abc import ABC, abstractmethod
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, Updater, CallbackQueryHandler, ContextTypes
from users import users
from my_api import get_food_info, get_random_10_foods
from utils import translate_text, calculate_calories, calculate_water
from logging_config import logger
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
matplotlib.use('Agg')


calorie_burn_rate = {
    'бег': 10,  # Calories per minute
    'велосипед': 8,
    'плавание': 12
}

# Сохранение данных в базу
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    step = context.user_data.get('step')
    update_flag = context.user_data.get('update')

    if step == 'log_workout':
        try:
            if 'workout_type' not in context.user_data:
                await update.message.reply_text("Пожалуйста, выберите тип тренировки с помощью /log_workout.")
                return

            workout_type = context.user_data['workout_type']
            user_data = users.get(user_id)
            try:
                workout_time = int(update.message.text)  # Time in minutes
            except ValueError:
                await update.message.reply_text("Пожалуйста, укажите время тренировки в числовом формате (в минутах).")
                return

            if workout_type in calorie_burn_rate:
                calories_burned = calorie_burn_rate[workout_type] * workout_time

                # Calculate additional water intake: 200 ml for every 30 minutes
                water_needed = (workout_time // 30) * 200
                if water_needed > 0:
                    water_goal = water_needed + user_data.get('water_goal')
                    users.update(user_id, water_goal=water_goal, db_update=1)
                if calories_burned > 0:
                    calories_burned = calories_burned + user_data.get('burned_calories')
                    users.update(user_id, burned_calories=calories_burned, db_update=1)

                    response = f"🏃‍♂️ {workout_type.capitalize()} {workout_time} минут — {calories_burned} ккал. Дополнительно: выпейте {water_needed} мл воды."
                    logger.info(f"user {user_id}"+response)
                await update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())

                # Reset the workout type for the user
                del context.user_data['workout_type']
                context.user_data['step'] = None
        except ValueError:
            await update.message.reply_text("Пожалуйста, укажите время тренировки в числовом формате (в минутах).", reply_markup=ReplyKeyboardRemove())
    elif step == 'log_food':
        try:
            logged_calories = int(text)
            user_data = users.get(user_id)
            logged_calories = logged_calories * context.user_data.get('calories') / 100
            logged_calories = round(logged_calories + user_data.get('logged_calories'),0)
            users.update(user_id, logged_calories=logged_calories, db_update=1)
            remaining_food = user_data.get('calorie_goal') - user_data.get('logged_calories')

            #Рекомендация
            random_10_foods = get_random_10_foods()
            recomend_food = f"\nРекомендация продуктов:\n"
            # Display the list of random low-calorie foods with translation
            for food in random_10_foods:
                food_name = f"{food['name']} - {food['calories']} calories"
                translated_food = translate_text(food_name, src_language="en", dest_language="ru")
                recomend_food = recomend_food +"§ "+ translated_food + '\n'
            logger.info(f"user {user_id} " + f"Записано {logged_calories} мл ккал. Осталось: {max(remaining_food, 0)} ккал\n" + recomend_food)
            await update.message.reply_text(
                f"Записано {logged_calories} мл ккал. Осталось: {max(remaining_food, 0)} ккал\n" + recomend_food, reply_markup=ReplyKeyboardRemove()
            )
            del context.user_data['calories']
            context.user_data['step'] = None
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение воды в мл.", reply_markup=ReplyKeyboardRemove())
    elif step == 'log_water':
        try:
            logged_water = int(text)
            user_data = users.get(user_id)
            logged_water = logged_water + user_data.get('logged_water')
            users.update(user_id, logged_water=logged_water, db_update=1)
            remaining_water = user_data.get('water_goal') - user_data.get('logged_water')
            logger.info(
                f"user {user_id} " + f"Вы выпили {logged_water} мл воды. Осталось: {max(remaining_water, 0)} мл до цели." + recomend_food)
            await update.message.reply_text(
                f"Вы выпили {logged_water} мл воды. Осталось: {max(remaining_water, 0)} мл до цели.", reply_markup=ReplyKeyboardRemove()
            )
            context.user_data['step'] = None
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение воды в мл.", reply_markup=ReplyKeyboardRemove())
    elif step == 'weight':
        try:
            users.update(user_id, weight=float(update.message.text))
            if update_flag:
                await set_profile(update, context)
                context.user_data['step'] = None
            else:
                context.user_data['step'] = 'height'
                await update.message.reply_text("Введите ваш рост (в см):", reply_markup=ReplyKeyboardRemove())
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение веса.", reply_markup=ReplyKeyboardRemove())
    elif step == 'height':
        try:
            users.update(user_id, height=float(update.message.text))
            if update_flag:
                await set_profile(update, context)
                context.user_data['step'] = None
            else:
                context.user_data['step'] = 'age'
                await update.message.reply_text("Введите ваш возраст:")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение роста.", reply_markup=ReplyKeyboardRemove())
    elif step == 'age':
        try:
            users.update(user_id, age=float(update.message.text))
            if update_flag:
                await set_profile(update, context)
                context.user_data['step'] = None
            else:
                context.user_data['step'] = 'gender'
                buttons = [
                    [KeyboardButton("male"), KeyboardButton("female")]
                ]
                reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
                await update.message.reply_text(
                    f"Пожалуйста, выберите пол",
                    reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение возраста.", reply_markup=ReplyKeyboardRemove())
    elif step == 'gender':
        gender = update.message.text
        try:
            if gender not in ('male', 'female'):
                context.user_data['step'] = 'gender'
                buttons = [
                    [KeyboardButton("male"), KeyboardButton("female")]
                ]
                reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
                await update.message.reply_text(
                    f"Пожалуйста, выберите пол",
                    reply_markup=reply_markup)
            else:
                users.update(user_id, gender=gender)
                if update_flag:
                    await set_profile(update, context)
                    context.user_data['step'] = None
                else:
                    context.user_data['step'] = 'activity'
                    await update.message.reply_text("Сколько минут активности у вас в день?", reply_markup=ReplyKeyboardRemove())
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение пола.", reply_markup=ReplyKeyboardRemove())
    elif step == 'activity':
        try:
            users.update(user_id, activity=float(update.message.text))
            if update_flag:
                await set_profile(update, context)
                context.user_data['step'] = None
            else:
                context.user_data['step'] = 'city'
                await update.message.reply_text("В каком городе вы находитесь?", reply_markup=ReplyKeyboardRemove())
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение активности.", reply_markup=ReplyKeyboardRemove())

    elif step == 'city':
        users.update(user_id, city=update.message.text)
        user_data = users.get(user_id)
        # Получить температуру через OpenWeatherMap

        water_goal = await calculate_water(user_data)
        calorie_goal = await calculate_calories(user_data)

        users.update(user_id, water_goal=water_goal, calorie_goal=calorie_goal, db_update=1)
        logger.info(
            f"user {user_id} " + f"Профиль настроен! 🎉\n"
            f"Ваша дневная норма воды: {user_data.get('water_goal')} мл.\n"
            f"Ваша дневная норма калорий: {user_data.get('calorie_goal')} ккал.")
        await update.message.reply_text(
            f"Профиль настроен! 🎉\n"
            f"Ваша дневная норма воды: {user_data.get('water_goal')} мл.\n"
            f"Ваша дневная норма калорий: {user_data.get('calorie_goal')} ккал."
        )

        context.user_data['step'] = None
        if update_flag:
            await set_profile(update, context)
    elif update_flag:
        # Параметры для обновления
        if text == "Вес":
            context.user_data['step'] = 'weight'
            await update.message.reply_text(
                f"Ваш текущий вес: {user_data.get('weight', 'Не указан')} кг.\n"
                "Введите новый вес (в кг):",
                reply_markup=ReplyKeyboardRemove(),
            )
        elif text == "Рост":
            context.user_data['step'] = 'height'
            await update.message.reply_text("Введите новый рост (в см):", reply_markup=ReplyKeyboardRemove())
        elif text == "Возраст":
            context.user_data['step'] = 'age'
            await update.message.reply_text("Введите новый возраст:", reply_markup=ReplyKeyboardRemove())
        elif text == "Активность":
            context.user_data['step'] = 'activity'
            await update.message.reply_text("Введите количество минут активности в день:",
                                            reply_markup=ReplyKeyboardRemove())
        elif text == "Город":
            context.user_data['step'] = 'city'
            await update.message.reply_text("Введите ваш город:", reply_markup=ReplyKeyboardRemove())
        elif text == "Сохранить":
            context.user_data['step'] = None
            context.user_data['update'] = False
            user_data = users.get(user_id)
            water_goal = await calculate_water(user_data)
            calorie_goal = await calculate_calories(user_data)

            users.update(user_id, water_goal=water_goal, calorie_goal=calorie_goal, db_update=1)
            logger.info(
                f"user {user_id} " + f"Профиль сохранён! 🎉\n"
                f"Ваша дневная норма воды: {user_data.get('water_goal')} мл.\n"
                f"Ваша дневная норма калорий: {user_data.get('calorie_goal')} ккал.")
            await update.message.reply_text(
                f"Профиль сохранён! 🎉\n"
                f"Ваша дневная норма воды: {user_data.get('water_goal')} мл.\n"
                f"Ваша дневная норма калорий: {user_data.get('calorie_goal')} ккал.",
                reply_markup = ReplyKeyboardRemove()
            )
        elif text == "Отмена":
            # Завершаем процесс обновления
            context.user_data['step'] = None
            logger.info(
                f"user {user_id} " + f"Отмена изменения профиля")
            await update.message.reply_text("Отмена изменения профиля",reply_markup=ReplyKeyboardRemove())
            context.user_data['update'] = False

# Команда /set_profile
async def set_profile(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data or user_data.get('water_goal') == 0:
        user_data = users.initialize_user_data()
        user_data['last_active'] = datetime.datetime.now()
        users.add(user_id, user_data)
        context.user_data['step'] = 'weight'
        await update.message.reply_text("Введите ваш вес (в кг):", reply_markup=ReplyKeyboardRemove())
    else:
        # Если данные найдены, показываем профиль и предлагаем обновить
        buttons = [
            [KeyboardButton("Вес"), KeyboardButton("Рост")],
            [KeyboardButton("Возраст"), KeyboardButton("Активность")],
            [KeyboardButton("Город")],
            [KeyboardButton("Отмена"), KeyboardButton("Сохранить")],
        ]
        reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        logger.info(
            f"user {user_id} " + f"set_profile")
        await update.message.reply_text(
            f"Ваш профиль:\n"
            f"Вес: {user_data.get('weight', 'Не указан')} кг\n"
            f"Рост: {user_data.get('height', 'Не указан')} см\n"
            f"Возраст: {user_data.get('age', 'Не указан')} лет\n"
            f"Активность: {user_data.get('activity', 'Не указана')} минут/день\n"
            f"Город: {user_data.get('city', 'Не указан')}\n\n"
            f"Выберите, что вы хотите обновить:",
            reply_markup=reply_markup,
        )
        context.user_data['update'] = True

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    logger.info(
        f"user {user_id} " + f"start")
    await update.message.reply_text(
        "Привет! Я ваш помощник по расчету нормы воды, калорий и трекингу активности. "
        "Используйте команду /set_profile для настройки профиля.", reply_markup=ReplyKeyboardRemove()
    )

# Function to handle the callback from the confirmation buttons
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    # Handle the 'yes' response
    if query.data == 'restart_yes':
        user_data = users.get(user_id)
        if user_data:
            try:
                # Reset the user data (burned calories, logged calories, logged water)
                users.update(user_id, burned_calories=0, logged_calories=0, logged_water=0, db_update=1)
                logger.info(
                    f"user {user_id} " + f"День перезапущен. Накопительные показатели обнулены. Удачи!")
                await query.edit_message_text("День перезапущен. Накопительные показатели обнулены. Удачи!")
            except (IndexError, ValueError):
                await query.edit_message_text("Что-то пошло не так при перезапуске дня.")
        else:
            await query.edit_message_text("Пользовательские данные не найдены.")

    # Handle the 'no' response
    elif query.data == 'restart_no':
        logger.info(
            f"user {user_id} " + f"Перезапуск дня отменен.")
        await query.edit_message_text("Перезапуск дня отменен.")

# Перезапуск дня
async def restart_day(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = users.get(user_id)

    if not user_data or user_data.get('water_goal') == 0:
        await update.message.reply_text("Пожалуйста, настройте профиль с помощью команды /set_profile.")
        return

    keyboard = [
        [
            InlineKeyboardButton("Да, перезапустить день", callback_data='restart_yes'),
            InlineKeyboardButton("Нет, отменить", callback_data='restart_no')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['step'] = "restart_day"
    await update.message.reply_text("Вы уверены, что хотите перезапустить день? Все данные будут обнулены.",
                                    reply_markup=reply_markup)

# Логирование воды
async def log_water(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data or user_data.get('water_goal') == 0:
        await update.message.reply_text("Пожалуйста, настройте профиль с помощью команды /set_profile.", reply_markup=ReplyKeyboardRemove())
        return
    try:
        logged_water = int(context.args[0])
        logged_water = logged_water + user_data.get('logged_water')
        users.update(user_id, logged_water=logged_water, db_update=1)
        remaining_water = user_data.get('water_goal') - user_data.get('logged_water')
        logger.info(
            f"user {user_id} " + f"Вы выпили {logged_water} мл воды. Осталось: {max(remaining_water, 0)} мл до цели.")
        await update.message.reply_text(
            f"Вы выпили {logged_water} мл воды. Осталось: {max(remaining_water, 0)} мл до цели.", reply_markup=ReplyKeyboardRemove()
        )
    except (IndexError, ValueError):
        context.user_data['step'] = 'log_water'
        await update.message.reply_text("Пожалуйста, укажите количество воды в мл после команды.", reply_markup=ReplyKeyboardRemove())

# Логирование еды
async def log_food(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data or user_data.get('calorie_goal') == 0:
        await update.message.reply_text("Пожалуйста, настройте профиль с помощью команды /set_profile.", reply_markup=ReplyKeyboardRemove())
        return

    try:
        if context.args:
            meal = ' '.join(context.args)
            response = get_food_info(translate_text(meal))
            if 'calories' in response:
                if response['calories'] > 0:
                    context.user_data['step'] = 'log_food'
                    context.user_data['calories'] = response['calories']
                    logger.info(
                        f"user {user_id} " + f"🍎 {translate_text(response['name'].capitalize(), src_language="en", 
                                                                 dest_language="ru")} содержит "
                                             f"{response['calories']} ккал на 100 г. Сколько грамм(мл) вы съели?")
                    await update.message.reply_text(
                        f"🍎 {translate_text(response['name'].capitalize(), src_language="en", 
                                            dest_language="ru")} содержит {response['calories']} ккал на 100 г. "
                        f"Сколько грамм(мл) вы съели?", reply_markup=ReplyKeyboardRemove()
                   )
                else:
                    await update.message.reply_text("Продукт найден. 0 ккал")
            else:
                await update.message.reply_text("Продукт не найден. Попробуйте другой запрос.")
        else:
            await update.message.reply_text("Продукт не задан.")
    except Exception as e:
        logger.error(f"Ошибка при запросе продукта: {e}")
        await update.message.reply_text("Произошла ошибка при получении данных о продукте.")

# Логирование тренировок
async def log_workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Create an inline keyboard with workout type options
    keyboard = [
        [
            InlineKeyboardButton("Бег", callback_data='бег'),
            InlineKeyboardButton("Велосипед", callback_data='велосипед'),
            InlineKeyboardButton("Плавание", callback_data='плавание'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Ask the user to select a workout type
    await update.message.reply_text("Выберите тип тренировки:", reply_markup=reply_markup)

# Function to handle the callback when a workout type is selected
async def workout_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    workout_type = query.data  # The selected workout type (e.g., 'бег', 'велосипед', etc.)

    # Ask the user to provide the time (in minutes)
    await query.answer()  # Acknowledge the button press
    await query.edit_message_text(f"Вы выбрали {workout_type.capitalize()}. Укажите время тренировки в минутах:")

    # Store the selected workout type in context.user_data for later use
    context.user_data['step'] = "log_workout"
    context.user_data['workout_type'] = workout_type

# Прогресс
async def check_progress(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data or user_data.get('calorie_goal') == 0:
        await update.message.reply_text("Пожалуйста, настройте профиль с помощью команды /set_profile.")
        return

    water = user_data.get('logged_water')
    water_goal = user_data.get('water_goal')
    calories = user_data.get('logged_calories')
    calorie_goal = user_data.get('calorie_goal')
    burned = user_data.get('burned_calories')
    logger.info(
        f"user {user_id} " + f"📊 Прогресс:\n"
        f"Вода:\n"
        f"§ Выпито: {water} мл из {water_goal} мл.\n"
        f"§ Осталось: {max(water_goal - water, 0)} мл.\n\n"
        f"Калории:\n"
        f"§ Потреблено: {calories} ккал из {calorie_goal} ккал.\n"
        f"§ Сожжено калорий: {burned} ккал.\n"
        f"§ Баланс: {max(calorie_goal - calories + burned, 0)} ккал.\n")
    await update.message.reply_text(
        f"📊 Прогресс:\n"
        f"Вода:\n"
        f"§ Выпито: {water} мл из {water_goal} мл.\n"
        f"§ Осталось: {max(water_goal - water, 0)} мл.\n\n"
        f"Калории:\n"
        f"§ Потреблено: {calories} ккал из {calorie_goal} ккал.\n"
        f"§ Сожжено калорий: {burned} ккал.\n"
        f"§ Баланс: {max(calorie_goal - calories + burned, 0)} ккал.\n"
    )

# Построение графика
def plot_progress(user_id, dates, water, calories, water_goal, calorie_goal, burned_calories, time_period):
    """
    Построение графика прогресса пользователя с учетом целей воды, калорий и сожженных калорий.
    Принимает time_period для настройки временной шкалы.
    Возвращает путь к сохраненному изображению.
    """
    # Convert dates to pandas datetime format for easier manipulation
    dates = pd.to_datetime(dates)

    # Aggregate data based on the time period
    if time_period == "day":
        # Data already in daily format, so no change needed
        aggregated_dates = dates
        aggregated_water = water
        aggregated_calories = calories
        aggregated_burned_calories = burned_calories
        aggregated_water_goal = water_goal
        aggregated_calorie_goal = calorie_goal
    elif time_period == "week":
        # Group by week and sum the values
        week_start_dates = dates - pd.to_timedelta(dates.dt.weekday, unit='D')
        aggregated_data = pd.DataFrame({
            'dates': week_start_dates,
            'water': water,
            'calories': calories,
            'burned_calories': burned_calories,
            'water_goal': water_goal,
            'calorie_goal': calorie_goal
        }).groupby('dates').sum()
        aggregated_dates = aggregated_data.index
        aggregated_water = aggregated_data['water']
        aggregated_calories = aggregated_data['calories']
        aggregated_burned_calories = aggregated_data['burned_calories']
        aggregated_water_goal = aggregated_data['water_goal']
        aggregated_calorie_goal = aggregated_data['calorie_goal']
    elif time_period == "month":
        # Group by month and sum the values
        month_start_dates = dates.dt.to_period('M').dt.start_time
        aggregated_data = pd.DataFrame({
            'dates': month_start_dates,
            'water': water,
            'calories': calories,
            'burned_calories': burned_calories,
            'water_goal': water_goal,
            'calorie_goal': calorie_goal
        }).groupby('dates').sum()
        aggregated_dates = aggregated_data.index
        aggregated_water = aggregated_data['water']
        aggregated_calories = aggregated_data['calories']
        aggregated_burned_calories = aggregated_data['burned_calories']
        aggregated_water_goal = aggregated_data['water_goal']
        aggregated_calorie_goal = aggregated_data['calorie_goal']
    elif time_period == "year":
        # Group by year and sum the values
        year_start_dates = dates.dt.to_period('A').dt.start_time
        aggregated_data = pd.DataFrame({
            'dates': year_start_dates,
            'water': water,
            'calories': calories,
            'burned_calories': burned_calories,
            'water_goal': water_goal,
            'calorie_goal': calorie_goal
        }).groupby('dates').sum()
        aggregated_dates = aggregated_data.index
        aggregated_water = aggregated_data['water']
        aggregated_calories = aggregated_data['calories']
        aggregated_burned_calories = aggregated_data['burned_calories']
        aggregated_water_goal = aggregated_data['water_goal']
        aggregated_calorie_goal = aggregated_data['calorie_goal']

    # Plotting the data
    plt.figure(figsize=(10, 6))

    # График воды
    plt.plot(aggregated_dates, aggregated_water, label="Вода (мл)", marker="o", color="blue")

    # График целевой воды по дням
    plt.plot(aggregated_dates, aggregated_water_goal, label="Рекомендуемая вода (мл)", linestyle="--", color="blue")

    # График калорий
    plt.plot(aggregated_dates, aggregated_calories, label="Калории (ккал)", marker="o", color="green")

    # График целевых калорий по дням
    plt.plot(aggregated_dates, aggregated_calorie_goal, label="Рекомендуемые калории (ккал)", linestyle="--", color="green")

    # График сожженных калорий
    plt.plot(aggregated_dates, aggregated_burned_calories, label="Сожженные калории", marker="o", color="red")

    # Настройка графика
    plt.title(f"Прогресс пользователя {user_id} ({time_period})")
    plt.xlabel("Дата")
    plt.ylabel("Значения")
    plt.legend()
    plt.grid(True)

    # Сохранение графика
    output_path = f"progress_{user_id}_{time_period}.png"
    plt.savefig(output_path)
    plt.close()

    logger.info(
        f"user {user_id} " + f"график построен")

    return output_path

# Прогресс
async def check_history_progress(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data or user_data.get('calorie_goal') == 0:
        await update.message.reply_text("Пожалуйста, настройте профиль с помощью команды /set_profile.")
        return

    # Extract the time period from the command
    if len(context.args) == 0:
        time_period = "day"
    else:
        time_period = context.args[0].lower()
        #await update.message.reply_text("Пожалуйста, укажите: /check_history_progress <day, week, month или year>.")
        #return

    if time_period not in ["day", "week", "month", "year"]:
        await update.message.reply_text("Неверный период. Выберите day, week, month или year.")
        return

    dates, water, calories, water_goal, calorie_goal, burned_calories = users.get_user_history(user_id, time_period)
    if not dates:
        await update.message.reply_text("Нет данных для отображения прогресса.")
        return

    logger.info(
        f"user {user_id} " + f"история")

    graph_path = plot_progress(user_id, dates, water, calories, water_goal, calorie_goal, burned_calories, time_period)

    # Отправка графика пользователю
    with open(graph_path, "rb") as graph_file:
        await update.message.reply_photo(graph_file)

    # Удаление временного файла
    os.remove(graph_path)
