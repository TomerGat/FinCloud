# build email server to send emails for account recovery
# replace phone numbers with email addresses, change hash table, so it contains email addresses and not hash values
# create function to validate email addresses
# change /forgot page to allow recovery of account name
# request confirmation with email for account creation
# add ssl encryption
# create enum for response codes / several final variables (important to remove repeated use of numbers)
# store ip addresses as hash values
# create admin account with special privileges, such as deleting accounts, backing up data and more
# add trade history, action history, account actions summary
# add option to trade crypto other than BTC
# get_value_usd() possibly very slow - might need changing


# import header file
from server_header import *


# classes
class TradeEntry:
    def __init__(self, cur_from, cur_to, amount_taken, date, conversion_rate):
        self.cur_from = cur_from
        self.cur_to = cur_to
        self.amount = amount_taken
        self.conversion_rate = conversion_rate
        self.date = date


class ConnectionEntry:
    def __init__(self, request_type, precise_time):
        self.lst = [request_type, precise_time]


class Entry:  # object properties: action, amount
    # entries are saved in the ledger of an account
    def __init__(self, action, amount, date, target_num, target_dep):
        self.action = action  # type of action (deposit, withdrawal, transfer_sent, transfer_received)
        self.amount = amount  # value moved in the action
        self.date = date
        self.target_num = target_num  # if action involves other accounts this is set, otherwise set to -1
        self.target_dep = target_dep  # if action involves other accounts this is set, otherwise set to -1


class Cloud:  # a financial cloud that allows deposits to be kept and accessed using an access code
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Cloud, cls).__new__(cls)
        return cls.instance

    def __init__(self):  # attribute contains dictionary {code: value accessed with code}
        self.allocated = {}

    def allocate(self, amount, allocation_code, ac_name, dep_name):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            confirm = False
            ac_index = name_table.in_table(ac_name)
            if 0 < ac_index <= len(Accounts.log):
                ac_type = loc_type_table.in_table(ac_index)
                if ac_type == 'reg':
                    ac_value = Accounts.log[ac_index].value['USD']
                elif ac_type == 'sav':
                    ac_value = Accounts.log[ac_index].value
                else:
                    ac_value = Accounts.log[ac_index].departments[dep_name][0]['USD']
                if ac_value >= amount:
                    if validate_string(allocation_code):
                        confirm = True
                        if ac_type == 'reg':
                            Accounts.log[ac_index].value['USD'] = Accounts.log[ac_index].value['USD'] - amount
                        elif ac_type == 'sav':
                            Accounts.log[ac_index].value = Accounts.log[ac_index].value - amount
                        else:
                            Accounts.log[ac_index].departments[dep_name][0]['USD'] = Accounts.log[ac_index].departments[dep_name][0]['USD'] - amount
                        if allocation_code in self.allocated.keys():
                            self.allocated[allocation_code] = self.allocated[allocation_code] + amount
                        else:
                            self.allocated[allocation_code] = amount
                        response_code = 1
                    else:
                        pass
                else:
                    pass
            else:
                pass

        return confirm, response_code

    def withdraw(self, amount, code_attempt, account_index):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            confirm = False
            if hash_function(code_attempt) in self.allocated.keys():
                if self.allocated[hash_function(code_attempt)] >= amount:
                    self.allocated[hash_function(code_attempt)] -= amount
                    Accounts.log[account_index].value += amount
                    confirm = True
                    response_code = 1
                    if self.allocated[hash_function(code_attempt)] == 0:
                        del self.allocated[hash_function(code_attempt)]
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

    def get_value_usd(self):
        total = 0
        for curr in self.value.keys():
            total += currency_rates(curr, 'USD', self.value[curr])
        return str(total)

    def deposit(self, amount):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            response_code = 1
            self.value['USD'] = self.value['USD'] + amount
            self.ledger.append(Entry('d', amount, get_date(), -1, -1))

        return confirm, response_code

    def withdraw(self, amount):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            if self.value['USD'] >= amount:
                response_code = 1
                self.value['USD'] = self.value['USD'] - amount
                self.ledger.append(Entry('w', amount, get_date(), -1, -1))
            else:
                response_code = -3  # account value too low
                confirm = False

        return confirm, response_code

    def trade_currency(self, amount, source_cur, target_cur):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            confirm = False
            if (source_cur in self.value.keys()) and (target_cur in self.value.keys()):
                if self.value[source_cur] >= amount:
                    self.value[source_cur] = self.value[source_cur] - amount
                    self.value[target_cur] = self.value[target_cur] + currency_rates(source_cur, target_cur, amount)
                    self.trade_ledger.append(
                        TradeEntry(source_cur, target_cur, amount, get_date(), currency_rates(source_cur, target_cur, 1)))
                    confirm = True
                else:
                    response_code = -3  # insufficient funds
            else:
                if (source_cur not in self.value.keys()) and (target_cur in self.value.keys()):
                    response_code = -4  # source currency not found
                elif (source_cur in self.value.keys()) and (target_cur not in self.value.keys()):
                    response_code = -5  # target currency not found
                else:
                    response_code = -6  # source and target currencies not found

        return confirm, response_code

    def transfer(self, amount, target_account, target_dep):
        confirm = True
        target_index = -1
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            confirm = False
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
                if target_dep == 'none':
                    if loc_type_table.in_table(target_index) == 'sav':
                        Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                    elif loc_type_table.in_table(target_index) == 'reg':
                        Accounts.log[target_index].value['USD'] = Accounts.log[target_index].value['USD'] + amount
                    if loc_type_table.in_table(target_index) == 'bus':
                        response_code = -7  # account is of business type but department name is set to 'none'
                        confirm = False
                    else:
                        self.value['USD'] = self.value['USD'] - amount
                        self.ledger.append(
                            Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, -1))
                        Accounts.log[target_index].ledger.append(
                            Entry('tt', amount, get_date(), self.account_number, -1))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.value['USD'] = self.value['USD'] - amount
                            self.ledger.append(
                                Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, target_dep))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('tt', amount, get_date(), self.account_number, -1))
                        else:
                            response_code = -6  # department name does not exist
                            confirm = False
                    else:
                        response_code = -5  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = -4  # insufficient funds
                confirm = False

        return confirm, response_code


