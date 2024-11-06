# bank.py
from database import db_query, db_transaction
from datetime import datetime
from decimal import Decimal
import logging
from typing import Optional, List, Dict
import uuid


class BankServices:
    def __init__(self, username: str, account_number: int):
        self.__username = username
        self.__account_number = account_number

    def balance_enquiry(self) -> Optional[Decimal]:
        """Get current balance for the account"""
        try:
            result = db_query(
                "SELECT balance FROM customers WHERE username = %s AND status = 1",
                (self.__username,)
            )

            if result:
                balance = result[0][0]
                print(f"\nCurrent balance: ${balance:,.2f}")
                return balance
            else:
                print("\nUnable to retrieve balance. Please contact support.")
                return None

        except Exception as e:
            logging.error(f"Balance enquiry failed: {str(e)}")
            print("\nFailed to retrieve balance. Please try again.")
            return None

    def deposit(self, amount: float) -> bool:
        """Deposit money into the account"""
        try:
            with db_transaction() as conn:
                cursor = conn.cursor(prepared=True)

                # Create transaction record
                transaction_id = str(uuid.uuid4())
                transaction_query = """
                    INSERT INTO transactions 
                    (transaction_id, from_account, amount, transaction_type, status)
                    VALUES (%s, %s, %s, 'deposit', 'completed')
                """
                cursor.execute(transaction_query, (
                    transaction_id,
                    self.__account_number,
                    amount
                ))

                # Update balance
                update_query = """
                    UPDATE customers 
                    SET balance = balance + %s 
                    WHERE username = %s AND status = 1
                """
                cursor.execute(update_query, (amount, self.__username))

                if cursor.rowcount:
                    print(f"\nSuccessfully deposited ${amount:,.2f}")
                    self.balance_enquiry()
                    return True
                else:
                    print("\nDeposit failed. Please try again.")
                    return False

        except Exception as e:
            logging.error(f"Deposit failed: {str(e)}")
            print("\nFailed to process deposit. Please try again.")
            return False

    def withdraw(self, amount: float) -> bool:
        """Withdraw money from the account"""
        try:
            # Check balance first
            current_balance = self.balance_enquiry()
            if not current_balance or current_balance < Decimal(str(amount)):
                print("\nInsufficient balance.")
                return False

            with db_transaction() as conn:
                cursor = conn.cursor(prepared=True)

                # Create transaction record
                transaction_id = str(uuid.uuid4())
                transaction_query = """
                    INSERT INTO transactions 
                    (transaction_id, from_account, amount, transaction_type, status)
                    VALUES (%s, %s, %s, 'withdrawal', 'completed')
                """
                cursor.execute(transaction_query, (
                    transaction_id,
                    self.__account_number,
                    amount
                ))

                # Update balance
                update_query = """
                    UPDATE customers 
                    SET balance = balance - %s 
                    WHERE username = %s AND status = 1 
                    AND balance >= %s
                """
                cursor.execute(update_query, (amount, self.__username, amount))

                if cursor.rowcount:
                    print(f"\nSuccessfully withdrew ${amount:,.2f}")
                    self.balance_enquiry()
                    return True
                else:
                    print("\nWithdrawal failed. Please try again.")
                    return False

        except Exception as e:
            logging.error(f"Withdrawal failed: {str(e)}")
            print("\nFailed to process withdrawal. Please try again.")
            return False

    def fund_transfer(self, receiver_account: int, amount: float) -> bool:
        """Transfer money to another account"""
        try:
            # Verify receiver account exists and is active
            receiver_query = """
                SELECT username, status 
                FROM customers 
                WHERE account_number = %s
            """
            receiver = db_query(receiver_query, (receiver_account,))

            if not receiver or not receiver[0][1]:
                print("\nInvalid receiver account number.")
                return False

            # Check sufficient balance
            current_balance = self.balance_enquiry()
            if not current_balance or current_balance < Decimal(str(amount)):
                print("\nInsufficient balance.")
                return False

            with db_transaction() as conn:
                cursor = conn.cursor(prepared=True)

                # Create transaction record
                transaction_id = str(uuid.uuid4())
                transaction_query = """
                    INSERT INTO transactions 
                    (transaction_id, from_account, to_account, amount, 
                     transaction_type, status)
                    VALUES (%s, %s, %s, %s, 'transfer', 'completed')
                """
                cursor.execute(transaction_query, (
                    transaction_id,
                    self.__account_number,
                    receiver_account,
                    amount
                ))

                # Update sender balance
                sender_update = """
                    UPDATE customers 
                    SET balance = balance - %s 
                    WHERE username = %s AND status = 1 
                    AND balance >= %s
                """
                cursor.execute(sender_update, (
                    amount,
                    self.__username,
                    amount
                ))

                # Update receiver balance
                receiver_update = """
                    UPDATE customers 
                    SET balance = balance + %s 
                    WHERE account_number = %s AND status = 1
                """
                cursor.execute(receiver_update, (amount, receiver_account))

                print(f"\nSuccessfully transferred ${amount:,.2f} to account {receiver_account}")
                self.balance_enquiry()
                return True

        except Exception as e:
            logging.error(f"Fund transfer failed: {str(e)}")
            print("\nFailed to process transfer. Please try again.")
            return False

    def show_transaction_history(self, limit: int = 10):
        """Show recent transactions for the account"""
        try:
            query = """
                SELECT 
                    created_at,
                    transaction_type,
                    amount,
                    CASE 
                        WHEN transaction_type = 'transfer' AND from_account = %s 
                        THEN CONCAT('Transfer to ', to_account)
                        WHEN transaction_type = 'transfer' AND to_account = %s 
                        THEN CONCAT('Transfer from ', from_account)
                        ELSE transaction_type
                    END as description,
                    status
                FROM transactions
                WHERE from_account = %s OR to_account = %s
                ORDER BY created_at DESC
                LIMIT %s
            """

            transactions = db_query(query, (
                self.__account_number,
                self.__account_number,
                self.__account_number,
                self.__account_number,
                limit
            ))

            if not transactions:
                print("\nNo transactions found.")
                return

            print("\nRecent Transactions:")
            print("-" * 80)
            print(f"{'Date':<20} {'Type':<12} {'Amount':>12} {'Description':<25} {'Status':<10}")
            print("-" * 80)

            for txn in transactions:
                date = txn[0].strftime("%Y-%m-%d %H:%M")
                txn_type = txn[1].capitalize()
                amount = f"${txn[2]:,.2f}"
                description = txn[3].capitalize()
                status = txn[4].capitalize()

                print(f"{date:<20} {txn_type:<12} {amount:>12} {description:<25} {status:<10}")

            print("-" * 80)

        except Exception as e:
            logging.error(f"Failed to retrieve transaction history: {str(e)}")
            print("\nFailed to retrieve transaction history. Please try again.")