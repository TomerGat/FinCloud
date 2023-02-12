# import header file
from Fincloud_data_structs import *


# classes
class TradeEntry:
    def __init__(self, cur_from, cur_to, amount_taken, date, conversion_rate):
        self.cur_from = cur_from
        self.cur_to = cur_to
        self.amount = amount_taken
        self.conversion_rate = conversion_rate
        self.date = date


class Message:
    def __init__(self, subject, message):
        self.subject = subject
        self.message = message
        self.date = get_date()
        self.precise_time = get_precise_time()


class ConnectionEntry:
    def __init__(self, request_type, precise_time):
        self.lst = (request_type, precise_time)


class Entry:  # object properties: action, amount
    # entries are saved in the ledger of an account
    def __init__(self, action, amount, date, target_num, target_dep, entry_index):
        self.action = action  # type of action (deposit, withdrawal, transfer_sent, transfer_received)
        self.amount = amount  # value moved in the action
        self.date = date
        self.target_num = target_num  # if action involves other accounts this is set, otherwise set to -1
        self.target_dep = target_dep  # if action involves other accounts this is set, otherwise set to -1
        self.entry_id = generate_entry_id()  # entry identification code (unique for every entry)
        self.entry_index = entry_index


class Cloud:  # a financial cloud that allows deposits to be kept and accessed using an access code
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Cloud, cls).__new__(cls)
        return cls.instance

    def __init__(self):  # attribute contains dictionary {code: value accessed with code}
        self.allocated = {}

    def allocate(self, amount, allocation_code, ac_name, dep_name):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_TRANSACTION or response_code == Responses.INVALID_INPUT_AMOUNT:
            confirm = False
        else:
            confirm = False
            ac_index = name_table.in_table(ac_name)
            if 0 < ac_index < len(Accounts.log):
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
                        hashed_id = hash_function(allocation_code)
                        if ac_type == 'reg':
                            Accounts.log[ac_index].value['USD'] = Accounts.log[ac_index].value['USD'] - amount
                        elif ac_type == 'sav':
                            Accounts.log[ac_index].value = Accounts.log[ac_index].value - amount
                        else:
                            Accounts.log[ac_index].departments[dep_name][0]['USD'] = Accounts.log[ac_index].departments[dep_name][0]['USD'] - amount
                        if hashed_id in self.allocated.keys():
                            self.allocated[hashed_id] = self.allocated[hashed_id] + amount
                        else:
                            self.allocated[hashed_id] = amount
                        response_code = Responses.GENERAL_CONFIRM
                    else:
                        response_code = Responses.ALLOCATION_ID_INVALID  # invalid allocation id
                else:
                    response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds to complete allocation
            else:
                response_code = Responses.PROCESSING_ERROR  # processing error: account not found

        if confirm:
            ac_index = name_table.in_table(ac_name)
            if loc_type_table.in_table(ac_index) == 'reg':
                if not Accounts.log[ac_index].remaining_spending:
                    response_code = Responses.SPENDING_LIMIT_BREACH
                    fee = set_overspending_fee(Accounts.log[ac_index].monthly_spending_limit, abs(Accounts.log[ac_index].remaining_spending), amount)
                    Accounts.log[ac_index].value['USD'] = Accounts.log[ac_index].value['USD'] - fee

        return confirm, response_code

    def withdraw(self, amount, allocation_code, ac_name, dep_name):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_TRANSACTION or response_code == Responses.INVALID_INPUT_AMOUNT:
            confirm = False
        else:
            confirm = False
            ac_index = name_table.in_table(ac_name)
            if 0 < ac_index < len(Accounts.log):
                if validate_string(allocation_code):
                    hashed_id = hash_function(allocation_code)
                    if hashed_id in self.allocated.keys():
                        if self.allocated[hashed_id] >= amount:
                            confirm = True
                            ac_type = loc_type_table.in_table(ac_index)
                            if ac_type == 'sav':
                                Accounts.log[ac_index].value = Accounts.log[ac_index].value + amount
                            elif ac_type == 'reg':
                                Accounts.log[ac_index].value['USD'] = Accounts.log[ac_index].value['USD'] + amount
                            else:
                                Accounts.log[ac_index].departments[dep_name][0]['USD'] = Accounts.log[ac_index].departments[dep_name][0]['USD'] + amount
                            self.allocated[hashed_id] = self.allocated[hashed_id] - amount
                            response_code = Responses.GENERAL_CONFIRM
                        else:
                            response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds to complete allocation
                    else:
                        response_code = Responses.ALLOCATION_NOT_FOUND  # allocation not found
                else:
                    response_code = Responses.ALLOCATION_ID_INVALID  # invalid allocation id
            else:
                response_code = Responses.PROCESSING_ERROR  # processing error: account not found

        return confirm, response_code