class SavingsAccount:  # object properties: value, returns, last_update, account_number, ledger
    def __init__(self, returns):
        self.value = 0
        self.returns = pow((1 + returns / 100), 1 / 12)  # returns per month
        self.last_update = get_date()
        self.shift_date = get_date()[0]
        self.account_number = assign_account_number()
        self.ledger = Log()
        self.fee = set_fee(self.returns)  # monthly fee
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('sav')

    def get_value_usd(self):
        return str(self.value)

    def update_value(self):
        current_date = get_date()
        months = current_date[1] - self.last_update[1]
        if current_date[0] < self.shift_date:
            months -= 1
        self.value = self.value * (pow((1 + self.returns), months))
        self.value = self.value - self.fee * months

    def deposit(self, amount):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            confirm = True
            response_code = 1
            self.value = self.value + amount
            self.ledger.append(Entry('d', amount, get_date(), -1, -1))

        return confirm, response_code

    def withdraw(self, amount):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            if self.value >= amount:
                confirm = True
                response_code = 1
                self.value = self.value - amount
                self.ledger.append(Entry('w', amount, get_date(), -1, -1))
            else:
                response_code = -3
                confirm = False

        return confirm, response_code

    def transfer(self, amount, target_account, target_dep):
        confirm = True
        target_index = -1
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
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
                if target_dep == 'none':
                    if loc_type_table.in_table(target_index) == 'sav':
                        Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                    elif loc_type_table.in_table(target_index) == 'reg':
                        Accounts.log[target_index].value['USD'] = Accounts.log[target_index].value['USD'] + amount
                    if loc_type_table.in_table(target_index) == 'bus':
                        response_code = -7  # account is of business type but department name is set to 'none'
                        confirm = False
                    else:
                        self.value = self.value - amount
                        self.ledger.append(
                            Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, -1))
                        Accounts.log[target_index].ledger.append(
                            Entry('tt', amount, get_date(), self.account_number, -1))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.value = self.value - amount
                            self.ledger.append(
                                Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, target_dep))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('tt', amount, get_date(), self.account_number, -1))
                        else:
                            response_code = -6  # department name does not exist
                            confirm = False
                    else:
                        response_code = -5  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = -4  # insufficient funds
                confirm = False

        return confirm, response_code


class BusinessAccount:  # object properties: company_name, departments_array, account_number, ledger
    def __init__(self, company_name, department_names):  # department_name is a list of names for each department
        self.company_name = company_name
        self.departments = {}
        self.account_number = assign_account_number()
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('bus')
        for name in department_names:
            # each department is assigned a tuple containing a value table, a ledger, and a trade ledger
            self.departments[name] = (create_value_table(), Log(), Log())

    def get_value_usd(self):
        total = 0
        for dep_name in self.departments.keys():
            for curr in self.departments[dep_name][0].keys():
                total += currency_rates(curr, 'USD', self.departments[dep_name][0][curr])
        return str(total)

    def trade_currency(self, dep_name, source_cur, target_cur, amount):
        confirm = True
        target_index = -1
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        else:
            confirm = False
            if dep_name in self.departments.keys():
                if (source_cur in self.departments[dep_name][0].keys()) and (target_cur in self.departments[dep_name][0].keys()):
                    if self.departments[dep_name][0][source_cur] >= amount:
                        self.departments[dep_name][0][source_cur] = self.departments[dep_name][0][source_cur] - amount
                        self.departments[dep_name][0][target_cur] = self.departments[dep_name][0][target_cur] + currency_rates(source_cur, target_cur, amount)
                        self.departments[dep_name][2].append(
                            TradeEntry(source_cur, target_cur, amount, get_date(), currency_rates(source_cur, target_cur, 1)))
                        confirm = True
                    else:
                        response_code = -3  # insufficient funds
                else:
                    if (source_cur not in self.departments[dep_name][0].keys()) and (target_cur in self.departments[dep_name][0].keys()):
                        response_code = -4  # source currency not found
                    elif (source_cur in self.departments[dep_name][0].keys()) and (target_cur not in self.departments[dep_name][0].keys()):
                        response_code = -5  # target currency not found
                    else:
                        response_code = -6  # source and target currencies not found
            else:
                response_code = -7  # department name not found (input error)

        return confirm, response_code

    def transfer(self, amount, source_dep, target_account, target_dep):
        confirm = True
        target_index = -1
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
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
            if source_dep not in self.departments.keys():
                response_code = -8  # origin department does not exist
                confirm = False
        if confirm:
            response_code = 1
            if self.departments[source_dep][0]['USD'] >= amount:
                if target_dep == 'none':
                    if loc_type_table.in_table(target_index) == 'sav':
                        Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                    elif loc_type_table.in_table(target_index) == 'reg':
                        Accounts.log[target_index].value['USD'] = Accounts.log[target_index].value['USD'] + amount
                    if loc_type_table.in_table(target_index) == 'bus':
                        response_code = -7  # account is of business type but department name is set to 'none'
                        confirm = False
                    else:
                        self.departments[source_dep][0]['USD'] = self.departments[source_dep][0]['USD'] - amount
                        self.departments[source_dep][1].append(
                            Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, -1))
                        Accounts.log[target_index].ledger.append(
                            Entry('tt', amount, get_date(), self.account_number, source_dep))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.departments[source_dep][0]['USD'] = self.departments[source_dep][0]['USD'] - amount
                            self.departments[source_dep][1].append(
                                Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, target_dep))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('tt', amount, get_date(), self.account_number, source_dep))
                        else:
                            response_code = -6  # department name does not exist
                            confirm = False
                    else:
                        response_code = -5  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = -4  # insufficient funds
                confirm = False

        return confirm, response_code

    def inner_transfer(self, source_dep, target_dep, amount):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        elif not ((source_dep in self.departments.keys()) and (target_dep in self.departments.keys())):
            if source_dep not in self.departments.keys():
                response_code = -3  # source dep does not exist
            else:
                response_code = -4  # target dep does not exist
            confirm = False
        if confirm:
            if self.departments[source_dep][0]['USD'] >= amount:
                self.departments[source_dep][0]['USD'] = self.departments[source_dep][0]['USD'] - amount
                self.departments[target_dep][0]['USD'] = self.departments[target_dep][0]['USD'] + amount
                self.departments[source_dep][1].append(Entry('tfi', amount, get_date(), -1, target_dep))
                self.departments[target_dep][1].append(Entry('tti', amount, get_date(), -1, source_dep))
            else:
                confirm = False
                response_code = -5  # insufficient funds

        return confirm, response_code

    def deposit(self, amount, dep_name):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        elif dep_name not in self.departments.keys():
            response_code = -3  # dep name does not exist
            confirm = False
        else:
            response_code = 1
            self.departments[dep_name][0]['USD'] = self.departments[dep_name][0]['USD'] + amount
            self.departments[dep_name][1].append(Entry('d', amount, get_date(), -1, -1))

        return confirm, response_code

    def withdraw(self, amount, dep_name):
        confirm = True
        response_code = 0
        if not validate_number(amount):
            response_code = -2  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = -1  # amount null or negative
        if response_code == -1 or response_code == -2:
            confirm = False
        elif dep_name not in self.departments.keys():
            response_code = -4  # dep name does not exist
            confirm = False
        else:
            if self.departments[dep_name][0]['USD'] >= amount:
                response_code = 1
                self.departments[dep_name][0]['USD'] = self.departments[dep_name][0]['USD'] - amount
                self.departments[dep_name][1].append(Entry('d', amount, get_date(), -1, -1))
            else:
                confirm = False
                response_code = -3  # insufficient funds

        return confirm, response_code

    def add_department(self, dep_name):
        confirm = False
        response_code = 0
        if dep_name not in self.departments.keys():
            if validate_string(dep_name):
                self.departments[dep_name] = (create_value_table(), Log(), Log())
                confirm = True
            else:
                response_code = -2  # department name not valid
        else:
            response_code = -1  # department name already exists

        return confirm, response_code


