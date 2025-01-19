import sqlite3
from datetime import datetime

# Initialize the database
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            weight REAL,
            height REAL,
            age INTEGER,
            gender TEXT,
            activity INTEGER,
            city TEXT,
            water_goal REAL,
            calorie_goal REAL,
            logged_water REAL,
            logged_calories REAL,
            burned_calories REAL,
            current_date DATETIME
        )
    """)

    # Create user_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            weight REAL,
            height REAL,
            age INTEGER,
            gender TEXT,
            activity INTEGER,
            city TEXT,
            water_goal REAL,
            calorie_goal REAL,
            logged_water REAL,
            logged_calories REAL,
            burned_calories REAL,
            current_date DATETIME,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# Retrieve user data
def get_user_db(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        columns = ["user_id", "weight", "height", "age", "gender", "activity", "city", "water_goal", "calorie_goal", "logged_water", "logged_calories", "burned_calories", "current_date"]
        return dict(zip(columns, row))
    return None

# Retrieve user data
def get_user_history_db(user_id, time_period):
    """
    Извлекает данные прогресса пользователя из базы данных.
    """
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Get the current date
    today = datetime.today()

    # Define date ranges for the selection
    if time_period == "day":
        start_date = today
        end_date = today
    elif time_period == "week":
        start_date = today - timedelta(days=today.weekday())  # Start of the current week
        end_date = start_date + timedelta(days=6)  # End of the current week
    elif time_period == "month":
        start_date = today.replace(day=1)  # Start of the current month
        end_date = today.replace(day=28) + timedelta(
            days=4)  # Start of next month, then go back 4 days to get last day of current month
    elif time_period == "year":
        start_date = today.replace(month=1, day=1)  # Start of the current year
        end_date = today.replace(month=12, day=31)  # End of the current year

    # Start of the current day (00:00:00)
    start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)

    # End of the current day (23:59:59)
    end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Format start_date and end_date as YYYY-MM-DD HH:MM:SS
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    # Получение данных из таблицы user_history
    cursor.execute("""
        SELECT logged_at, logged_water, logged_calories, water_goal, calorie_goal, burned_calories
        FROM user_history
        WHERE user_id = ? AND logged_at BETWEEN ? AND ?
        ORDER BY logged_at ASC
    """, (user_id, start_date_str, end_date_str))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return [], [], [], [], [], []

    # Преобразование данных в списки
    dates = [row[0] for row in rows]
    water = [row[1] for row in rows]
    calories = [row[2] for row in rows]
    water_goal = [row[3] for row in rows]
    calorie_goal = [row[4] for row in rows]
    burned_calories = [row[5] for row in rows]

    return dates, water, calories, water_goal, calorie_goal, burned_calories

# Add or update user profile
def update_user_db(user_id, data):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Log the current user data into user_history table
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    current_data = cursor.fetchone()
    if current_data:
        # Insert current data into history before updating
        cursor.execute("""
                INSERT INTO user_history (user_id, weight, height, age, gender, activity, city, water_goal, calorie_goal, logged_water, logged_calories, burned_calories, current_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, current_data)

    cursor.execute("""
        INSERT INTO users (user_id, weight, height, age, gender, activity, city, water_goal, calorie_goal, logged_water, logged_calories, burned_calories, current_date)
        VALUES (:user_id, :weight, :height, :age, :gender, :activity, :city, :water_goal, :calorie_goal, :logged_water, :logged_calories, :burned_calories, :current_date)
        ON CONFLICT(user_id) DO UPDATE SET
            weight=excluded.weight,
            height=excluded.height,
            age=excluded.age,
            gender=excluded.gender,
            activity=excluded.activity,
            city=excluded.city,
            water_goal=excluded.water_goal,
            calorie_goal=excluded.calorie_goal,
            logged_water=excluded.logged_water,
            logged_calories=excluded.logged_calories,
            burned_calories=excluded.burned_calories,
            current_date=excluded.current_date
    """, {**data, "user_id": user_id})
    conn.commit()
    conn.close()