class Account:
    def __init__(self, spending_limit):
        self.value = create_value_table()  # value table
        self.account_number = assign_account_number()  # account number
        self.ledger = Log()  # ledger for transaction entries
        self.trade_ledger = Log()  # ledger for trade entries
        self.monthly_spending_limit = spending_limit  # current monthly spending limit
        self.remaining_spending = self.monthly_spending_limit  # remaining funds to spend in month according to spending limit
        current_date = get_date()
        self.shift_date = current_date[2]  # date to reset remaining spending
        self.last_update = current_date  # last update
        self.new_spending_limit = spending_limit  # spending limit to shift to next month
        self.inbox = []  # account inbox, contains list of messages
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('reg')

    def update(self):
        current_date = get_date()
        months = current_date[1] - self.last_update[1]
        if current_date[2] < self.shift_date:
            months -= 1
        if months > 0:
            if self.remaining_spending > 0:
                # add bonus if monthly limit not reached
                bonus = set_underspending_bonus(self.monthly_spending_limit, self.remaining_spending, self.value['USD'])
                self.value['USD'] = self.value['USD'] + bonus
            # update monthly_spending_limit to new_spending_limit and reset remaining_spending
            self.monthly_spending_limit = self.new_spending_limit
            self.remaining_spending = self.monthly_spending_limit
            self.last_update = current_date

    def get_value_usd(self):
        total = 0
        for curr in self.value.keys():
            total += get_daily_rates(curr, 'USD', self.value[curr])
        return str(total)

    def deposit(self, amount):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        else:
            response_code = Responses.GENERAL_CONFIRM
            self.value['USD'] = self.value['USD'] + amount
            self.ledger.append(Entry('d', amount, get_date(), -1, -1, len(self.ledger.log)))

        return confirm, response_code

    def withdraw(self, amount):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        else:
            if self.value['USD'] >= amount:
                response_code = Responses.GENERAL_CONFIRM
                self.value['USD'] = self.value['USD'] - amount
                self.ledger.append(Entry('w', amount, get_date(), -1, -1, len(self.ledger.log)))
                self.remaining_spending -= amount
            else:
                response_code = Responses.INSUFFICIENT_AMOUNT  # account value too low
                confirm = False

        # check remaining spending and possibly deduct fee from account according to set_overspending_fee() function
        if confirm and not self.remaining_spending:
            response_code = Responses.SPENDING_LIMIT_BREACH
            fee = set_overspending_fee(self.monthly_spending_limit, abs(self.remaining_spending), amount)
            self.value['USD'] = self.value['USD'] - fee

        return confirm, response_code

    def trade_currency(self, amount, source_cur, target_cur):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
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
                    response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds
            else:
                if (source_cur not in self.value.keys()) and (target_cur in self.value.keys()):
                    response_code = Responses.SOURCE_CUR_NOT_FOUND # source currency not found
                elif (source_cur in self.value.keys()) and (target_cur not in self.value.keys()):
                    response_code = Responses.TARGET_CUR_NOT_FOUND  # target currency not found
                else:
                    response_code = Responses.CURRENCIES_NOT_FOUND  # source and target currencies not found

        return confirm, response_code

    def transfer(self, amount, target_account, target_dep):
        confirm = True
        target_index = -1
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        else:
            confirm = False
            target_index = name_table.in_table(target_account)
            if target_index == -1:
                target_index = number_table.in_table(target_account)
                if target_index == -1:
                    response_code = Responses.TARGET_AC_NOT_FOUND  # target account does not exist
                else:
                    confirm = True
            else:
                confirm = True
        if confirm:
            response_code = Responses.GENERAL_CONFIRM
            if self.value['USD'] >= amount:
                if target_dep == 'none':
                    if loc_type_table.in_table(target_index) == 'sav':
                        Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                    elif loc_type_table.in_table(target_index) == 'reg':
                        Accounts.log[target_index].value['USD'] = Accounts.log[target_index].value['USD'] + amount
                    if loc_type_table.in_table(target_index) == 'bus':
                        response_code = Responses.TARGET_DEP_WRONGLY_UNSET  # account is of business type but department name is set to 'none'
                        confirm = False
                    else:
                        self.value['USD'] = self.value['USD'] - amount
                        self.ledger.append(
                            Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, -1, len(self.ledger.log)))
                        Accounts.log[target_index].ledger.append(
                            Entry('tt', amount, get_date(), self.account_number, -1, len(self.ledger.log)))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.value['USD'] = self.value['USD'] - amount
                            self.ledger.append(
                                Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, target_dep, len(self.ledger.log)))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('tt', amount, get_date(), self.account_number, -1, len(self.ledger.log)))
                        else:
                            response_code = Responses.TARGET_DEP_NOT_FOUND  # department name does not exist
                            confirm = False
                    else:
                        response_code = Responses.TARGET_DEP_WRONGLY_SET  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds
                confirm = False

        if confirm:
            self.remaining_spending -= amount
            if not self.remaining_spending:
                response_code = Responses.SPENDING_LIMIT_BREACH
                fee = set_overspending_fee(self.monthly_spending_limit, abs(self.remaining_spending), amount)
                self.value['USD'] = self.value['USD'] - fee

        return confirm, response_code