# functions
def set_fee(returns):
    if returns == returns_premium:
        return 100
    elif returns == returns_medium:
        return 80
    elif returns == returns_minimum:
        return 50
    return -1


def currency_rates(cur1, cur2, amount):
    try:
        return round(converter.CurrencyRates().convert(cur1, cur2, amount), 3)
    except converter.RatesNotAvailableError:
        amount_new = amount / last_rates[cur1] * last_rates[cur2]
        return round(amount_new, 3)


def assign_account_number():
    # Generate a random number between 1000000000 and 9999999999
    number = random.randint(1000000000, 9999999999)

    # Check if the random number has been generated before
    while number in existing_account_numbers:
        # If it has, generate a new random number
        number = random.randint(1000000000, 9999999999)

    # Add the random number to the set of generated numbers
    existing_account_numbers.add(number)

    return number


def hash_function(param) -> int:
    input_str = str(param)
    ascii_values = [ord(ch) for ch in input_str]
    values = []
    for i in range(len(ascii_values)):
        values.append((i * 123854 ^ ascii_values[i] * 984) | (multiple(ascii_values)))
    val = ((sum_vec(values) - 2587465) & (951456 * (multiple(values)) + 456 * sum_vec(values)))
    if val < 0:
        val = val ^ (sum_vec(ascii_values) + 95813)
    factor = (((sum_vec(values) + 15984354) | (multiple(values) + 10000009814008)) & ((sum_vec(ascii_values) + 87515557) ^ (multiple(ascii_values) * 8558224)))
    new_val = abs(val ^ factor)
    if new_val % 10 != 9:
        new_val += 1
    else:
        new_val += 11
    shifts = 64 - math.floor(math.log10(new_val)) + 1
    new_val = new_val << shifts
    temp = digit_count(new_val)
    if temp == 18:
        new_val = 100 * new_val
    elif temp == 20:
        new_val = new_val // 10
    if new_val < 0:
        return abs(10 * new_val)
    return limit_length(abs(new_val))


def create_table_output(value_table):
    output = '<table>' + '<tr>'
    output += '<th>Currency</th>' + '<th> | Current Value</th>' + '<th> | Exchange Rate to USD</th>' + '</tr>'
    output += '<tr><td> | USD</td><td> | ' + str(value_table['USD']) + '</td>' + '<td> | ' + str(currency_rates('USD', 'USD', 1)) + '</td></tr>'
    for key in value_table.keys():
        if value_table[key] != 0 and key != 'USD':
            output += '<tr><td> | ' + key + '</td>'
            output += '<td> | ' + str(value_table[key]) + '</td>'
            output += '<td> | ' + str(currency_rates(key, 'USD', 1)) + '</td></tr>'
    output += '</table>'

    return output


# fix
def send_recovery_email(email_address):
    # create an SMTP server object
    mail_server = smtplib.SMTP('smtp.example.com', 587)

    # starting server encryption
    mail_server.starttls()

    # create the email data, including the email content and recipients
    message = """\
    From: FinCloud@server.com
    To: {}
    Subject: Recovery for FinCloud account

    Recovery code for your account: {}""".format(email_address, generate_code())

    # send the email using the server object
    mail_server.sendmail('FinCloud@server.com', [email_address], message)


# fix
def send_confirmation_email(email_address):
    # create an SMTP server object
    mail_server = smtplib.SMTP('smtp.example.com', 587)

    # starting server encryption
    mail_server.starttls()

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
    name_index = name_table.in_table(attempt)  # attempt - client's attempt at account name/number
    num_index = number_table.in_table(attempt)
    # set response
    if (name_index == -1) and (num_index == -1):
        response_code = -1  # incorrect name/number
    elif (name_index != -1) and (num_index == -1):
        if pass_table.in_table(name_index) == hash_function(code_attempt):
            response_code = 1
            verify = True
        else:
            response_code = -2  # incorrect password
    elif (num_index != -1) and (name_index == -1):
        if pass_table.in_table(num_index) == hash_function(code_attempt):
            response_code = 1
            verify = True
        else:
            response_code = -2  # incorrect password
    else:
        response_code = -3  # system error (user's attempt matches both a name and a number -> impossible situation)

    # setting index of account
    index = -1
    if verify:
        index = name_table.in_table(attempt)
        if index == -1:
            index = number_table.in_table(attempt)

    # return values (verification answer, response code)
    return verify, response_code, index


def create_savings_account(account_name, account_code, phone_num, returns):
    confirm = False
    user_name = account_name
    response_code = 0

    # checking validity and availability of account name and code
    if validate_string(account_name) and validate_string(account_code):
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = 1  # account name and code are confirmed
        else:
            response_code = -4  # account name is unavailable
    else:
        if (not validate_string(account_name)) and validate_string(account_code):
            response_code = -1  # name invalid
        else:
            response_code = -2  # code invalid
        if not (validate_string(account_name) or validate_string(account_code)):
            response_code = -3  # name and code invalid
    if confirm:
        if returns not in [returns_premium, returns_medium, returns_minimum]:
            response_code = -5
            confirm = False
        if not validate_phone_number(phone_num):
            response_code = -6
            confirm = False
        if phone_name_table.in_table(hash_function(phone_num)) != -1:
            response_code = -7
            confirm = False
    if confirm:
        # add account details to tables
        name_table.add_key_index(account_name)
        pass_table.add_index_value(hash_function(account_code))
        phone_name_table.add_key_value(hash_function(phone_num), account_name)

        # create account object
        new_account = SavingsAccount(returns)
        account_name = "ac" + str(name_table.in_table(account_name))
        globals()[account_name] = new_account
        Accounts.append(globals()[account_name])

    # return values (confirmation, account index, response code)
    return confirm, name_table.in_table(user_name), response_code


