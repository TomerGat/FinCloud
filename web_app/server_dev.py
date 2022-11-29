from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import cgi
import datetime
from random import randint
import numpy as np
from enum import Enum

# initial setup:


# classes
class Log:  # object variables: log (contains a numpy array)
    # an array used to store other objects
    def __init__(self):
        self.log = np.array([])

    def append(self, val):
        self.log = np.append(self.log, [val])


class Entry:  # object variables: action, amount, department
    # entries are saved in the ledger of an account
    def __init__(self, action, amount, account_type, department):
        self.action = action  # type of action (deposit, withdrawal, transfer_sent, transfer_received)
        self.amount = amount  # value moved in the action
        self.department = department  # if the account is a business account, department is set, otherwise set as -1


class Errors(Enum):  # enum containing types of errors
    invalid = -1
    system_error = -2


class HashTable:  # object variables: body (contains a dictionary)
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

    def allocate(self, amount, code):
        confirm = False
        response_code = -1
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            return confirm, response_code
        if Accounts.log[current_account].value >= amount:
            Accounts.log[current_account].value -= amount
            if code in self.allocated.keys():
                self.allocated[code] += amount
            else:
                self.allocated[code] = amount
            confirm = True
            response_code = 1
        else:
            response_code = -3

        return confirm, response_code

    def withdraw(self, amount, code_attempt):
        confirm = False
        response_code = -1
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            return confirm, response_code
        if code_attempt in self.allocated.keys():
            if self.allocated[code_attempt] >= amount:
                self.allocated[code_attempt] -= amount
                Accounts.log[current_account].value += amount
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
    def __init__(self):  # object variables: value, account_number, ledger
        self.value = create_value_table()
        self.account_number = assign_account_number()
        self.ledger = Log()
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('reg')

    def check_value(self):
        return self.value['USD']

    def transfer(self, amount, target_account, dep_name):
        confirm = False
        target_index = -1
        response_code = 0
        if not (check_validity(amount) and (type(amount) is int) and amount != 0):
            if amount == 0:
                response_code = -2
            else:
                response_code = -1
            confirm = False
        else:
            target_index = name_table.in_table(target_account)
            if target_index == -1:
                target_index = number_table.in_table(target_account)
                if target_index == -1:
                    response_code = -2
                else:
                    confirm = True
            else:
                confirm = True
        if confirm:
            response_code = 1
            if self.value['USD'] >= amount:
                self.value['USD'] = self.value['USD'] - amount
                if dep_name == 'none':
                    Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if dep_name in Accounts.log[target_index].departments:
                            Accounts.log[target_index].departments[dep_name] = \
                                Accounts.log[target_index].departments[dep_name] + amount
                        else:
                            response_code = -5
                            confirm = False
                    else:
                        response_code = -4
                        confirm = False
            else:
                response_code = -3
                confirm = False

        return confirm, response_code


class SavingsAccount:  # object variables: value, returns, last_update, account_number, ledger
    def __init__(self, returns):
        self.value = 0
        self.returns = returns
        self.last_update = get_date()
        self.account_number = assign_account_number()
        self.ledger = Log()
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('sav')

    # def transfer(self, amount, target_account, ):


class BusinessAccount:  # object variables: company_name, departments_array, account_number, ledger
    def __init__(self, company_name, department_names):  # department_name is a list of names for each department
        self.company_name = company_name
        self.departments = {}
        self.account_number = assign_account_number()
        self.ledger = Log()
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('bus')
        for name in department_names:
            self.departments[name] = 0


# functions
def assign_account_number():
    num = 0
    confirm_num = False
    while not confirm_num:
        num = randint(1000000000, 9999999999)
        check = number_table.in_table(num)
        if (check != -1) and (name_table.in_table(hash_function(num)) == -1):
            break
    return num


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


def hash_function(text):
    def list_sum(lst):
        add = 0
        for i in lst:
            add += i
        return add

    def list_mul(lst):
        mul = 1
        for i in lst:
            mul *= i
        return mul

    text = str(text)
    ascii_values = []
    for ch in text:
        ascii_values.append(ord(ch))
    values = []
    for i in range(len(ascii_values)):
        values.append(((i*123854) ^ (ascii_values[i]*984)) | (-list_mul(ascii_values)))
    val = list_sum(values) & (list_mul(values) + 456 * list_sum(values))
    val = val & 0xFEDCBAABCDEF
    return val


def create_value_table():
    value_table = {'USD': 0, 'EUR': 0, 'JPY': 0, 'BGN': 0, 'CZK': 0, 'GBP': 0, 'CHF': 0, 'AUD': 0, 'BRL': 0, 'CAD': 0,
                   'CNY': 0, 'IDR': 0, 'INR': 0, 'MXN': 0, 'SGD': 0, 'BTC': 0, 'history': False,
                   'mining start date': '', 'mining rate': 0, 'mining fine': 0, 'mined BTC': 0}
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
        response_code = -3  # system error (user's attempt matches both a __name__ and a number -> impossible situation)

    # setting index of account
    index = -1
    if verify:
        index = pass_table.in_table(hash_function(code_attempt))

    # return values (verification answer, response code)
    return verify, response_code, index