class SavingsAccount:  # object properties: value, returns, last_update, account_number, ledger
    def __init__(self, returns):
        self.value = 0  # account value
        self.returns = pow((1 + returns / 100), 1 / 12)  # returns per month
        self.last_update = get_date()  # last update of account value
        self.shift_date = get_date()[2]  # day of account creation (shift month count +1 when updating)
        self.account_number = assign_account_number()  # account number
        self.ledger = Log()  # ledger for transaction entries
        self.fee = set_fee(self.returns)  # monthly fee
        self.inbox = []  # account inbox, contains list of messages
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('sav')

    def get_value_usd(self):
        return str(self.value)

    def update(self):
        current_date = get_date()
        months = current_date[1] - self.last_update[1]
        if current_date[2] < self.shift_date:
            months -= 1
        self.value = self.value * (pow((1 + self.returns), months))
        self.value = self.value - self.fee * months
        if months != 0:
            self.last_update = current_date

    def deposit(self, amount):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        else:
            confirm = True
            response_code = Responses.GENERAL_CONFIRM
            self.value = self.value + amount
            self.ledger.append(Entry('d', amount, get_date(), -1, -1, len(self.ledger.log)))

        return confirm, response_code

    def withdraw(self, amount):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        else:
            if self.value >= amount:
                confirm = True
                response_code = Responses.GENERAL_CONFIRM
                self.value = self.value - amount
                self.ledger.append(Entry('w', amount, get_date(), -1, -1, len(self.ledger.log)))
            else:
                response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient amount
                confirm = False

        return confirm, response_code

    def transfer(self, amount, target_account, target_dep):
        confirm = True
        target_index = -1
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        else:
            confirm = False
            target_index = name_table.in_table(target_account)
            if target_index == -1:
                target_index = number_table.in_table(target_account)
                if target_index == -1:
                    response_code = Responses.TARGET_AC_NOT_FOUND  # target account does not exist
                else:
                    confirm = True
            else:
                confirm = True
        if confirm:
            response_code = Responses.GENERAL_CONFIRM
            if self.value >= amount:
                if target_dep == 'none':
                    if loc_type_table.in_table(target_index) == 'sav':
                        Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                    elif loc_type_table.in_table(target_index) == 'reg':
                        Accounts.log[target_index].value['USD'] = Accounts.log[target_index].value['USD'] + amount
                    if loc_type_table.in_table(target_index) == 'bus':
                        response_code = Responses.TARGET_DEP_WRONGLY_UNSET  # account is of business type but department name is set to 'none'
                        confirm = False
                    else:
                        self.value = self.value - amount
                        self.ledger.append(
                            Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, -1, len(self.ledger.log)))
                        Accounts.log[target_index].ledger.append(
                            Entry('tt', amount, get_date(), self.account_number, -1, len(self.ledger.log)))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.value = self.value - amount
                            self.ledger.append(
                                Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, target_dep, len(self.ledger.log)))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('tt', amount, get_date(), self.account_number, -1, len(self.ledger.log)))
                        else:
                            response_code = Responses.TARGET_DEP_NOT_FOUND  # target department name does not exist
                            confirm = False
                    else:
                        response_code = Responses.TARGET_DEP_WRONGLY_SET  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds
                confirm = False

        return confirm, response_code