def create_checking_account(account_name, account_code, phone_num):  # returns confirms, account index, response code
    confirm = False  # initialize return value
    user_name = account_name  # saving initial name of account
    response_code = 0

    # checking validity and availability of account name and code
    if validate_string(account_name) and validate_string(account_code):
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = 1  # account name and code are confirmed
        else:
            response_code = -4  # account name is unavailable
    else:
        if (not validate_string(account_name)) and validate_string(account_code):
            response_code = -1  # name invalid
        if (not validate_string(account_code)) and validate_string(account_name):
            response_code = -2  # code invalid
        if not (validate_string(account_name) or validate_string(account_code)):
            response_code = -3  # name and code invalid
    if confirm:
        if not validate_phone_number(phone_num):
            response_code = -5  # phone number not valid
            confirm = False
        elif phone_name_table.in_table(hash_function(phone_num)) != -1:
            response_code = -6  # phone number already registered
            confirm = False
    if confirm:
        # add account details to tables
        name_table.add_key_index(account_name)
        pass_table.add_index_value(hash_function(account_code))
        phone_name_table.add_key_value(hash_function(phone_num), account_name)

        # create account object
        new_account = Account()
        account_name = "ac" + str(name_table.in_table(account_name))
        globals()[account_name] = new_account
        Accounts.append(globals()[account_name])

    # return values (confirmation, account index, response code)
    return confirm, name_table.in_table(user_name), response_code


def create_business_account(account_name, company_name, account_code, phone_num):
    confirm = False  # initialize return value
    user_name = account_name  # saving initial name of account
    response_code = 0

    # checking validity and availability of account name and code
    ac_name_valid = validate_string(account_name)
    ac_code_valid = validate_string(account_code)
    if check_for_spaces(company_name):
        company_name = organize_comp_name(company_name)
    comp_name_valid = validate_comp_name(company_name)

    if ac_name_valid and ac_code_valid and comp_name_valid:
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = 1  # account name and code are confirmed
        else:
            response_code = -10  # account name is unavailable
    else:
        if not ac_name_valid and ac_code_valid and comp_name_valid:
            response_code = -1  # name invalid
        elif ac_name_valid and not ac_code_valid and comp_name_valid:
            response_code = -2  # code invalid
        elif ac_name_valid and ac_code_valid and not comp_name_valid:
            response_code = -3  # comp name invalid
        elif not ac_name_valid and not ac_code_valid and comp_name_valid:
            response_code = -4  # name and code invalid
        elif not ac_name_valid and ac_code_valid and not comp_name_valid:
            response_code = -5  # name and comp name invalid
        elif ac_name_valid and not ac_code_valid and not comp_name_valid:
            response_code = -6  # code and comp name invalid
        elif not (ac_name_valid or ac_code_valid or comp_name_valid):
            response_code = -7  # name and code and comp name invalid
    if confirm:
        if not validate_phone_number(phone_num):
            response_code = -8  # phone number not valid
            confirm = False
        elif phone_name_table.in_table(hash_function(phone_num)) != -1:
            response_code = -9  # phone number already registered
            confirm = False
    if confirm:
        # add account details to tables
        name_table.add_key_index(account_name)
        pass_table.add_index_value(hash_function(account_code))
        phone_name_table.add_key_value(hash_function(phone_num), account_name)

        # create account object
        new_account = BusinessAccount(company_name, [])
        account_name = "ac" + str(name_table.in_table(account_name))
        globals()[account_name] = new_account
        Accounts.append(globals()[account_name])

    # return values (confirmation, account index, response code)
    return confirm, name_table.in_table(user_name), response_code


