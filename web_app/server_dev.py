# build email server to send emails for account recovery
# replace phone numbers with email addresses, change hash table so it contains email addresses and not hash values
# create function to validate email addresses
# change /forgot page
# add a function to generate code for account recovery
# request confirmation with email for account creation
# add ssl encryption
# create enum for response codes / several final variables (important to remove repeated use of numbers)


# imports
import http.server
from http.server import BaseHTTPRequestHandler
import socket
import cgi
import datetime
import random
import numpy as np
from forex_python.converter import CurrencyRates
import smtplib


# classes
class Log:  # object properties: log (contains a numpy array)
    # an array used to store other objects
    def __init__(self):
        self.log = np.array([])

    def append(self, val):
        self.log = np.append(self.log, [val])


class EntryTrade:
    def __init__(self, cur_from, cur_to, amount_taken, date, conversion_rate):
        self.cur_from = cur_from
        self.cur_to = cur_to
        self.amount = amount_taken
        self.conversion_rate = conversion_rate
        self.date = date


class Entry:  # object properties: action, amount, department
    # entries are saved in the ledger of an account
    def __init__(self, action, amount, department, date):
        self.action = action  # type of action (deposit, withdrawal, transfer_sent, transfer_received)
        self.amount = amount  # value moved in the action
        self.department = department  # if the account is a business account, department is set, otherwise set as -1
        self.date = date


class HashTable:  # object properties: body (contains a dictionary)
    def __init__(self):
        self.body = {}

    def add_key_value(self, key, value):  # add {key: value}
        self.body[key] = value

    def add_key_index(self, key):  # add {key: index}
        self.body[key] = len(self.body)

    def add_index_value(self, value):  # add {index: value}
        self.body[len(self.body)] = value

    def in_table(self, key):  # return value for received key (return -1 if key does not exist)
        try:
            return self.body[key]
        except KeyError:
            return -1

    def alter_key_index(self, index, new_key):  # change the key in a {key: index} type table
        temp_table = reverse_dictionary(self.body)
        temp_table[index] = new_key
        new_table = reverse_dictionary(temp_table)
        self.body = new_table


class Cloud:  # a financial cloud that allows deposits to be kept and accessed using an access code
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Cloud, cls).__new__(cls)
        return cls.instance

    def __init__(self):  # attribute contains dictionary {code: value accessed with code}
        self.allocated = {}

    def allocate(self, amount, code, account_index):
        confirm = False
        response_code = -1
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            return confirm, response_code
        if Accounts.log[account_index].value >= amount:
            Accounts.log[account_index].value -= amount
            if code in self.allocated.keys():
                self.allocated[code] += amount
            else:
                self.allocated[code] = amount
            confirm = True
            response_code = 1
        else:
            response_code = -3

        return confirm, response_code

    def withdraw(self, amount, code_attempt, account_index):
        confirm = False
        response_code = -1
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            return confirm, response_code
        if code_attempt in self.allocated.keys():
            if self.allocated[code_attempt] >= amount:
                self.allocated[code_attempt] -= amount
                Accounts.log[account_index].value += amount
                confirm = True
                response_code = 1
                if self.allocated[code_attempt] == 0:
                    del self.allocated[code_attempt]
            else:
                response_code = -3
        else:
            response_code = -4

        return confirm, response_code