class BusinessAccount:  # object properties: company_name, departments_array, account_number, ledger
    def __init__(self, company_name, department_names):  # department_name is a list of names for each department
        self.company_name = company_name  # name of owning company
        self.departments = {}  # dictionary containing all departments as keys
        self.account_number = assign_account_number()  # account number
        number_table.add_key_index(self.account_number)
        loc_type_table.add_index_value('bus')
        self.inbox = []  # account inbox, contains list of messages
        for name in department_names:
            # each department is assigned a tuple containing a value table, a ledger, and a trade ledger
            self.departments[name] = (create_value_table(), Log(), Log())

    def get_value_usd(self):
        total = 0
        for dep_name in self.departments.keys():
            for curr in self.departments[dep_name][0].keys():
                total += get_daily_rates(curr, 'USD', self.departments[dep_name][0][curr])
        return str(total)

    def trade_currency(self, dep_name, source_cur, target_cur, amount):
        confirm = True
        target_index = -1
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
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
                        response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds
                else:
                    if (source_cur not in self.departments[dep_name][0].keys()) and (target_cur in self.departments[dep_name][0].keys()):
                        response_code = Responses.SOURCE_CUR_NOT_FOUND  # source currency not found
                    elif (source_cur in self.departments[dep_name][0].keys()) and (target_cur not in self.departments[dep_name][0].keys()):
                        response_code = Responses.TARGET_CUR_NOT_FOUND  # target currency not found
                    else:
                        response_code = Responses.CURRENCIES_NOT_FOUND  # source and target currencies not found
            else:
                response_code = Responses.DEP_NOT_FOUND  # department name not found (input error)

        return confirm, response_code

    def transfer(self, amount, source_dep, target_account, target_dep):
        confirm = True
        target_index = -1
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        else:
            target_index = name_table.in_table(target_account)
            if target_index == -1:
                target_index = number_table.in_table(target_account)
                if target_index == -1:
                    response_code = Responses.TARGET_AC_NOT_FOUND  # target account does not exist
                else:
                    confirm = True
            else:
                confirm = True
        if confirm:
            if source_dep not in self.departments.keys():
                response_code = Responses.SOURCE_DEP_NOT_FOUND  # source department does not exist
                confirm = False
        if confirm:
            response_code = Responses.GENERAL_CONFIRM
            if self.departments[source_dep][0]['USD'] >= amount:
                if target_dep == 'none':
                    if loc_type_table.in_table(target_index) == 'sav':
                        Accounts.log[target_index].value = Accounts.log[target_index].value + amount
                    elif loc_type_table.in_table(target_index) == 'reg':
                        Accounts.log[target_index].value['USD'] = Accounts.log[target_index].value['USD'] + amount
                    if loc_type_table.in_table(target_index) == 'bus':
                        response_code = Responses.TARGET_DEP_WRONGLY_UNSET  # account is of business type but department name is set to 'none'
                        confirm = False
                    else:
                        self.departments[source_dep][0]['USD'] = self.departments[source_dep][0]['USD'] - amount
                        self.departments[source_dep][1].append(
                            Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, -1, len(self.departments[source_dep][1].log)))
                        Accounts.log[target_index].ledger.append(
                            Entry('tt', amount, get_date(), self.account_number, source_dep, len(Accounts.log[target_index].departments[target_dep][1].log)))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.departments[source_dep][0]['USD'] = self.departments[source_dep][0]['USD'] - amount
                            self.departments[source_dep][1].append(
                                Entry('tf', amount, get_date(), Accounts.log[target_index].account_number, target_dep, len(self.departments[source_dep][1].log)))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('tt', amount, get_date(), self.account_number, source_dep, len(Accounts.log[target_index].departments[target_dep][1].log)))
                        else:
                            response_code = Responses.TARGET_DEP_NOT_FOUND  # target department name does not exist
                            confirm = False
                    else:
                        response_code = Responses.TARGET_DEP_WRONGLY_SET  # department set even though account is not a business account
                        confirm = False
            else:
                response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds
                confirm = False

        return confirm, response_code

    def inner_transfer(self, source_dep, target_dep, amount):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        elif not ((source_dep in self.departments.keys()) and (target_dep in self.departments.keys())):
            if source_dep not in self.departments.keys():
                response_code = Responses.SOURCE_DEP_NOT_FOUND  # source dep does not exist
            else:
                response_code = Responses.TARGET_DEP_NOT_FOUND  # target dep does not exist
            confirm = False
        if confirm:
            if self.departments[source_dep][0]['USD'] >= amount:
                self.departments[source_dep][0]['USD'] = self.departments[source_dep][0]['USD'] - amount
                self.departments[target_dep][0]['USD'] = self.departments[target_dep][0]['USD'] + amount
                self.departments[source_dep][1].append(Entry('tfi', amount, get_date(), -1, target_dep, len(self.departments[source_dep][1].log)))
                self.departments[target_dep][1].append(Entry('tti', amount, get_date(), -1, source_dep, len(self.departments[target_dep][1].log)))
            else:
                confirm = False
                response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds

        return confirm, response_code

    def deposit(self, amount, dep_name):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        elif dep_name not in self.departments.keys():
            response_code = Responses.DEP_NOT_FOUND  # dep name does not exist
            confirm = False
        else:
            response_code = 1
            self.departments[dep_name][0]['USD'] = self.departments[dep_name][0]['USD'] + amount
            self.departments[dep_name][1].append(Entry('d', amount, get_date(), -1, -1, len(self.departments[dep_name][1].log)))

        return confirm, response_code

    def withdraw(self, amount, dep_name):
        confirm = True
        response_code = Responses.EMPTY_RESPONSE
        if not validate_number(amount):
            response_code = Responses.INVALID_INPUT_AMOUNT  # input (amount) not valid
        else:
            amount = float(amount)
            if amount <= 0:
                response_code = Responses.INVALID_TRANSACTION  # amount null or negative
        if response_code == Responses.INVALID_INPUT_AMOUNT or response_code == Responses.INVALID_TRANSACTION:
            confirm = False
        elif dep_name not in self.departments.keys():
            response_code = Responses.DEP_NOT_FOUND  # dep name does not exist
            confirm = False
        else:
            if self.departments[dep_name][0]['USD'] >= amount:
                response_code = Responses.GENERAL_CONFIRM
                self.departments[dep_name][0]['USD'] = self.departments[dep_name][0]['USD'] - amount
                self.departments[dep_name][1].append(Entry('d', amount, get_date(), -1, -1, len(self.departments[dep_name][1].log)))
            else:
                confirm = False
                response_code = Responses.INSUFFICIENT_AMOUNT  # insufficient funds

        return confirm, response_code

    def add_department(self, dep_name):
        confirm = False
        response_code = Responses.EMPTY_RESPONSE
        if dep_name not in self.departments.keys():
            if validate_string(dep_name):
                self.departments[dep_name] = (create_value_table(), Log(), Log())
                confirm = True
            else:
                response_code = Responses.DEP_NAME_INVALID  # department name not valid
        else:
            response_code = Responses.DEP_NAME_EXISTS  # department name already exists

        return confirm, response_code


