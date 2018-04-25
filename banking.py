import MySQLdb
import datetime

class Banking():
    def __init__(self):
        self.conn = MySQLdb.connect("localhost", "root", "", "Bank")
        self.cur = self.conn.cursor()
        try:
            self.total = self.cur.execute("SELECT * FROM account")
            self.total_transactions = self.cur.execute("SELECT * FROM transactions")
        except Exception:
            """
            If there is no table  create one
            status in table is for to check if account is closed.
            open account  satus = 1
            closed account status = -1
            for savings account-> account_type = 1
            for current account-> account_type = 2
            transaction_type = 1 -> Deposit
            transaction_type = 2 -> Transfer
            transaction_type = 3 -> Withdraw
            """
            create_account_table_query = """
            CREATE TABLE account (account_number int PRIMARY KEY AUTO_INCREMENT,
            name varchar(30), address varchar(350), account_type int,  closing_month varchar(50),
            last_name varchar(50), address2 varchar(350), city varchar(100), state varchar(100),
            pincode int, balance float, password varchar(100), status int)
            """
            create_transactions_table_query = """
            CREATE TABLE transactions (account_number int, amount int,
            transaction_month varchar(30),
            transaction_type int,  FOREIGN KEY (account_number) REFERENCES account(account_number))
            """
            self.cur.execute(create_account_table_query)
            self.cur.execute(create_transactions_table_query)
            self.conn.commit()

    def on_exit(self):
        self.conn.close()

    def open_account(self, name, address, initial_balance, password, account_type, last_name, address2, city, state, pincode):
        # status is 1 for open acount
        if account_type == 2:
            if initial_balance < 5000:
                print("Enter amount more than 5000")
                print("Account creation failed")
                return 0
        print("openning")
        self.cur.execute("INSERT INTO account  (name, address, account_type,"
                         "closing_month,last_name, address2, city, state,"
                         " pincode,  balance, password, status)"
                         " VALUES(%s, %s, %s, %s, %s, %s,  %s, %s, %s, %s, %s, %s)",
                         (name, address, account_type, '-1', last_name,
                          address2, city, state, pincode, initial_balance,
                          password, 1))
        try:
            self.total += 1
            self.conn.commit()
            return self.total
        except Exception as err:
            print("Exception %s occured"%(err))
            self.conn.rollback()
            return -1

    def closed_account_history(self):
        month_range = str(input("Enter the month number for which data is needed Ex: 1 for January "))
        while True:
            try:
                month_range = int(month_range)
                if month_range > 12 or month_range < 1:
                    1/0
                else:
                    rows = self.cur.execute("SELECT * FROM account WHERE status"
                                            " = 0 and closing_month = %s", (str(month_range),))
                    if rows == 0:
                        print("No data for this month")
                    else:
                        for i in range(rows):
                            user_data = self.cur.fetchone()
                            try:
                                print("Accout Number: {acc_no} | Name: {name}"
                                      "| Closing Month: {closing_month} | "
                                      "Balance: {bal}".format(acc_no=user_data[0],
                                                              name=user_data[1],
                                                              closing_month=user_data[2],
                                                              bal=user_data[5]))
                            except Exception:
                                pass
                    break
            except Exception:
                month_range = str(input("Enter valid month number"))

    def login(self, account_number, password):
        incorrect_attempts = 0
        while True:
            rows = self.cur.execute("SELECT * FROM account "
                                    " WHERE account_number = %s",
                                    (account_number,))
            user_data = self.cur.fetchone()
            if rows == 0 or user_data[-1] == 0:
                print("Account not found check your account_number\n")
                return -1
            else:
                if user_data[-2] == password:
                    print("You are logged in now...\n")
                    while(True):
                        self.cur.execute("SELECT * FROM account WHERE"
                                         " account_number = %s", (account_number,))
                        user_data = self.cur.fetchone()
                        print("\n 1. Address Change\n 2. Money Deposit\n"
                              "3. Money Withdraw\n 4. Print Statement \n"
                              "5. Transfer Money\n 6. Account Closure\n "
                              "7. Go to Main menu\n")
                        choice = int(input())
                        if choice == 1:
                            new_address = str(input("Enter new address  "))
                            try:
                                self.cur.execute("UPDATE account SET address "
                                                 "= %s  WHERE account_number = %s",
                                                 (new_address, account_number))
                                self.conn.commit()
                                print("Address updated sucessfully.\n")
                            except Exception as e:
                                print("Failed\n")
                        elif choice == 2:
                            # Money Deposit
                            month = str(datetime.datetime.now()).split()[0].split('-')[1]
                            try:
                                deposit_amount = int(input("Enter the amount  "))
                                bal = user_data[-3]
                                self.cur.execute("UPDATE account SET balance = "
                                                 "%s  WHERE account_number = %s",
                                                 (bal + deposit_amount, account_number))
                                self.conn.commit()
                                print("Amount credited new balance: {}\n".format(bal + deposit_amount))
                                self.cur.execute("INSERT INTO transactions  "
                                                 "(account_number, amount,  transaction_month, transaction_type)"
                                                 " VALUES(%s, %s, %s, %s)",
                                                 (account_number, deposit_amount, month, 1))
                                self.conn.commit()
                            except ValueError:
                                print("Enter proper value")
                            except Exception as e:
                                print("Failed {}".format(str(e)))
                        elif choice == 3:
                            # Money Withdraw
                            month = str(datetime.datetime.now()).split()[0].split('-')[1]
                            rows = self.cur.execute("SELECT * FROM transactions WHERE (account_number = %s and "
                                                    "transaction_month = %s and transaction_type = 3) ",
                                                    (account_number, month))
                            if rows >= 10 and user_data[4] == 1:
                                print("You have reached limit of 10 withdrawals this month.")
                            else:
                                try:
                                    withdraw_amount = int(input("Enter the amount  "))
                                    bal = user_data[-3]
                                    if withdraw_amount <= bal:
                                        self.cur.execute("UPDATE account SET balance = %s  WHERE account_number"
                                                         " = %s", (bal - withdraw_amount, account_number))
                                        self.conn.commit()
                                        print("Address debited new balance: {}\n".format(bal - withdraw_amount))
                                        self.cur.execute("INSERT INTO transactions  (account_number, amount, "
                                                         " transaction_month, transaction_type) VALUES(%s, %s, %s, %s)" ,
                                                         (account_number, withdraw_amount, month, 3))
                                        self.conn.commit()
                                    else:
                                        print("Enter amount less than {balance}\n".format(balance=bal))
                                except ValueError:
                                    print("Enter proper value")
                                except Exception as e:
                                    print("Failed {}".format(str(e)))
                        elif choice == 4:
                            # account statement
                            print("Your Account Statement:")
                            rows = self.cur.execute("SELECT * FROM transactions WHERE account_number = %s", (account_number,))
                            transaction_type_dist = {1: 'Deposit', 2: 'Transfer', 3: 'Withdraw'}
                            if rows <= 5:
                                for i in range(rows):
                                    user_data = self.cur.fetchone()
                                    print("Account Number: {account_number} | Name: {name} | Amount: {amt} | Transaction: "
                                          "{trans_type}".format(account_number=user_data[0], name=user_data[1], 
                                                                amt=user_data[3], trans_type=transaction_type_dist[user_data[-1]],))
                            else:
                                for i in range(rows - 6):
                                    user_data = self.cur.fetchone()
                                for i in range(5):
                                    user_data = self.cur.fetchone()
                                    print("Account Number: {account_number} | Name: {name} | "
                                          " Amount: {amt} | Transaction: {trans_type}".format(account_number=user_data[0],
                                                                                              name=user_data[1], 
                                                                                              amt=user_data[3], 
                                                                                              trans_type=transaction_type_dist[user_data[-1]],))
                        elif choice == 5:
                            # Transfer Money
                            bal = user_data[-3]
                            month = str(datetime.datetime.now()).split()[0].split('-')[1]
                            try:
                                benificier_account_number = int(input("Enter the benificier's account number  "))
                                rows = self.cur.execute("SELECT * FROM account WHERE account_number = %s", (benificier_account_number,))
                                if rows == 0:
                                    print("Account not found check benificier's account_number\n")
                                else:
                                    receiver_details = self.cur.fetchone()
                                    print("Sending Money to {name}".format(name=receiver_details[1]))
                                    if int(input("Enter 1 to continue.  ")) == 1:
                                        transfer_amount = int(input("Enter the amount  "))
                                        if transfer_amount <= bal:
                                            self.cur.execute("UPDATE account SET balance = %s  WHERE account_number = %s",
                                                             (bal - transfer_amount, account_number))
                                            self.cur.execute("UPDATE account SET balance = %s  WHERE account_number = %s", 
                                                             (bal + transfer_amount, benificier_account_number))
                                            self.conn.commit()
                                            print("Amount transfered new balance: {new_bal}\n".format(new_bal=(bal - transfer_amount)))
                                            self.cur.execute("INSERT INTO transactions  (account_number, amount,"
                                                             " transaction_month, transaction_type) VALUES(%s, %s, %s, %s)" ,
                                                             (account_number, transfer_amount, month, 2))
                                            self.conn.commit()
                                        else:
                                            print("Enter amount less than {balance}\n".format(balance=bal))
                                    else:
                                        print("Transaction cancelled sucessfully")
                            except ValueError as e:
                                print("Enter proper value")
                        elif choice == 6:
                            # Account closure
                            bal = user_data[-3]
                            print("Are you sure you want to close account? \n")
                            if int(input("Enter 1 to continue.. ")) == 1:
                                month = str(int(str(datetime.datetime.now()).split()[0].split('-')[1]))
                                self.cur.execute("UPDATE account SET status = 0,"
                                                 " balance = 0, closing_month = {month__}"
                                                 " WHERE account_number ="
                                                 "{acc_no}".format(month__=month,
                                                                   acc_no=account_number,))
                                self.conn.commit()
                                print("Collect your balance {balance}".format(balance=bal))
                                print("Account closed")
                                break
                            else:
                                print("Request to close account cancelled")
                        elif choice == 7:
                            break
                    return 0
                else:
                    incorrect_attempts += 1
                    if incorrect_attempts >= 3:
                        print("Maximum incorrect attempts reached\n Account Closing\n")
                        month = str(int(str(datetime.datetime.now()).split()[0].split('-')[1]))
                        self.cur.execute("UPDATE account SET status = 0,"
                                         "closing_month = %s WHERE account_number = %s",
                                         (month, account_number,))
                        self.conn.commit()
                        return -1
                    else:
                        try:
                            choice = int(input("Incorrect username or password"
                                               "\n 1. Try Again\n 2. Go back to main menu\n"))
                            if choice == 1:
                                account_number = str(input("Enter the account number: ")) 
                                password = str(input("Enter the password: "))
                            elif choice == 2:
                                return -1
                            else:
                                print("Enter proper value")
                        except ValueError:
                            print("Enter proper value")

    def admin_login(self, admin_id, password):
        if admin_id == "admin" and password == "admin":
            while(True):
                print("\n 1. Print closed accounts history\n 2. Go back to main menu\n")
                choice = int(input())
                if choice == 1:
                    # print closed account history
                    self.closed_account_history()
                elif choice == 2:
                    break
            return 0
        else:
            print("Incorrect user name or password")
            return -1