class Account:
    def __init__(self):  # object properties: value, account_number, ledger
        self.value = create_value_table()
        self.account_number = assign_account_number()
        self.ledger = Log()
        self.trade_ledger = Log()
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('reg')

    def deposit(self, amount):
        confirm = False
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            else:
                response_code = -1
            confirm = False
        else:
            confirm = True
            response_code = 1
            self.value['USD'] = self.value['USD'] + amount
            self.ledger.append(Entry('d', amount, -1, get_date()))

        return confirm, response_code

    def withdraw(self, amount):
        confirm = False
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            else:
                response_code = -1
            confirm = False
        else:
            if self.value['USD'] >= amount:
                confirm = True
                response_code = 1
                self.value['USD'] = self.value['USD'] - amount
                self.ledger.append(Entry('w', amount, -1, get_date()))
            else:
                response_code = -3
                confirm = False

        return confirm, response_code

    def trade_currency(self, amount, cur_from, cur_to):
        confirm = False
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2  # amount is 0
            else:
                response_code = -1  # input invalid
            confirm = False
        if confirm:
            if (cur_from in self.value.keys()) and (cur_to in self.value.keys()):
                if self.value[cur_from] >= amount:
                    self.value[cur_from] = self.value[cur_from] - amount
                    self.value[cur_to] = self.value[cur_to] + currency_rates(cur_from, cur_to, amount)
                    self.trade_ledger.append(EntryTrade(cur_from, cur_to, amount, get_date(), currency_rates(cur_from, cur_to, 1)))
                else:
                    response_code = -3
                    confirm = False
            else:
                response_code = -4
                confirm = False

        return confirm, response_code

    def transfer(self, amount, target_account, dep_name):
        confirm = False
        target_index = -1
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2  # amount is 0
            else:
                response_code = -1  # input invalid
            confirm = False
        else:
            target_index = name_table.in_table(target_account)
            if target_index == -1:
                target_index = number_table.in_table(target_account)
                if target_index == -1:
                    response_code = -3  # target account does not exist
                else:
                    confirm = True
            else:
                confirm = True
        if confirm:
            response_code = 1
            if self.value['USD'] >= amount:
                if dep_name == 'none':
                    Accounts.log[target_index].value['USD'] = Accounts.log[target_index].value['USD'] + amount
                    self.value['USD'] = self.value['USD'] - amount
                    self.ledger.append(Entry('tf', amount, -1, get_date()))
                    Accounts.log[target_index].ledger.append(Entry('tt', amount, -1, get_date()))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if dep_name in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[dep_name]['USD'] = \
                                Accounts.log[target_index].departments[dep_name]['USD'] + amount
                            self.value['USD'] = self.value['USD'] - amount
                            self.ledger.append(Entry('tf', amount, -1, get_date()))
                            Accounts.log[target_index].ledger.append(Entry('tt', amount, dep_name, get_date()))
                        else:
                            response_code = -6  # department name does not exist
                            confirm = False
                    else:
                        response_code = -5  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = -4  # amount is not enough
                confirm = False

        return confirm, response_code


class SavingsAccount:  # object properties: value, returns, last_update, account_number, ledger
    def __init__(self, returns):
        self.value = 0
        self.returns = pow(returns, 1/12)  # returns per month
        self.last_update = get_date()
        self.shift_date = get_date()[0]
        self.account_number = assign_account_number()
        self.ledger = Log()
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('sav')

    def update(self):
        current_date = get_date()
        months = current_date[1] - self.last_update[1]
        if current_date[0] < self.shift_date:
            months -= 1
        self.value = self.value * (pow((1 + self.returns), months))

    def deposit(self, amount):
        confirm = False
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            else:
                response_code = -1
            confirm = False
        else:
            confirm = True
            response_code = 1
            self.value = self.value + amount
            self.ledger.append(Entry('d', amount, -1, get_date()))

        return confirm, response_code

    def withdraw(self, amount):
        confirm = False
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            else:
                response_code = -1
            confirm = False
        else:
            if self.value >= amount:
                confirm = True
                response_code = 1
                self.value = self.value - amount
                self.ledger.append(Entry('w', amount, -1, get_date()))
            else:
                response_code = -3
                confirm = False

        return confirm, response_code

    def transfer(self, amount, target_account, dep_name):
        confirm = False
        target_index = -1
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2  # amount is 0
            else:
                response_code = -1  # input invalid
            confirm = False
        else:
            target_index = name_table.in_table(target_account)
            if target_index == -1:
                target_index = number_table.in_table(target_account)
                if target_index == -1:
                    response_code = -3  # target account does not exist
                else:
                    confirm = True
            else:
                confirm = True
        if confirm:
            response_code = 1
            if self.value >= amount:
                if dep_name == 'none':
                    Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                    self.value = self.value - amount
                    self.ledger.append(Entry('tf', amount, -1, get_date()))
                    Accounts.log[target_index].ledger.append(Entry('tt', amount, -1, get_date()))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if dep_name in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[dep_name]['USD'] = \
                                Accounts.log[target_index].departments[dep_name]['USD'] + amount
                            self.value = self.value - amount
                            self.ledger.append(Entry('tf', amount, -1, get_date()))
                            Accounts.log[target_index].ledger.append(Entry('tt', amount, dep_name, get_date()))
                        else:
                            response_code = -6  # department name does not exist
                            confirm = False
                    else:
                        response_code = -5  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = -4  # amount is not enough
                confirm = False

        return confirm, response_code


