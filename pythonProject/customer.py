# customer.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import bcrypt
from typing import Optional
import json
import logging
from database import db_query, db_transaction


@dataclass
class CustomerDTO:
    username: str
    name: str
    age: int
    city: str
    account_number: int
    balance: Decimal = Decimal('0.00')
    status: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Customer:
    def __init__(self, username: str, password: str, name: str, age: int,
                 city: str, account_number: int):
        self.validate_input(username, password, name, age, city)
        self.__username = username
        self.__password_hash = self._hash_password(password)
        self.__name = name
        self.__age = age
        self.__city = city
        self.__account_number = account_number

    @staticmethod
    def validate_input(username: str, password: str, name: str, age: int, city: str):
        if not all([username, password, name, city]):
            raise ValueError("All fields must be non-empty")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if age < 18:
            raise ValueError("Customer must be at least 18 years old")
        if not username.isalnum():
            raise ValueError("Username must be alphanumeric")

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def create_user(self) -> bool:
        try:
            with db_transaction() as conn:
                cursor = conn.cursor(prepared=True)

                # Insert customer record
                insert_query = """
                    INSERT INTO customers 
                    (username, password_hash, name, age, city, account_number)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    self.__username,
                    self.__password_hash,
                    self.__name,
                    self.__age,
                    self.__city,
                    self.__account_number
                ))

                # Log the creation
                audit_query = """
                    INSERT INTO audit_log (user_id, action, details)
                    VALUES (LAST_INSERT_ID(), 'account_created', %s)
                """
                audit_details = {
                    'username': self.__username,
                    'name': self.__name,
                    'age': self.__age,
                    'city': self.__city,
                    'account_number': self.__account_number
                }
                cursor.execute(audit_query, (json.dumps(audit_details),))

                return True

        except Exception as e:
            logging.error(f"Failed to create user: {str(e)}")
            return False

    @staticmethod
    def get_customer_by_username(username: str) -> Optional[CustomerDTO]:
        try:
            query = """
                SELECT username, name, age, city, account_number, balance, 
                       status, created_at, updated_at
                FROM customers
                WHERE username = %s AND status = 1
            """
            result = db_query(query, (username,))

            if not result:
                return None

            return CustomerDTO(*result[0])

        except Exception as e:
            logging.error(f"Failed to retrieve customer: {str(e)}")
