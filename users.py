"""
This module contains the `Users` class to manage user data in memory

It includes methods to:
- Add, update, and retrieve user data.
- Reset daily activity logs.
- Remove inactive users from memory.
- Initialize user data with default values.

The module works with in-memory data storage and communicates with an external database
"""
import datetime
import threading
from logging_config import logger
from db_utils import get_user_db, update_user_db, get_user_history_db

class Users:
    """
    A class to manage user data in memory and synchronize it with a database.

    Attributes:
        users (dict): A dictionary to store user data in memory.
         lock (threading.Lock): A lock to ensure thread-safe operations on user data.
    """
    def __init__(self):
        """
                Initializes the Users class with an empty dictionary for user data
                and a threading lock for thread-safe operations.
        """
        self.users = {}
        self.lock = threading.Lock()

    def reset_user_acvitities(self, user_id, user_data):
        """
                Resets daily user activities if the current date has changed.

                Args:
                    user_id (str): The unique identifier of the user.
                    user_data (dict): The user's data dictionary.

                Returns:
                    dict: Updated user data with reset daily activities.
        """
        now = datetime.datetime.now()
        current_day = now.date().strftime('%Y-%m-%d')
        if user_data['current_date'] and user_data['current_date'] != current_day:
            user_data['logged_water'] = 0
            user_data['logged_calories'] = 0
            user_data['burned_calories'] = 0
            user_data['current_date'] = current_day
            logger.info("User %s reset daily logs: water, calories, "
                        "burned calories for current date %s", user_id, current_day)

        return  user_data

    def get_user_history(self, user_id, time_period):
        """
        Retrieves the user's history data for a given time period.

        Args:
            user_id (str): The unique identifier of the user.
            time_period (str): The time period for retrieving history.

        Returns:
            dict: User history data for the specified time period.
        """
        return  get_user_history_db(user_id, time_period)

    def get(self, user_id):
        """
        Retrieves user data from memory or database. Resets daily activities if needed.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict or None: The user's data if found, otherwise None.
        """
        with self.lock:
            user_data = self.users.get(user_id)
            if user_data:
                user_data['last_active'] = datetime.datetime.now()
                logger.info("User %s found in memory with data: %s", user_id, user_data)
            else:
                # Try to fetch the user data from the database
                user_data = get_user_db(user_id)
                if user_data:
                    # Update the in-memory storage with the fetched user data
                    user_data['last_active'] = datetime.datetime.now()
                    logger.info("User %s found in db with data: %s", user_id, user_data)
                    self.users[user_id] = user_data
                else:
                    #init user
                    #user_data = self.initialize_user_data()
                    #user_data['last_active'] = datetime.datetime.now()
                    logger.info("No User %s found in: %s", user_id, user_data)
                    #self.users[user_id] = user_data
                    return user_data
            user_data = self.reset_user_acvitities(user_id, user_data)
            return user_data

    def add(self, user_id, user_data):
        """
        Adds a new user to the in-memory storage.

        Args:
            user_id (str): The unique identifier of the user.
            user_data (dict): The user's data to be added.
        """
        with self.lock:
            logger.info("User %s added to memory: %s", user_id, user_data)
            self.users[user_id] = user_data

    def update(self, user_id, db_update = 0, **kwargs):
        """
        Updates user data in memory and optionally synchronizes it with the database.

        Args:
            user_id (str): The unique identifier of the user.
            db_update (int): Flag to indicate if the update should be saved to the database
            **kwargs: Additional data fields to update.
        """
        with self.lock:
            # Fetch user data from memory, or initialize a new entry if not found
            user_data = self.users.get(user_id, {'last_active': datetime.datetime.now()})

            # Update specific fields in the user data
            user_data.update(kwargs)

            now = datetime.datetime.now()
            current_day = now.date()
            # Always update the `last_active` timestamp
            user_data['last_active'] = now
            #if user_data['last_active']:
            #    user_data['last_active'] = current_day

            if not user_data['current_date']:
                user_data['current_date'] = current_day

            # Save the updated user data back to the in-memory dictionary
            self.users[user_id] = user_data
            logger.info("User %s updated with data: %s", user_id, user_data)
            if db_update == 1:
                update_user_db(user_id, user_data)
                logger.info("User %s updated in db: %s", user_id, user_data)

    def remove_inactive_users(self):
        """
        Removes users who have been inactive for more than one day from memory.
        """
        with self.lock:
            now = datetime.datetime.now()
            inactive_users = [
                user_id for user_id, data in self.users.items()
                if (now - data['last_active']).days > 1
            ]
            for user_id in inactive_users:
                user_data = self.users.get(user_id)  # Access user data before deletion
                if user_data:
                    logger.info("User %s removed from memory: %s", user_id, user_data)
                del self.users[user_id]
                logger.info("User %s removed from memory due to inactivity.", user_id)

    def initialize_user_data(self):
        """
        Initializes a new user data dictionary with default values.

        Returns:
            dict: A dictionary with default user data fields and values.
        """
        # Используем setdefault только для отсутствующих ключей, не затираем существующие данные
        user_data = {}
        user_data.setdefault('weight', 0)
        user_data.setdefault('height', 0)
        user_data.setdefault('age', 0)
        user_data.setdefault('gender', '')
        user_data.setdefault('activity', 0)
        user_data.setdefault('city', '')
        user_data.setdefault('water_goal', 0)
        user_data.setdefault('calorie_goal', 0)
        user_data.setdefault('logged_water', 0)
        user_data.setdefault('logged_calories', 0)
        user_data.setdefault('burned_calories', 0)
        user_data.setdefault('current_date', None)
        return user_data

# Словарь для хранения данных пользователей
users = Users()