# functions
def send_message(ac_index, subject, message):
    mes = Message(subject, message)
    Accounts.log[ac_index].inbox.append(mes)


def set_fee(returns):
    if returns == RETURNS_PREMIUM:
        return PREMIUM_RETURNS_FEE
    elif returns == RETURNS_MEDIUM:
        return MEDIUM_RETURNS_FEE
    elif returns == RETURNS_MINIMUM:
        return MINIMUM_RETURNS_FEE
    return -1


def set_overspending_fee(spending_limit, total_spending_breach, last_spending_amount):
    deviation_percentage = total_spending_breach / spending_limit
    fee = deviation_percentage * last_spending_amount * OVERSPENDING_FEE_RATIO
    return fee


def set_underspending_bonus(spending_limit, remaining_spending, total_account_value):
    # check that spending was at least 15%, otherwise do not give bonus
    if spending_limit / remaining_spending > (1 - MINIMUM_SPENDING_RATIO_FOR_BONUS):
        return 0
    # calculate bonus according to the percentage of underspending and according to the size of the spending limit
    # also take into consideration total account value to prevent setting high limits in order to get large bonuses
    underspending_percentage = remaining_spending / spending_limit
    bonus = underspending_percentage * (total_account_value - spending_limit) * UNDERSPENDING_BONUS_RATIO
    return bonus