# HTTP request handler for HTTP server
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

    def system_error(self):  # redirect to main page, set redirect flag to true, set response code to -1 to display error
        if self.client_address[0] in data.current_account.keys():
            data.delete_ca(self.client_address[0])
        data.alter_rf(self.client_address[0], True)
        data.alter_re(self.client_address[0], -1)
        self.redirect('/')

    def timeout_session(self):
        if self.client_address[0] in data.current_account.keys():
            data.delete_ca(self.client_address[0])
        data.alter_rf(self.client_address[0], True)
        data.alter_re(self.client_address[0], -2)
        data.alter_brf(self.client_address[0], False)
        self.redirect('/')

    def do_GET(self):

        if self.client_address[0] not in data.redirect_flags.keys():
            data.alter_rf(self.client_address[0], False)

        if self.client_address[0] not in history.keys():
            history[self.client_address[0]] = Log()

        history[self.client_address[0]].append(ConnectionEntry('get', get_precise_time()))

        if self.client_address[0] not in data.background_redirect_flags.keys():
            data.alter_brf(self.client_address[0], False)

        # check background redirect flag
        if data.background_redirect_flags[self.client_address[0]]:
            self.timeout_session()

        if self.client_address[0] not in addresses:
            addresses.append(self.client_address[0])

        if self.path.endswith('/'):
            self.start()
            self.clear()
            output = '<html><body>'
            self.wfile.write(bytes('<head><title>FinCloud.com</title></head>', "utf-8"))
            output += '<h1>FinCloud - A modern solution for you</h1>'
            output += '<h3><a href="/About">Learn about us</a></h3>'
            output += '<h3><a href="/login">Sign in</a></h3>'
            output += '</br>' + '</br>'
            output += '<h2>Discover Our Financial Cloud</h2>'
            output += 'To use Financial Cloud ' + '<a href="/guest/cloud">Click here</a>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.redirect_flags[self.client_address[0]] = False
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>System error. Please try again later.</h4>'
                if response_code == -2:
                    output += '<h4>Session timed out.</h4>'
                data.alter_re(self.client_address[0], 0)
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
            output += '<h5><a href="/forgot">' + temp + '</a></h5>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Account name/number is incorrect. Please try again.</h4>'
                elif response_code == -2:
                    output += '<h4>Password is incorrect. Please try again.</h4>'
                elif response_code == -3:
                    output += '<h4>System error. Please try again at a later time.</h4>'
                elif response_code == 2:
                    output += '<h4>Account recovered. Password reset.</h4>'
                elif response_code == 3:
                    output += '<h4>New account created.</h4>'
                elif response_code == 4:
                    output += '<h4>Session timed out. Log in again.'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '________      or      ________' + '</br></br></br>'
            output += 'New to FinCloud? ' + '<a href="/new">Get started</a></br></br></br>'
            output += 'Return to home page ' + '<a href="/">Here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/logout'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            output += '<h1>Your Account: ' + account_name + '</h1>'
            output += '<h2><Are you sure you want to log out of your account?</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/logout">'
            output += '<input type="submit" value="Confirm">' + '</form>'
            output += '<h4><a href="/account/home">Cancel logout</a></h4>'
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
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Phone number does not exist in out system.</h4>'
                elif response_code == -2:
                    output += '<h4>Account name/number incorrect.</h4>'
                elif response_code == -3:
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
            output += '<h4><a href="/new/savings">Personal Savings Account</a></h4>'
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
            output += '<h2>Create Your Account</h2>'
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
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Account name is invalid. Please try again.</h4>'
                elif response_code == -2:
                    output += '<h4>Account code is invalid: do not use symbols. Please try again.</h4>'
                elif response_code == -3:
                    output += '<h4>Account name and code are invalid: do not use symbols.' \
                              ' Please try again.</h4>'
                elif response_code == -4:
                    output += '<h4>An account with this name already exists. Please try again.</h4>'
                elif response_code == -5:
                    output += '<h4>Phone number not valid.</h4>'
                elif response_code == -6:
                    output += '<h4>Phone number already registered to an existing account.</h4>'
                elif response_code == -7:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/new/savings'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open a personal savings account</h1>'
            output += 'Personal savings accounts allow for safe and profitable storage for your savings.' \
                      ' Our personal savings accounts provide preset annual returns guaranteed and backed by our funds.'
            output += '<h4>Options for account returns:</h4>'
            output += 'Premium: 4% annual returns, $100 monthly fee' + '</br>'
            output += 'Regular: 2.75% annual returns, $80 monthly fee' + '</br>'
            output += 'Safe: 2% annual returns, $50 monthly fee' + '</br>'
            output += '</br></br></br>'
            output += '<h2>Create Your Account</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/new/savings">'
            output += 'Enter a name for your account: ' + '<input name="user" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter a password for your account: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += 'Select preferred returns for your savings account: '
            output += '<select id="returns" name="returns">'
            output += '<option value = "premium">Premium - 4% annually</option>'
            output += '<option value = "medium">Regular - 2.75% annually</option>'
            output += '<option value = "minimum">Safe - 2% annually</option>'
            output += '</select>'
            output += '</br></br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Account name is invalid. Please try again.</h4>'
                elif response_code == -2:
                    output += '<h4>Account code is invalid: do not use symbols. Please try again.</h4>'
                elif response_code == -3:
                    output += '<h4>Account name and code are invalid: do not use symbols.' \
                              ' Please try again.</h4>'
                elif response_code == -4:
                    output += '<h4>An account with this name already exists. Please try again.</h4>'
                if response_code == -5:
                    output += '<h4>Returns are invalid for this type of account.</h4>'
                if response_code == -6:
                    output += '<h4>Phone number not valid.</h4>'
                if response_code == -7:
                    output += '<h4>Phone number already registered to an existing account.</h4>'
                if response_code == -8:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/new/business'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open a business account</h1>'
            output += 'Business accounts allow for optimal and dynamic management of company resources.' \
                      'Our business account offer distribution of funds throughout company departments, ' \
                      'while also offering the option to invest company capital in international currencies.'
            output += '</br>' + '</br>'
            output += '<h2>Create Your Account</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/new/business">'
            output += 'Enter the name of the company: ' + '<input name="comp_name" type="text">' + '</br></br>'
            output += 'Enter a name for your account: ' + '<input name="user" type="text">' + '</br></br>'
            output += 'Enter a password for your account: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br></br>'
            output += 'After opening the account, you will have the option to open departments and ' \
                      'distribute company funds' + '</br></br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br>'

            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Account name is invalid. Please try again.</h4>'
                if response_code == -2:
                    output += '<h4>Account code is invalid. Please try again.</h4>'
                if response_code == -3:
                    output += '<h4>Company name is invalid. Please try again.</h4>'
                if response_code == -4:
                    output += '<h4>Account name and code are invalid. Please try again.</h4>'
                if response_code == -5:
                    output += '<h4>Account name and company name are invalid. Please try again.</h4>'
                if response_code == -6:
                    output += '<h4>Account code and company name are invalid. Please try again.</h4>'
                if response_code == -7:
                    output += '<h4>Invalid data (account name, account code, company name). Please try again.</h4>'
                if response_code == -8:
                    output += '<h4>Phone number is invalid. Please try again.</h4>'
                if response_code == -9:
                    output += '<h4>Phone number already registered to an existing account.</h4>'
                if response_code == -10:
                    output += '<h4>Account name already registered to an existing account.</h4>'
                if response_code == -11:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/admin_access/' + str(data.admin_token)):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<a href="/admin_access/' + str(data.admin_token) + '/account_list">Accounts list</a></br></br>'
            output += '<a href="/admin_access/' + str(data.admin_token) + '/cloud_watch">Cloud allocations</a></br></br>'
            output += '<a href="/account/logout">Log out</a>'
            self.wfile.write(output.encode())

        if self.path.endswith('/admin_access/' + str(data.admin_token) + '/account_list'):
            self.start()
            self.clear()
            output = '<table>' + '<tr>'
            output += '<th>Index</th>' + '<th> | Account name</th>' + '<th> | Account number</th>' + '<th> | Account type</th>' + '<th> | Total account value in USD</th>' + '</tr>'
            for i in range(len(Accounts.log)):
                output += '<tr><td> | ' + str(i) + '</td>'
                output += '<td> | <a href="/admin_access/account_list/' + name_table.get_key(i) + '/' + str(data.admin_token) + '/account_watch/details">' + name_table.get_key(i) + '</a></td>'
                output += '<td> | ' + str(number_table.get_key(i)) + '</td>'
                output += '<td> | ' + loc_type_table.in_table(i) + '</td>'
                output += '<td> | ' + Accounts.log[i].get_value_usd() + '</td></tr>'
            output += '</table>'
            self.wfile.write(output.encode())

        if self.path.endswith(str(data.admin_token) + '/account_watch/details'):
            pass

        if self.path.endswith('/admin_access/' + str(data.admin_token) + '/cloud_watch'):
            pass

        if self.path.endswith('/account/home'):
            if name_table.get_key(data.current_account[self.client_address[0]]) == 'Admin':
                data.admin_token = hash(generate_code())
                self.redirect('/admin_access/' + str(data.admin_token))
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            account_number = str(number_table.get_key(ac_index))
            output += '<h1>Account name: ' + account_name + '</h1>'
            output += '<h2>Account number: ' + account_number + '</h2>'
            val = Accounts.log[ac_index].get_value_usd()
            if loc_type_table.body[ac_index] == 'bus':
                comp_name = str(Accounts.log[ac_index].company_name)
                output += '<h2>Company name: ' + comp_name + '</h2>'
            output += '</br><h2>Current value in USD: ' + val + '</h2>'
            if loc_type_table.body[ac_index] == 'reg':
                output += '<h3>See current holdings ' + '<a href="/account/holdings">Here</a></h3>'
            elif loc_type_table.body[ac_index] == 'bus':
                output += '<h3>See company departments ' + '<a href="/account/business/departments">Here</a></h3>'
            if loc_type_table.body[ac_index] == 'bus':
                output += '</br>'
                output += '<h3>Open a new department for your business account ' + \
                          '<a href="/account/business/open_dep">now</a></h3>'
            output += '</br>' + '</br>'

            output += '<h3>To deposit funds ' + '<a href="/account/deposit_funds">Click here</a></h3>'
            output += '<h3>To withdraw funds ' + '<a href="/account/withdraw_funds">Click here</a></h3>'
            output += '<h3>To transfer funds to other accounts ' + \
                      '<a href="/account/transfer_funds">Click here</a></h3>'
            if loc_type_table.body[ac_index] == 'bus':
                output += '</br>'
                output += '<h3><a href="/account/business/inner_transfer">Transfer between business departments</a></h3>'
            output += '</br>'
            output += '<h3>To use Financial Cloud ' + '<a href="/account/cloud">Click here</a></h3>'
            output += '</br>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == 2:
                    output += '<h4>Deposit confirmed.</h4>'
                if response_code == 3:
                    output += '<h4>Withdrawal confirmed.</h4>'
                if response_code == 4:
                    output += '<h4>Transfer confirmed.</h4>'
                if response_code == 5:
                    output += '<h4>Departmental transfer processed.</h4>'
                if response_code == 6:
                    output += '<h4>New department established.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br></br>' + '<h4><a href="/account/logout">Log out</a></h4>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/deposit_funds'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output += '<h1>Deposit Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/deposit_funds">'
            output += 'Enter amount to deposit: ' + '<input name="amount" type="text">' + '</br></br>'
            if loc_type_table.body[ac_index] == 'bus':
                output += 'Enter department to deposit to: ' + '<input name="dep_name" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                if response_code == -2:
                    output += '<h4>Invalid input (amount).</h4>'
                if response_code == -3:
                    output += '<h4>Department name not found</h4>'
                data.alter_re(self.client_address[0], False)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/withdraw_funds'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output += '<h1>Withdraw Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/withdraw_funds">'
            output += 'Enter amount to withdraw: ' + '<input name="amount" type="text">' + '</br></br>'
            if loc_type_table.body[ac_index] == 'bus':
                output += 'Enter department to withdraw from: ' + '<input name="dep_name" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                if response_code == -2:
                    output += '<h4>Invalid input (amount).</h4>'
                if response_code == -3:
                    output += '<h4>Account value in USD is insufficient for this withdrawal.</h4>'
                if response_code == -4:
                    output += '<h4>Department name not found</h4>'
                data.alter_re(self.client_address[0], False)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/transfer_funds'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.body[ac_index]
            output = '<html><body>'
            output += '<h1>Transfer Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/transfer_funds">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Enter name/number of account to transfer to: ' + '<input name="target" type="text">' + '</br>'
            output += 'If you are transferring to a business account, enter name of department to transfer to: ' + \
                      '<input name="target_dep" type="text">' + '</br>'
            if ac_type == 'bus':
                output += '</br>' + 'Enter name of department to transfer from: ' + \
                          '<input name="source_dep" type="text">' + '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                if response_code == -2:
                    output += '<h4>Invalid input (amount).</h4>'
                if response_code == -3:
                    output += '<h4>Target account not found.</h4>'
                if response_code == -4:
                    output += '<h4>Account value in USD is insufficient for this transfer.</h4>'
                if response_code == -5:
                    output += '<h4>Target department set though target account is not a business account.</h4>'
                if response_code == -6:
                    output += '<h4>Target department not found.</h4>'
                if response_code == -7:
                    output += '<h4>Target department not set (target account is a business account).</h4>'
                if response_code == -8:
                    output += '<h4>Source department not found.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/holdings'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            output = '<html><body>'
            output += '<h1>Account Holdings</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h2>Current currency holdings:</h2>'

            value_table = Accounts.log[ac_index].value
            output += create_table_output(value_table)

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == 2:
                    output += '<h4>Currency trade confirmed.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br></br>' + 'To trade and invest in different currencies ' + \
                      '<a href="/account/holdings/trade_currencies">Click here</a>' + '</br></br>'
            output += 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/business/departments'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            comp_name = Accounts.log[ac_index].company_name
            output = '<html><body>'
            output += '<h1>Business Departments</h1>' + '</br>'
            output += '<h2>Company: ' + comp_name + '</h2>'
            output += '<h2>Account name: ' + account_name + '</h2>' + '</br></br>'
            output += '<h1>Company Departments and holdings: </h1>'
            if len(Accounts.log[ac_index].departments.keys()) == 0:
                output += '<h3>Account has no departments.</h3></br></br>'
            for dep in Accounts.log[ac_index].departments.keys():
                output += '</br><h2>Holdings for department "' + dep + '":</h2>'
                output += create_table_output(Accounts.log[ac_index].departments[dep][0]) + '</br>'
                output += 'Trade currencies with ' + dep + ' department capital: ' + \
                          '<a href="/account/business/departments/' + dep + '/invest_capital/trade_currencies">Here</a></br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == 2:
                    output += '<h4>Currency trade confirmed.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/holdings/trade_currencies'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            value_table = Accounts.log[ac_index].value
            available_currencies = [currency for currency in value_table.keys() if value_table[currency] > 0]
            output = '<html><body>'
            output += '<h1>Currencies - Trade & Invest</h1>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += 'We offer you the opportunity to distribute and invest your account capital throughout' \
                      ' multiple international currencies. '
            output += 'Transfer funds between an array of currencies at market value without additional cost.' + '</br></br>'
            if len(available_currencies) == 0:
                output += '<h2>No funds available.</h2></br>'
            output += '<h2>Trade currencies:</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/holdings/trade_currencies">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Select currency to transfer from: '
            output += '<select id="source_cur" name="source_cur">'
            for curr in available_currencies:
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br>'
            output += 'Select currency to transfer to: '
            output += '<select id="source_cur" name="target_cur">'
            for curr in value_table.keys():
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br></br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                if response_code == -2:
                    output += '<h4>Invalid input (amount).</h4>'
                if response_code == -3:
                    output += '<h4>Insufficient funds in source currency.</h4>'
                if response_code == -4:
                    output += '<h4>Source currency not found.</h4>'
                if response_code == -5:
                    output += '<h4>Target currency not found.</h4>'
                if response_code == -6:
                    output += '<h4>Source and target currencies not found.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account holdings page ' + '<a href="/account/holdings">Click here</a>'
            output += '</br>' + '</br>' + 'Return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/invest_capital/trade_currencies'):
            self.start()
            self.clear()
            url_parsed = self.path.split('/')
            dep_name = url_parsed[4]
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            value_table = Accounts.log[ac_index].departments[dep_name][0]
            available_currencies = [currency for currency in value_table.keys() if value_table[currency] > 0]
            output = '<html><body>'
            output += '<h1>Currencies - Trade & Invest</h1>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h2>Department name: ' + dep_name + '</h2>'
            output += 'We offer you the opportunity to distribute and invest your account capital throughout' \
                      ' multiple international currencies. '
            output += 'Transfer funds between an array of currencies at market value without additional cost.' + '</br></br>'
            if len(available_currencies) == 0:
                output += '<h2>No funds available.</h2></br>'
            output += '<h2>Trade currencies:</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/business/departments/' + dep_name + '/invest_capital/trade_currencies">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Select currency to transfer from: '
            output += '<select id="source_cur" name="source_cur">'
            for curr in available_currencies:
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br>'
            output += 'Select currency to transfer to: '
            output += '<select id="source_cur" name="target_cur">'
            for curr in value_table.keys():
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br></br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                if response_code == -2:
                    output += '<h4>Invalid input (amount).</h4>'
                if response_code == -3:
                    output += '<h4>Insufficient funds in source currency.</h4>'
                if response_code == -4:
                    output += '<h4>Source currency not found.</h4>'
                if response_code == -5:
                    output += '<h4>Target currency not found.</h4>'
                if response_code == -6:
                    output += '<h4>Source and target currencies not found.</h4>'
                if response_code == -7:
                    self.system_error()
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account holdings page ' + '<a href="/account/business/departments">Click here</a>'
            output += '</br>' + '</br>' + 'Return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/business/inner_transfer'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            account_number = str(number_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output = '<html><body>'
            output += '<h1>Departmental Transfer</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Account number: ' + account_number + '</h3>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/business/inner_transfer">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Enter name of department to transfer from: ' + '<input name="source_dep" type="text">' + '</br>'
            output += 'Enter name of department to transfer to: ' + '<input name="target_dep" type="text">' + '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                if response_code == -2:
                    output += '<h4>Invalid input (amount).</h4>'
                if response_code == -3:
                    output += '<h4>Source department not found.</h4>'
                if response_code == -4:
                    output += '<h4>Target department not found.</h4>'
                if response_code == -5:
                    output += '<h4>Department value in USD is insufficient for this transfer.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/cloud'):
            pass

        if self.path.endswith('/account/cloud/allocate'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.body[ac_index]
            output = '<html><body>'
            output += '<h1>Allocate Funds With Fincloud</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/cloud/allocate">'
            output += 'Enter amount to allocate: ' + '<input name="amount" type="text">' + '</br>'
            if ac_type == 'bus':
                output += '</br>' + 'Enter name of department to allocate from: ' + '<input name="source_dep" type="text">' + '</br>'
            output += 'Enter allocation number (used to access funds): ' + '<input name="allocation_id" type="text">' + '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                # add options for response codes
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/account/cloud/withdraw'):
            pass

        if self.path.endswith('/guest/cloud'):
            pass

        if self.path.endswith('/account/business/open_dep'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            output += '<h1>Your Account: ' + account_name + '</h1>'
            comp_name = str(Accounts.log[ac_index].company_name)
            output += '<h1>Company: ' + comp_name + '</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/business/open_dep">'
            output += 'Enter name for new department: ' + '<input name="new_dep" type="text">'
            output += '</br></br>'
            output += '<input type="submit" value="Open department">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.responses[self.client_address[0]]
                if response_code == -1:
                    output += '<h4>Department name already exists.</h4>'
                if response_code == -2:
                    output += '<h4>Department name invalid. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

    def do_POST(self):

        if self.client_address[0] not in addresses or self.client_address[0] not in history.keys():
            self.system_error()

        history[self.client_address[0]].append(ConnectionEntry('post', get_precise_time()))

        # check background redirect flag
        if data.background_redirect_flags[self.client_address[0]]:
            self.timeout_session()

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
                    self.redirect('/account/home')
                else:
                    data.alter_re(self.client_address[0], response_code)
                    data.alter_rf(self.client_address[0], True)
                    self.redirect('/login')
            else:
                self.system_error()

        if self.path.endswith('/account/logout'):
            # logout page does not request input, any post request signals logging out of account
            data.delete_ca(self.client_address[0])
            self.redirect('/login')

        if self.path.endswith('/new/savings'):
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
                returns_str = fields.get('returns')[0]
                returns_dict = {'premium': 4, 'medium': 2.75, 'safe': 2}  # to determine returns in numbers
                returns = returns_dict[returns_str]
                # create account with user input
                if code == code_confirm:
                    confirm, index, response_code = create_savings_account(account_name, code, phone_number, returns)
                    if confirm:
                        data.alter_re(self.client_address[0], 3)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/login')
                    else:
                        data.alter_re(self.client_address[0], response_code)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/new/savings')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], -8)
                    self.redirect('/new/savings')
            else:
                self.system_error()

        if self.path.endswith('/new/business'):
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
                company_name = fields.get('comp_name')[0]
                # create account with user input
                if code == code_confirm:
                    confirm, index, response_code = create_business_account(account_name, company_name, code, phone_number)
                    if confirm:
                        data.alter_re(self.client_address[0], 3)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/login')
                    else:
                        data.alter_re(self.client_address[0], response_code)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/new/business')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], -11)
                    self.redirect('/new/business')
            else:
                self.system_error()

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
                    confirm, index, response_code = create_checking_account(account_name, code, phone_number)
                    if confirm:
                        data.alter_re(self.client_address[0], 3)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/login')
                    else:
                        data.alter_re(self.client_address[0], response_code)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/new/checking')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], -7)
                    self.redirect('/new/checking')
            else:
                self.system_error()

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
                self.system_error()

        if self.path.endswith('/account/deposit_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                amount = fields.get('amount')[0]
                is_bus_account = False
                if loc_type_table.body[data.current_account[self.client_address[0]]] == 'bus':
                    is_bus_account = True
                index = data.current_account[self.client_address[0]]
                if not is_bus_account:
                    confirm, response_code = Accounts.log[index].deposit(amount)
                else:
                    confirm, response_code = Accounts.log[index].deposit(amount, fields.get('dep_name')[0])
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 2)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/deposit_funds')
            else:
                self.system_error()

        if self.path.endswith('/account/withdraw_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                amount = fields.get('amount')[0]
                is_bus_account = False
                if loc_type_table.body[data.current_account[self.client_address[0]]] == 'bus':
                    is_bus_account = True
                ac_index = data.current_account[self.client_address[0]]
                if not is_bus_account:
                    confirm, response_code = Accounts.log[ac_index].withdraw(amount)
                else:
                    confirm, response_code = Accounts.log[ac_index].withdraw(amount, fields.get('dep_name')[0])
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 3)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/withdraw_funds')
            else:
                self.system_error()

        if self.path.endswith('/account/transfer_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                is_bus_account = False
                target_account = fields.get('target')[0]
                target_dep = fields.get('target_dep')[0]
                amount = fields.get('amount')[0]
                if target_dep == "":
                    target_dep = "none"
                ac_index = data.current_account[self.client_address[0]]
                if loc_type_table.body[ac_index] == 'bus':
                    is_bus_account = True
                if not is_bus_account:
                    confirm, response_code = Accounts.log[ac_index].transfer(amount, target_account, target_dep)
                else:
                    confirm, response_code = \
                        Accounts.log[ac_index].transfer(amount, fields.get('source_dep')[0], target_account, target_dep)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 4)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/transfer_funds')
            else:
                self.system_error()

        if self.path.endswith('/account/business/inner_transfer'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                target_dep = fields.get('target_dep')[0]
                source_dep = fields.get('source_dep')[0]
                amount = fields.get('amount')[0]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].inner_transfer(source_dep, target_dep, amount)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 5)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/business/inner_transfer')
            else:
                self.system_error()

        if self.path.endswith('/account/business/open_dep'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                new_dep = fields.get('new_dep')[0]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].add_department(new_dep)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 6)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/business/open_dep')
            else:
                self.system_error()

        if self.path.endswith('/account/holdings/trade_currencies'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                source_cur = fields.get('source_cur')[0]
                target_cur = fields.get('target_cur')[0]
                amount = fields.get('amount')[0]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].trade_currency(amount, source_cur, target_cur)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 2)
                    self.redirect('/account/holdings')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/holdings/trade_currencies')
            else:
                self.system_error()

        if self.path.endswith('/invest_capital/trade_currencies'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                source_cur = fields.get('source_cur')[0]
                target_cur = fields.get('target_cur')[0]
                amount = fields.get('amount')[0]
                url_parsed = self.path.split('/')
                dep_name = url_parsed[4]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].trade_currency(dep_name, source_cur, target_cur, amount)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 2)
                    self.redirect('/account/business/departments')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/business/departments/' + dep_name + '/invest_capital/trade_currencies')
            else:
                self.system_error()

        if self.path.endswith('/account/cloud/allocate'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                allocation_id = fields.get('allocation_id')[0]
                amount = fields.get('amount')[0]
                ac_index = data.current_account[self.client_address[0]]
                if loc_type_table.body[ac_index] == 'bus':
                    dep_name = fields.get('dep_name')[0]
                else:
                    dep_name = "none"
                confirm, response_code = Cloud().allocate(amount, allocation_id, name_table.get_key(ac_index), dep_name)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], 2)
                    self.redirect('/account/cloud')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/cloud/allocate')
            else:
                self.system_error()


