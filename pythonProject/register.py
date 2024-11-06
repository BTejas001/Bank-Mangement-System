# register.py
from customer import Customer
from database import db_query, db_transaction
import secrets
import logging
from typing import Optional, Tuple
import re


class AccountManager:
    MIN_PASSWORD_LENGTH = 8
    ACCOUNT_NUMBER_LENGTH = 10

    @staticmethod
    def generate_account_number() -> int:
        """Generate a secure random account number"""
        while True:
            # Generate a random number with proper length
            account_number = int(''.join([str(secrets.randbelow(10))
                                          for _ in range(AccountManager.ACCOUNT_NUMBER_LENGTH)]))

            # Check if it already exists
            result = db_query(
                "SELECT 1 FROM customers WHERE account_number = %s",
                (account_number,)
            )

            if not result:
                return account_number

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, message)
        """
        if len(password) < AccountManager.MIN_PASSWORD_LENGTH:
            return False, "Password must be at least 8 characters long"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, "Password is strong"

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username
        Returns: (is_valid, message)
        """
        if not 3 <= len(username) <= 30:
            return False, "Username must be between 3 and 30 characters"

        if not username.isalnum():
            return False, "Username must contain only letters and numbers"

        result = db_query("SELECT 1 FROM customers WHERE username = %s", (username,))
        if result:
            return False, "Username already exists"

        return True, "Username is available"


class UserAuthentication:
    @staticmethod
    def sign_up() -> Optional[Customer]:
        try:
            # Get and validate username
            while True:
                username = input("Create Username: ").strip()
                is_valid, message = AccountManager.validate_username(username)
                if is_valid:
                    break
                print(message)

            # Get and validate password
            while True:
                password = input("Enter Password: ").strip()
                is_valid, message = AccountManager.validate_password(password)
                if is_valid:
                    break
                print(message)

            # Get user details
            name = input("Enter Your Name: ").strip()
            while True:
                try:
                    age = int(input("Enter Your Age: "))
                    if age >= 18:
                        break
                    print("Must be at least 18 years old")
                except ValueError:
                    print("Please enter a valid age")

            city = input("Enter Your City: ").strip()

            # Generate account number
            account_number = AccountManager.generate_account_number()
            print(f"Your Account Number: {account_number}")

            # Create customer
            customer = Customer(username, password, name, age, city, account_number)
            if customer.create_user():
                logging.info(f"New user created: {username}")
                return customer
            else:
                logging.error(f"Failed to create user: {username}")
                return None

        except Exception as e:
            logging.error(f"Sign up failed: {str(e)}")
            print("An error occurred during sign up. Please try again.")
            return None

    @staticmethod
    def sign_in() -> Optional[str]:
        try:
            max_attempts = 3
            attempts = 0

            while attempts < max_attempts:
                username = input("Enter Username: ").strip()
                password = input("Enter Password: ").strip()

                query = "SELECT password_hash FROM customers WHERE username = %s AND status = 1"
                result = db_query(query, (username,))

                if result and Customer.verify_password(password, result[0][0]):
                    logging.info(f"Successful login: {username}")
                    return username

                attempts += 1
                remaining = max_attempts - attempts
                print(f"Invalid credentials. {remaining} attempts remaining.")

            logging.warning(f"Account locked due to multiple failed attempts: {username}")
            print("Too many failed attempts. Please try again later.")
            return None

        except Exception as e:
            logging.error(f"Sign in failed: {str(e)}")
            print("An error occurred during sign in. Please try again.")
            return None