def get_daily_rates(cur1, cur2, amount):
    amount_new = amount / last_rates[cur1] * last_rates[cur2]
    return round(amount_new, 3)


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


def generate_entry_id():
    # Generate a random number between 100000000000 and 999999999999
    number = random.randint(100000000000, 999999999999)

    # Check if the random number has been generated before
    while number in existing_entry_id:
        # If it has, generate a new random number
        number = random.randint(100000000000, 999999999999)

    # Add the random number to the set of generated numbers
    existing_entry_id.add(number)

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
    shifts = 64 - math.floor(math.log10(new_val)) + 1
    new_val = new_val << shifts if shifts >= 0 else new_val >> abs(shifts)
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


def verification(attempt, code_attempt):  # returns: verification answer, response code, account index
    """
    :param attempt: user attempt for account name/number
    :param code_attempt: user attempt for account code
    :return: answer for verification, response code, index of account that was logged into (if verified)
    """

    # initialize return values
    verify = False
    response_code = Responses.EMPTY_RESPONSE
    # check existence of account name/number
    name_index = name_table.in_table(attempt)  # attempt - client's attempt at account name/number
    num_index = number_table.in_table(attempt)
    # set response
    if (name_index == -1) and (num_index == -1):
        response_code = Responses.AC_IDENTITY_INCORRECT  # incorrect name/number
    elif (name_index != -1) and (num_index == -1):
        if pass_table.in_table(name_index) == hash_function(code_attempt):
            response_code = Responses.GENERAL_CONFIRM
            verify = True
        else:
            response_code = Responses.AC_CODE_INCORRECT  # incorrect password
    elif (num_index != -1) and (name_index == -1):
        if pass_table.in_table(num_index) == hash_function(code_attempt):
            response_code = Responses.GENERAL_CONFIRM
            verify = True
        else:
            response_code = Responses.AC_CODE_INCORRECT  # incorrect password
    else:
        response_code = Responses.PROCESSING_ERROR  # processing error (user's attempt matches both a name and a number -> impossible situation)

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
    response_code = Responses.EMPTY_RESPONSE

    # checking validity and availability of account name and code
    if validate_string(account_name) and validate_string(account_code):
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = Responses.GENERAL_CONFIRM  # account name and code are confirmed
        else:
            response_code = Responses.AC_NAME_EXISTS  # account name is unavailable
    else:
        if (not validate_string(account_name)) and validate_string(account_code):
            response_code = Responses.AC_NAME_INVALID  # name invalid
        else:
            response_code = Responses.AC_CODE_INVALID  # code invalid
        if not (validate_string(account_name) or validate_string(account_code)):
            response_code = Responses.NAME_AND_CODE_INVALID  # name and code invalid
    if confirm:
        if returns not in [RETURNS_PREMIUM, RETURNS_MEDIUM, RETURNS_MINIMUM]:
            response_code = Responses.INVALID_SAVING_RETURNS  # invalid returns
            confirm = False
        if not validate_phone_number(phone_num):
            response_code = Responses.PHONE_NUM_INVALID  # phone number invalid
            confirm = False
        if phone_name_table.in_table(hash_function(phone_num)) != -1:
            response_code = Responses.PHONE_NUM_EXISTS  # phone number already registered
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