def create_account(account_name, account_code, phone_num):  # returns: confirmation, account index, response code
    # initialize return values
    confirm = False

    # checking validity and availability of account __name__ and code
    if check_validity(account_name) and check_validity(account_code):
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = 1  # account __name__ and code are confirmed
        else:
            response_code = -4  # account __name__ is unavailable
    else:
        if not check_validity(account_name) and check_validity(account_code):
            response_code = -1  # __name__ invalid
        else:
            response_code = -2  # code invalid
        if not (check_validity(account_name) or check_validity(account_code)):
            response_code = -3  # __name__ and code invalid
    if confirm:
        # add account details to tables
        name_table.add_key_index(account_name)
        pass_table.add_key_index(hash_function(account_code))
        phone_name_table.add_key_value(hash_function(phone_num), account_name)

        # create account object
        new_account = Account()
        account_name = "ac" + name_table.in_table(account_name)
        globals()[account_name] = new_account
        Accounts.append(globals()[account_name])

    # return values (confirmation, account index, response code)
    return confirm, name_table.in_table(account_name), response_code


# tables
name_table = HashTable()  # account __name__ table - {account name: serial number}
number_table = HashTable()  # account number table - {account number: serial number}
pass_table = HashTable()  # password table - {hash value of account password: serial number}
phone_name_table = HashTable()  # account recovery recovery table - {hash value of phone number: account name}
loc_type_table = HashTable()  # account type table - {serial number: type of account (reg/bus/sav)}
value_summary_table = HashTable()  # value recovery table - {value summary: serial number}

# Accounts log
Accounts = Log()  # Log containing all Accounts
# create_random()

# global variables
current_account = {}  # {ip address : account that the ip address is logged into}
redirect = False  # set redirect flag to True when necessary
response_global = 0  # variable containing response code


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

    def do_GET(self):
        global redirect  # declare redirect as global variable
        global response_global  # declare response_global as global variable
        global current_account  # declare current_account as global variable
        self.start()
        output = '<html><body>'
        self.wfile.write(bytes('<head><title>FinCloud.com</title></head>', "utf-8"))
        output += '<h1>FinCloud - A modern solution for you</h1>'
        output += '<h3><a href="/About">Learn about us</a></h3>'
        output += '<h3><a href="/login">Sign in</a></h3>'
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

            # print error message if redirect flag is set to True
            if redirect:
                redirect = False
                if response_global == -1:
                    output += '<h4>Account name/number is incorrect. Please try again.</h4>'
                elif response_global == -2:
                    output += '<h4>Password is incorrect. Please try again.</h4>'
                elif response_global == -3:
                    output += '<h4>System error. Please try again at a later time.</h4>'
                response_global = 0
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
            output += '</br>' + '</br>'
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
            output += 'Enter a __name__ for your account: ' + '<input name="user" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter a password for your account: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br>'

            # print error message if redirect flag is set to True
            if redirect:
                redirect = False
                if response_global == -1:
                    output += '<h4>Account __name__ is invalid. Please try again.</h4>'
                elif response_global == -2:
                    output += '<h4>Account code is invalid: do not use unnecessary symbols. Please try again.</h4>'
                elif response_global == -3:
                    output += '<h4>Account __name__ and code are invalid: do not use unnecessary symbols.' \
                              ' Please try again.</h4>'
                elif response_global == -4:
                    output += '<h4>An account with this __name__ already exists. Please try again.</h4>'
                elif response_global == -5:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
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
        global current_account  # declare current_account as global variable
        global redirect  # declare redirect as global variable
        global response_global  # declare response_global as global variable

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
                verify, response_code, account_index = verification(user_attempt, code_attempt)
                if verify:
                    current_account[self.client_address[0][0]] = account_index
                    self.redirect('/home')
                else:
                    response_global = response_code
                    redirect = True
                    self.redirect('/login')

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

                # create account process with user input
                if code == code_confirm:
                    confirm, index, response_code = create_account(account_name, code, phone_number)
                    if confirm:
                        current_account[self.client_address[0][0]] = account_index
                        self.redirect('/login')
                    else:
                        response_global = response_code
                        redirect = True
                        self.redirect('/new/checking')
                else:
                    redirect = True
                    response_global = -5
                    self.redirect('/new/checking')

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
                        else:
                            print()
                            # redirect to forgot page and send error message (phone number does not exist in our system)
                    else:
                        print()
                        # redirect to forgot page and send error message (account name/number incorrect)
                else:
                    print()
                    # redirect to forgot page send error message (codes do not match)


# 'main' function
def main():
    PORT = 8080
    IP = socket.gethostbyname(socket.gethostname())
    server_address = (IP, PORT)
    server = HTTPServer(server_address, FinCloud)
    print('Server running at http://{}:{}'.format(IP, PORT))
    server.serve_forever()


if __name__ == '__main__':
    main()