class BusinessAccount:  # object properties: company_name, departments_array, account_number, ledger
    def __init__(self, company_name, department_names):  # department_name is a list of names for each department
        self.company_name = company_name
        self.departments = {}
        self.account_number = assign_account_number()
        self.ledger = Log()
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('bus')
        for name in department_names:
            self.departments[name] = create_value_table()

    def add_department(self, dep_name):
        confirm = False
        response_code = 0
        if dep_name not in self.departments.keys():
            self.departments[dep_name] = create_value_table()
            confirm = True
        else:
            response_code = -1  # department name already exists

        return confirm, response_code


class Global:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Global, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.redirect_flags = {}
        self.responses = {}
        self.current_account = {}

    def alter_rf(self, key, value):  # add to/change key:value for redirect_flags
        self.redirect_flags[key] = value

    def alter_re(self, key, value):  # add to/change key:value for responses
        self.responses[key] = value

    def alter_ca(self, key, value):  # add to/change key:value for current_account
        self.current_account[key] = value


# functions
def currency_rates(cur1, cur2, amount):
    return CurrencyRates().convert(cur1, cur2, amount)


def assign_account_number():
    # Generate a random number between 1000000000 and 9999999999
    number = random.randint(1000000000, 9999999999)

    # Check if the random number has been generated before
    while number in existing_account_numbers:
        # If it has, generate a new random number
        random_number = random.randint(1000000000, 9999999999)

    # Add the random number to the set of generated numbers
    existing_account_numbers.add(number)

    return number


def reverse_dictionary(dic):
    keys = list(dic.keys())
    values = list(dic.values())
    reversed_dic = {}
    for i in range(len(keys)):
        reversed_dic[values[i]] = keys[i]
    return reversed_dic


def get_date():
    now = str(datetime.datetime.now())
    year = now[0:4]
    month = now[5:7]
    day = now[8:10]
    date = np.array([year, month, day])
    return date


def digitcount(num):
    num = str(num)
    counter = 0
    for ch in num:
        counter += 1
    return counter


def multiple(vec):
    sumlist = 1
    for i in vec:
        sumlist *= i
    return sumlist


def sum_list(vec):
    sumlist = 1
    for i in vec:
        sumlist += i
    return sumlist


def hash_function(enter):
    ascii_values = []
    for ch in enter:
        ascii_values.append(ord(ch))
    values = []
    for i in range(len(ascii_values)):
        values.append((i * 123854 ^ ascii_values[i] * 984) | (multiple(ascii_values)))
    val = ((sum(values) - 2587465) & (951456 * (multiple(values)) + 456 * sum(values)))
    if val < 0:
        val = val ^ (sum(ascii_values) + 95813)
    factor = (((sum(values) + 15984354) | (multiple(values) + 10000009814008)) & (
            (sum(ascii_values) + 87515557) ^ (multiple(ascii_values) * 8558224)))
    newval = abs(val ^ factor)
    if newval % 10 != 9:
        newval += 1
    else:
        newval += 11
    temp = newval
    while digitcount(temp) < 30:
        temp *= 10
    return abs(temp)


def create_value_table():
    value_table = {'USD': 0, 'EUR': 0, 'JPY': 0, 'BGN': 0, 'CZK': 0, 'GBP': 0, 'CHF': 0, 'AUD': 0, 'BRL': 0, 'CAD': 0,
                   'CNY': 0, 'IDR': 0, 'INR': 0, 'MXN': 0, 'SGD': 0, 'BTC': 0}
    return value_table


def check_validity(data):
    data = str(data)
    characters = []
    valid = True
    non_valid = ['.', ':', '(', '{', ')', '}', ',', '^', '<', '>', '+', '-', '*', '/', '%', '=', '|', ' ']
    counter = 0
    while (counter < len(data)) and valid:
        ch = data[counter]
        if ch in non_valid:
            valid = False
        else:
            counter += 1
    return valid