def create_checking_account(account_name, account_code, phone_num, monthly_spending_limit):  # returns confirms, account index, response code
    confirm = False  # initialize return value
    user_name = account_name  # saving initial name of account
    response_code = Responses.EMPTY_RESPONSE

    # checking validity and availability of account name and code
    if validate_string(account_name) and validate_string(account_code):
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = Responses.GENERAL_CONFIRM  # account name and code are confirmed
        else:
            response_code = Responses.AC_NAME_EXISTS  # account name is unavailable
    else:
        if (not validate_string(account_name)) and validate_string(account_code):
            response_code = Responses.AC_NAME_INVALID  # name invalid
        if (not validate_string(account_code)) and validate_string(account_name):
            response_code = Responses.AC_CODE_INVALID  # code invalid
        if not (validate_string(account_name) or validate_string(account_code)):
            response_code = Responses.NAME_AND_CODE_INVALID  # name and code invalid
    if confirm:
        if not validate_phone_number(phone_num):
            response_code = Responses.PHONE_NUM_INVALID  # phone number not valid
            confirm = False
        elif phone_name_table.in_table(hash_function(phone_num)) != -1:
            response_code = Responses.PHONE_NUM_EXISTS  # phone number already registered
            confirm = False
        elif not validate_number(monthly_spending_limit) or monthly_spending_limit <= 0:
            response_code = Responses.INVALID_SPENDING_LIMIT
            confirm = False
    if confirm:
        # add account details to tables
        name_table.add_key_index(account_name)
        pass_table.add_index_value(hash_function(account_code))
        phone_name_table.add_key_value(hash_function(phone_num), account_name)

        # create account object
        new_account = Account(monthly_spending_limit)
        account_name = "ac" + str(name_table.in_table(account_name))
        globals()[account_name] = new_account
        Accounts.append(globals()[account_name])

    # return values (confirmation, account index, response code)
    return confirm, name_table.in_table(user_name), response_code


def create_business_account(account_name, company_name, account_code, phone_num):
    confirm = False  # initialize return value
    user_name = account_name  # saving initial name of account
    response_code = Responses.EMPTY_RESPONSE

    # checking validity and availability of account name and code
    ac_name_valid = validate_string(account_name)
    ac_code_valid = validate_string(account_code)
    if check_for_spaces(company_name):
        company_name = organize_comp_name(company_name)
    comp_name_valid = validate_comp_name(company_name)

    if ac_name_valid and ac_code_valid and comp_name_valid:
        if name_table.in_table(account_name) == -1 and number_table.in_table(account_name) == -1:
            confirm = True
            response_code = Responses.GENERAL_CONFIRM  # account name and code are confirmed
        else:
            response_code = Responses.AC_NAME_EXISTS  # account name is unavailable
    else:
        if not ac_name_valid and ac_code_valid and comp_name_valid:
            response_code = Responses.AC_NAME_INVALID  # name invalid
        elif ac_name_valid and not ac_code_valid and comp_name_valid:
            response_code = Responses.AC_CODE_INVALID  # code invalid
        elif ac_name_valid and ac_code_valid and not comp_name_valid:
            response_code = Responses.COMP_NAME_INVALID  # comp name invalid
        elif not ac_name_valid and not ac_code_valid and comp_name_valid:
            response_code = Responses.NAME_AND_CODE_INVALID  # name and code invalid
        elif not ac_name_valid and ac_code_valid and not comp_name_valid:
            response_code = Responses.NAME_AND_COMP_INVALID  # name and comp name invalid
        elif ac_name_valid and not ac_code_valid and not comp_name_valid:
            response_code = Responses.CODE_AND_COMP_INVALID  # code and comp name invalid
        elif not (ac_name_valid or ac_code_valid or comp_name_valid):
            response_code = Responses.DATA_INVALID  # name and code and comp name invalid
    if confirm:
        if not validate_phone_number(phone_num):
            response_code = Responses.PHONE_NUM_INVALID  # phone number not valid
            confirm = False
        elif phone_name_table.in_table(hash_function(phone_num)) != -1:
            response_code = Responses.PHONE_NUM_EXISTS  # phone number already registered
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