# background functions
def session_timing():  # check for session timeout
    while True:
        for ip in addresses:
            if len(history[ip].log) >= 2:
                log_length = len(history[ip].log)
                time1 = history[ip].log[log_length - 2].lst[1]
                time2 = history[ip].log[log_length - 1].lst[1]
                timeDif = time_dif(time1, time2)
                if timeDif >= session_limit:
                    print("time dif above limit")
                    data.alter_brf(ip, True)
                    addresses.remove(ip)
                    history[ip] = Log()

        # for ip in addresses set
        # check if the same ip exists twice in history log
        # if so, check time dif between last two connection entries
        # if time dif is larger than session limit, set background redirect flag to true for the ip
        # if background redirect flag is set to true, delete address from addresses set and reset history log


def savings_update():  # update value in savings accounts
    while True:
        time.sleep(SAVINGS_UPDATE_CYCLE)  # update every 10 min
        for index in loc_type_table.body.keys():
            if loc_type_table.body[index] == 'sav':
                Accounts.log[index].update_value()


def rates_update():  # update last currency rates to use if live rates are not available
    while True:
        time.sleep(RATES_UPDATE_CYCLE)
        for curr in last_rates.keys():
            last_rates[curr] = converter.CurrencyRates().get_rate('USD', curr)


def refresh_admin_credentials():
    while True:
        time.sleep(CREDENTIALS_UPDATE_CYCLE)
        print('Updating credentials')
        new_credentials = str(hash_function(generate_code()))
        pass_table.body[0] = new_credentials
        dir_path = str(os.path.dirname(os.path.abspath(__file__))) + '\\credentials'
        file_path = dir_path + '\\Admin_credentials.txt'
        try:
            os.mkdir(dir_path)
        except FileExistsError:
            pass
        with open(file_path, 'w') as file:
            file.write(new_credentials)