def generate_code():
    number = random.randint(100000, 999999)
    return number


def send_recovery_email(email_address):
    # create an SMTP server object
    mail_server = smtplib.SMTP('smtp.example.com', 587)

    # create the email data, including the email content and recipients
    message = """\
    From: FinCloud@server.com
    To: {}
    Subject: Recovery for FinCloud account

    Recovery code for your account: {}""".format(email_address, generate_code())

    # send the email using the server object
    mail_server.sendmail('FinCloud@server.com', [email_address], message)


def send_confirmation_email(email_address):
    # create an SMTP server object
    mail_server = smtplib.SMTP('smtp.example.com', 587)

    # create the email data, including the email content and recipients
    message = """\
    From: FinCloud@server.com
    To: {}
    Subject: Recovery for FinCloud account

    Confirm your email with this code: {}""".format(email_address, generate_code())

    # send the email using the server object
    mail_server.sendmail('FinCloud@server.com', [email_address], message)


def verification(attempt, code_attempt):  # returns: verification answer, response code, account index
    # initialize return values
    verify = False

    # check existence of account name/number
    temp_name = name_table.in_table(attempt)  # attempt - client's attempt at account name/number
    temp_num = number_table.in_table(attempt)
    # set response
    if (temp_name == -1) and (temp_num == -1):
        response_code = -1  # incorrect name/number
    elif (temp_name != -1) and (temp_num == -1):
        if temp_name == pass_table.in_table(hash_function(code_attempt)):
            response_code = 1
            verify = True
        else:
            response_code = -2  # incorrect password
    elif (temp_num != -1) and (temp_name == -1):
        if temp_num == pass_table.in_table(hash_function(code_attempt)):
            response_code = 1
            verify = True
        else:
            response_code = -2  # incorrect password
    else:
        response_code = -3  # system error (user's attempt matches both a name and a number -> impossible situation)

    # setting index of account
    index = -1
    if verify:
        index = pass_table.in_table(hash_function(code_attempt))

    # return values (verification answer, response code)
    return verify, response_code, index


def create_account(account_name, account_code, phone_num):  # returns: confirmation, account index, response code
    confirm = False  # initialize return value
    user_name = account_name  # saving initial name of account

    # checking validity and availability of account name and code
    if check_validity(account_name) and check_validity(account_code):
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = 1  # account name and code are confirmed
        else:
            response_code = -4  # account name is unavailable
    else:
        if not check_validity(account_name) and check_validity(account_code):
            response_code = -1  # name invalid
        else:
            response_code = -2  # code invalid
        if not (check_validity(account_name) or check_validity(account_code)):
            response_code = -3  # name and code invalid
    if confirm:
        # add account details to tables
        name_table.add_key_index(account_name)
        pass_table.add_key_index(hash_function(account_code))
        phone_name_table.add_key_value(hash_function(phone_num), account_name)

        # create account object
        new_account = Account()
        account_name = "ac" + str(name_table.in_table(account_name))
        globals()[account_name] = new_account
        Accounts.append(globals()[account_name])

    # return values (confirmation, account index, response code)
    return confirm, name_table.in_table(user_name), response_code


# tables
name_table = HashTable()  # account name table - {account name: serial number}
number_table = HashTable()  # account number table - {account number: serial number}
pass_table = HashTable()  # password table - {hash value of account password: serial number}
phone_name_table = HashTable()  # account recovery recovery table - {hash value of phone number: account name}
loc_type_table = HashTable()  # account type table - {serial number: type of account (reg/bus/sav)}
value_summary_table = HashTable()  # value recovery table - {value summary: serial number}

# Accounts log
Accounts = Log()  # Log containing all Accounts

# class containing data that can be accessible from all locations in file
data = Global()

# set containing all existing account numbers
existing_account_numbers = set()