if __name__ == '__main__':
    banking = Banking()
    print("Connection Established")
    # To be executed ONCE and then must be commented out
    while True:
        print("\n 1. Sign Up\n 2. Sign In\n 3. Admin Sign In\n 4. Quit")
        choice = int(input())
        if choice == 1:
            # creating new account here
            try:
                name = str(input("Enter your first name  "))
                last_name = str(input("Enter your last name  "))
                address = str(input("Enter the address  "))
                address2 = str(input("Enter the second address  "))
                city = str(input("Enter the city name  "))
                state = str(input("Enter the state name  "))
                pincode = int(input("Enter the pincode  "))
                while True:
                    if len(str(pincode)) != 6:
                        print("Pincode must be equal to 6 digits")
                        pincode = int(input("Enter the pincode"))
                    else:
                        break
                account_type = 0
                while True:
                    account_type = int(input("Enter the Account type :"
                                             " \n1. Savings Account \n"
                                             "2. Current Account\n"))
                    if account_type != 1 and account_type != 2:
                        print("Enter proper value")
                    else:
                        break
                initial_balance = int(input("Entert the inital balance  "))
                password = str(input("Enter the password  "))
                while len(password) < 8:
                    print("Password must have minimum 8 characters")
                    password = str(input("Enter the password  "))
                account_number = banking.open_account(name, address,
                                                      initial_balance,
                                                      password, account_type,
                                                      last_name, address2,
                                                      city, state, pincode)
                if account_number == -1:
                    print("Some Exception occured")
                elif account_number != 0:
                    print("Account created sucessfully\n"
                          "Your Account Number is: %s"%(account_number))
            except Exception:
                print("Please enter proper value")
        elif choice == 2:
            try:
                while(True):
                    account_number = str(input("Enter your accout number  "))
                    password = str(input("Enter your password   "))
                    status = banking.login(account_number, password)
                    if status == 0 or status == -1:
                        break
            except Exception:
                print("Please enter proper value")
        elif choice == 3:
            # Admin Login
            # admin_id = "admin" , password = "admin"
            try:
                while(True):
                    admin_id = str(input("Enter your admin id  "))
                    password = str(input("Enter your password   "))
                    status = banking.admin_login(admin_id, password)
                    if status == 0:
                        break
            except Exception:
                print("Please enter proper value")
        elif choice == 4:
            break