# main - driver function
def main():
    # admin account and credentials setup
    Admin_code = str(hash_function(generate_code()))
    dir_path = str(os.path.dirname(os.path.abspath(__file__))) + '\\credentials'
    file_path = dir_path + '\\Admin_credentials.txt'
    try:
        os.mkdir(dir_path)
    except FileExistsError:
        pass
    with open(file_path, 'w') as file:
        file.write(Admin_code)
    create_checking_account('Admin', Admin_code, 1234567890)
    loc_type_table.body[0] = 'admin'

    # thread management
    print('Starting background threads:')

    # create separate thread for session timings
    session_thread = threading.Thread(target=session_timing)
    # run the process
    session_thread.start()
    session_thread_ID = session_thread.ident
    print('* Session timing thread started at thread id = "' + str(session_thread_ID) + '"')

    # create separate thread for savings updates
    savings_update_thread = threading.Thread(target=savings_update)
    # run the process
    savings_update_thread.start()
    savings_update_thread_ID = savings_update_thread.ident
    print('* Savings account updating thread started at thread ID = "' + str(savings_update_thread_ID) + '"')

    # create separate thread for currency rates updates
    rates_update_thread = threading.Thread(target=rates_update)
    # run the process
    rates_update_thread.start()
    rates_update_thread_ID = rates_update_thread.ident
    print('* Currency rates updating thread started at thread ID = "' + str(rates_update_thread_ID) + '"')

    # create separate thread for admin credentials updates
    credentials_update_thread = threading.Thread(target=refresh_admin_credentials)
    # run the process
    credentials_update_thread.start()
    credentials_update_thread_ID = credentials_update_thread.ident
    print('* Admin credentials updating thread started at thread ID = "' + str(credentials_update_thread_ID) + '"\n')

    # create HTTP server with custom request handler
    print('Running main thread at thread ID = "' + str(threading.get_ident()) + '"')
    PORT = 8080
    IP = socket.gethostbyname(socket.gethostname())
    server_address = (IP, PORT)
    server = http.server.HTTPServer(server_address, FinCloud)
    print('Server running at http://{}:{}'.format(IP, PORT))
    server.serve_forever()

    # delete admin credentials
    with open(file_path, 'w') as file:
        file.write('')


# run main driver function
if __name__ == '__main__':
    main()