# server: request handling
class FinCloud(BaseHTTPRequestHandler):

    def clear(self):
        output = '<html><body>'
        output += '<script type="text/javascript">document.body.innerHTML = ""</script>'
        output += '</body></html>'
        self.wfile.write(output.encode())

    def start(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()

    def redirect(self, path):
        self.send_response(301)
        self.send_header('content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def input_error(self):  # redirect to main page, set redirect flag to true, set response code to -1 to display error
        data.alter_rf(self.client_address[0], True)
        data.alter_re(self.client_address[0], -1)
        self.redirect('/')

    def do_GET(self):

        if self.client_address[0] not in data.redirect_flags.keys():
            data.alter_rf(self.client_address[0], False)

        if self.path.endswith('/'):
            self.start()
            self.clear()
            output = '<html><body>'
            self.wfile.write(bytes('<head><title>FinCloud.com</title></head>', "utf-8"))
            output += '<h1>FinCloud - A modern solution for you</h1>'
            output += '<h3><a href="/About">Learn about us</a></h3>'
            output += '<h3><a href="/login">Sign in</a></h3>'
            output += '<h3><a href="/see_data">Temp</a></h3>'
            if data.redirect_flags[self.client_address[0]]:
                data.redirect_flags[self.client_address[0]] = False
                if data.responses[self.client_address[0]] == -1:
                    output += '</br>' + '<h4>System error. Please try again later.</h4>'
                data.alter_re(self.client_address[0], 0)
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/home'):
            self.start()
            self.clear()

        if self.path.endswith('/see_data'):  # delete after development
            self.start()
            self.clear()
            output = '<html><body>'
            print(name_table.body)
            print(pass_table.body)
            print(phone_name_table.body)
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/About'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>What is FinCloud?</h1>'
            output += 'Fincloud is a state of the art financial network...'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/login'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Log in   |   Continue to FinCloud</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/login">'
            output += 'Account name/number: ' + '<input name="username" type="text">' + '</br>'
            output += 'Account access Code: ' + '<input name="code" type="text">' + '</br>' + '</br>'
            output += '<input type="submit" value="Login">'
            output += '</form>'
            temp = '<p style = "color: black" style = "text-decoration: none">Forgot your password?</p>'
            output += '<h5><a href="/forgot">' + temp + '</a></h5>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                if data.responses[self.client_address[0]] == -1:
                    output += '<h4>Account name/number is incorrect. Please try again.</h4>'
                elif data.responses[self.client_address[0]] == -2:
                    output += '<h4>Password is incorrect. Please try again.</h4>'
                elif data.responses[self.client_address[0]] == -3:
                    output += '<h4>System error. Please try again at a later time.</h4>'
                elif data.responses[self.client_address[0]] == 2:
                    output += '<h4>Account recovered. Password reset.</h4>'
                elif data.responses[self.client_address[0]] == 3:
                    output += '<h4>New account created.</h4>'
                data.alter_re(self.client_address[0], 0)
            output += '___         or         ___' + '</br>' + '</br>' + '</br>'
            output += 'New to FinCloud? ' + '<a href="/new">Get started</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/forgot'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Recover your account</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/forgot">'
            output += 'Enter your account name/number: ' + '<input name="user" type="text">' + '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your new account password: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>'
            output += '</br>'
            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                if data.responses[self.client_address[0]] == -1:
                    output += '<h4>Phone number does not exist in out system.</h4>'
                elif data.responses[self.client_address[0]] == -2:
                    output += '<h4>Account name/number incorrect.</h4>'
                elif data.responses[self.client_address[0]] == -3:
                    output += '<h4>Codes do not match</h4>'
                data.alter_re(self.client_address[0], 0)
            output += '</br>'
            output += '<h4><a href="/login">Return to log in page</a></h4>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/new'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open an account</h1>'
            output += '<h3>Select an account that fits your needs</h3>'
            output += 'From personal accounts to specialized accounts for business, ' \
                      'FinCloud offers the best service you can find.' + '</br>' + '</br>'
            output += '<h2>Select the best account for you</h2>'
            output += '<h4><a href="/new/business">Specialized Business Account</a></h4>'
            output += 'Specialized accounts that allow simple and effective' \
                      ' management of funds throughout multiple departments'
            output += '<h4><a href="/new/checking">Personal Checking Account</a></h4>'
            output += 'Personal accounts that allow for dynamic management of personal funds.' \
                      ' Our personal accounts also offer users the option to distribute' \
                      ' their capital and purchase multiple currencies.'
            output += '<h4><a href="/new/savings">Savings Account</a></h4>'
            output += 'Personal accounts that support savings at an interest determined by you.'
            output += '</br>' + '</br>' + '</br>' + '</br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/new/checking'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open a personal checking account</h1>'
            output += 'Personal checking accounts allow for dynamic management of personal funds.' \
                      ' Our personal accounts also offer you the option to distribute' \
                      ' your capital and purchase multiple currencies.'
            output += '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/new/checking">'
            output += 'Enter a name for your account: ' + '<input name="user" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter a password for your account: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                if data.responses[self.client_address[0]] == -1:
                    output += '<h4>Account name is invalid. Please try again.</h4>'
                elif data.responses[self.client_address[0]] == -2:
                    output += '<h4>Account code is invalid: do not use unnecessary symbols. Please try again.</h4>'
                elif data.responses[self.client_address[0]] == -3:
                    output += '<h4>Account name and code are invalid: do not use unnecessary symbols.' \
                              ' Please try again.</h4>'
                elif data.responses[self.client_address[0]] == -4:
                    output += '<h4>An account with this name already exists. Please try again.</h4>'
                elif data.responses[self.client_address[0]] == -5:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)
            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br>' + '</br>' + '</br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/new/business'):
            print()

        if self.path.endswith('/new/savings'):
            print()

    def do_POST(self):

        if self.path.endswith('/login'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                user_attempt = fields.get('username')[0]
                code_attempt = fields.get('code')[0]

                # verification process with input from user
                verify, response_code, index = verification(user_attempt, code_attempt)
                if verify:
                    data.alter_ca(self.client_address[0], index)
                    self.redirect('/home')
                else:
                    data.alter_re(self.client_address[0], response_code)
                    data.alter_rf(self.client_address[0], True)
                    self.redirect('/login')
            else:
                self.input_error()

        if self.path.endswith('/new/checking'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                phone_number = fields.get('phone')[0]
                code = fields.get('code')[0]
                code_confirm = fields.get('code_confirm')[0]
                account_name = fields.get('user')[0]

                # create account with user input
                if code == code_confirm:
                    confirm, index, response_code = create_account(account_name, code, phone_number)
                    if confirm:
                        data.alter_ca(self.client_address[0], index)
                        data.alter_re(self.client_address[0], 3)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/login')
                    else:
                        data.alter_re(self.client_address[0], response_code)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/new/checking')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], -5)
                    self.redirect('/new/checking')
            else:
                self.input_error()

        if self.path.endswith('/forgot'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                phone_number = fields.get('phone')[0]
                new_code = fields.get('code')[0]
                code_confirm = fields.get('code_confirm')[0]
                user = fields.get('user')[0]

                # account code reset process with user input
                if new_code == code_confirm:
                    if (name_table.in_table(user) != -1) or (number_table.in_table(user) != -1):
                        if phone_name_table.in_table(hash_function(phone_number)) != -1:
                            account_name = phone_name_table.in_table(hash_function(phone_number))
                            account_loc = name_table.in_table(account_name)
                            pass_table.alter_key_index(account_loc, hash_function(new_code))

                            # redirect to login page and send approval
                            data.alter_rf(self.client_address[0], True)
                            data.alter_re(self.client_address[0], 2)
                            self.redirect('/login')
                        else:
                            # redirect to forgot page and send error message (phone number does not exist in our system)
                            data.alter_rf(self.client_address[0], True)
                            data.alter_re(self.client_address[0], -1)
                            self.redirect('/forgot')
                    else:
                        # redirect to forgot page and send error message (account name/number incorrect)
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], -2)
                        self.redirect('/forgot')
                else:
                    if not (name_table.in_table(user) != -1) and not (number_table.in_table(user) != -1):
                        # redirect to forgot page and send error message (account name/number incorrect)
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], -2)
                        self.redirect('/forgot')
                    else:
                        # redirect to forgot page send error message (codes do not match)
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], -3)
                        self.redirect('/forgot')
            else:
                self.input_error()


# 'main' function
def main():
    PORT = 8080
    IP = socket.gethostbyname(socket.gethostname())
    server_address = (IP, PORT)
    server = http.server.HTTPServer(server_address, FinCloud)
    print('Server running at http://{}:{}'.format(IP, PORT))
    server.serve_forever()
    print("yes")


if __name__ == '__main__':
    main()
