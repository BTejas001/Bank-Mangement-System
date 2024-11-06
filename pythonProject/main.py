# main.py
from register import UserAuthentication
from bank import BankServices
from database import db_query
import logging
import sys
from typing import Optional


class BankingApplication:
    def __init__(self):
        self.auth = UserAuthentication()
        self.current_user = None
        self.account_number = None

    def display_welcome(self):
        print("\n=== Welcome to Modern Banking System ===")
        print("1. Sign Up")
        print("2. Sign In")
        print("3. Exit")

    def display_services(self):
        print(f"\nWelcome {self.current_user.capitalize()}")
        print("Available Banking Services:")
        print("1. Balance Enquiry")
        print("2. Cash Deposit")
        print("3. Cash Withdrawal")
        print("4. Fund Transfer")
        print("5. Transaction History")
        print("6. Sign Out")

    def handle_auth(self) -> bool:
        while True:
            try:
                self.display_welcome()
                choice = input("\nPlease select an option (1-3): ").strip()

                if choice == "1":
                    if self.auth.sign_up():
                        print("\nAccount created successfully! Please sign in.")
                    else:
                        print("\nFailed to create account. Please try again.")

                elif choice == "2":
                    username = self.auth.sign_in()
                    if username:
                        self.current_user = username
                        self.account_number = self._get_account_number()
                        return True

                elif choice == "3":
                    print("\nThank you for using Modern Banking System. Goodbye!")
                    sys.exit(0)

                else:
                    print("\nInvalid choice. Please select 1, 2, or 3.")

            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                sys.exit(0)

            except Exception as e:
                logging.error(f"Authentication error: {str(e)}")
                print("\nAn error occurred. Please try again.")

    def _get_account_number(self) -> Optional[int]:
        try:
            result = db_query(
                "SELECT account_number FROM customers WHERE username = %s",
                (self.current_user,)
            )
            return result[0][0] if result else None
        except Exception as e:
            logging.error(f"Failed to get account number: {str(e)}")
            return None

    def handle_banking_services(self):
        bank_service = BankServices(self.current_user, self.account_number)

        while True:
            try:
                self.display_services()
                choice = input("\nPlease select a service (1-6): ").strip()

                if choice == "1":
                    bank_service.balance_enquiry()

                elif choice == "2":
                    amount = self._get_valid_amount("deposit")
                    if amount:
                        bank_service.deposit(amount)

                elif choice == "3":
                    amount = self._get_valid_amount("withdraw")
                    if amount:
                        bank_service.withdraw(amount)

                elif choice == "4":
                    self._handle_fund_transfer(bank_service)

                elif choice == "5":
                    bank_service.show_transaction_history()

                elif choice == "6":
                    print("\nSign out successful. Thank you for using our services!")
                    self.current_user = None
                    self.account_number = None
                    return

                else:
                    print("\nInvalid choice. Please select 1-6.")

                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\nReturning to main menu...")
                return

            except Exception as e:
                logging.error(f"Banking service error: {str(e)}")
                print("\nAn error occurred. Please try again.")

    def _get_valid_amount(self, transaction_type: str) -> Optional[float]:
        while True:
            try:
                amount = float(input(f"\nEnter amount to {transaction_type}: ").strip())
                if amount <= 0:
                    print("Amount must be greater than 0.")
                    continue
                return amount
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                return None

    def _handle_fund_transfer(self, bank_service: 'BankServices'):
        try:
            receiver_account = int(input("\nEnter receiver's account number: ").strip())
            amount = self._get_valid_amount("transfer")
            if amount:
                bank_service.fund_transfer(receiver_account, amount)
        except ValueError:
            print("Please enter a valid account number.")
        except KeyboardInterrupt:
            print("\nTransfer cancelled.")

    def run(self):
        try:
            while True:
                if not self.current_user:
                    if not self.handle_auth():
                        continue
                self.handle_banking_services()
        except Exception as e:
            logging.error(f"Application error: {str(e)}")
            print("\nAn unexpected error occurred. Please restart the application.")
            sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='banking.log'
    )

    # Run the application
    app = BankingApplication()
    app.run()