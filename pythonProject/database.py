# database.py
import mysql.connector as sql
from mysql.connector.pooling import MySQLConnectionPool
from contextlib import contextmanager
import os
from typing import Any, List, Optional
import logging
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()


class DatabaseConfig:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME', 'bank'),
            'pool_name': 'bank_pool',
            'pool_size': 5
        }

        # Validate configuration
        if not self.config['password']:
            raise ValueError("Database password not set in environment variables")


class DatabaseConnection:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._setup_pool()
        return cls._instance

    @classmethod
    def _setup_pool(cls):
        try:
            config = DatabaseConfig().config
            cls._pool = MySQLConnectionPool(**config)
            logging.info("Database connection pool created successfully")
        except Exception as e:
            logging.error(f"Failed to create database pool: {str(e)}")
            raise

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
        except Exception as e:
            logging.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self):
        with self.get_connection() as conn:
            cursor = conn.cursor(prepared=True)
            try:
                yield cursor
            finally:
                cursor.close()


def db_query(query: str, params: tuple = None) -> List[Any]:
    db = DatabaseConnection()
    with db.get_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


@contextmanager
def db_transaction():
    db = DatabaseConnection()
    with db.get_connection() as conn:
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Transaction failed: {str(e)}")
            raise


def init_database():
    """Initialize database tables with proper constraints and indices"""
    try:
        # Create customers table with proper constraints
        db_query("""
            CREATE TABLE IF NOT EXISTS customers (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash CHAR(60) NOT NULL,
                name VARCHAR(100) NOT NULL,
                age INTEGER CHECK (age >= 18),
                city VARCHAR(100) NOT NULL,
                balance DECIMAL(15,2) DEFAULT 0.00,
                account_number BIGINT UNIQUE NOT NULL,
                status BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username),
                INDEX idx_account_number (account_number)
            ) ENGINE=InnoDB;
        """)

        # Create transactions table
        db_query("""
            CREATE TABLE IF NOT EXISTS transactions (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                transaction_id CHAR(36) UNIQUE NOT NULL,
                from_account BIGINT NOT NULL,
                to_account BIGINT,
                amount DECIMAL(15,2) NOT NULL,
                transaction_type ENUM('deposit', 'withdrawal', 'transfer') NOT NULL,
                status ENUM('pending', 'completed', 'failed') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_account) REFERENCES customers(account_number),
                FOREIGN KEY (to_account) REFERENCES customers(account_number),
                INDEX idx_transaction_id (transaction_id),
                INDEX idx_from_account (from_account),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB;
        """)

        # Create audit log table
        db_query("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                action VARCHAR(100) NOT NULL,
                details JSON,
                ip_address VARCHAR(45),
                user_agent VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES customers(id),
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB;
        """)

        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    init_database()