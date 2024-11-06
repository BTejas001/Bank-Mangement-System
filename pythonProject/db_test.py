# db_test.py
from database import db_query, init_database
import logging

logging.basicConfig(level=logging.INFO)


def test_database_connection():
    try:
        # Test database connection
        result = db_query("SELECT 1")
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False


def check_tables():
    try:
        # Check if tables exist
        tables = ['customers', 'transactions', 'audit_log']
        for table in tables:
            result = db_query(f"SHOW TABLES LIKE '{table}'")
            if result:
                print(f"Table '{table}' exists")
            else:
                print(f"Table '{table}' does not exist")
    except Exception as e:
        print(f"Error checking tables: {str(e)}")


if __name__ == "__main__":
    print("Testing database connection and setup...")
    if test_database_connection():
        print("\nInitializing database tables...")
        try:
            init_database()
            print("Database initialization successful!")
        except Exception as e:
            print(f"Database initialization failed: {str(e)}")

        print("\nChecking tables...")
        check_tables()