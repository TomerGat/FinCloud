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


class ConnectionEntry:
    def __init__(self, request_type, precise_time):
        self.lst = (request_type, precise_time)


class Message:
    def __init__(self, subject, message, sender, message_type):
        self.subject = subject
        self.message = message
        self.sender = sender
        self.message_type = message_type
        self.date = get_date()
        self.message_id = generate_message_id()


class Entry:  # object properties: action, amount
    # entries are saved in the ledger of an account
    def __init__(self, action, amount, date, target_num, target_dep, entry_id=None):
        self.action = action  # type of action (deposit, withdrawal, transfer_sent, transfer_received)
        self.amount = amount  # value moved in the action
        self.date = date
        self.target_num = target_num  # if action involves other accounts this is set, otherwise set to -1
        self.target_dep = target_dep  # if action involves other accounts this is set, otherwise set to -1
        self.entry_id = entry_id  # entry identification code (unique for every entry)
        if self.entry_id is None:
            self.entry_id = generate_entry_id()


class Request:
    def __init__(self, entry: Entry, source_index: int, source_dep: str):
        if source_index not in active_requests.keys():
            active_requests[source_index] = []
        if source_index not in previous_requests.keys():
            previous_requests[source_index] = []
        self.source_index = source_index
        self.source_dep = source_dep
        self.target_index = number_table.get_key(entry.target_num)
        self.target_dep = entry.target_dep
        self.action_type = entry.action
        self.amount = entry.amount
        self.request_id = generate_request_id()
        self.date = get_date()
        self.entry_id = entry.entry_id
        self.status = 'active'
        active_requests[source_index].append(self)


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
        self.account_number = generate_account_number()  # account number
        self.ledger = Log()  # ledger for transaction entries
        self.trade_ledger = Log()  # ledger for trade entries
        self.monthly_spending_limit = spending_limit  # current monthly spending limit
        self.remaining_spending = self.monthly_spending_limit  # remaining funds to spend in month (limit - spending)
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
                message_str = 'Congratulations! In the last month you spent less that your monthly spending limit,' \
                              ' so we decided to award you with a bonus of ' + str(bonus) + ' USD to your account.'
                send_message(number_table.in_table(self.account_number),
                             'Underspending Bonus',
                             message_str,
                             'Fincloud Awards Team',
                             'notif')
            # update monthly_spending_limit to new_spending_limit and reset remaining_spending
            self.monthly_spending_limit = self.new_spending_limit
            self.remaining_spending = self.monthly_spending_limit
            self.last_update = current_date
            send_message(number_table.in_table(self.account_number),
                         'Monthly spending limit update',
                         'Monthly spending limit updated to ' + str(self.monthly_spending_limit),
                         'Fincloud Account Management Team',
                         'notif')

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
            self.ledger.append(Entry('deposit', amount, get_date(), -1, -1))

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
                self.ledger.append(Entry('withdrawal', amount, get_date(), -1, -1))
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
                        entry_id = generate_entry_id()
                        self.ledger.append(
                            Entry('transfer from', amount, get_date(), Accounts.log[target_index].account_number, -1, entry_id))
                        Accounts.log[target_index].ledger.append(
                            Entry('transfer to', amount, get_date(), self.account_number, -1, entry_id))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.value['USD'] = self.value['USD'] - amount
                            entry_id = generate_entry_id()
                            self.ledger.append(
                                Entry('transfer from', amount, get_date(), Accounts.log[target_index].account_number, target_dep, entry_id))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('transfer to', amount, get_date(), self.account_number, -1, entry_id))
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
        self.account_number = generate_account_number()  # account number
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
            self.ledger.append(Entry('deposit', amount, get_date(), -1, -1))

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
                self.ledger.append(Entry('withdrawal', amount, get_date(), -1, -1))
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
                entry_id = generate_entry_id()
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
                            Entry('transfer from', amount, get_date(), Accounts.log[target_index].account_number, -1, entry_id))
                        Accounts.log[target_index].ledger.append(
                            Entry('transfer to', amount, get_date(), self.account_number, -1, entry_id))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.value = self.value - amount
                            self.ledger.append(
                                Entry('transfer from', amount, get_date(), Accounts.log[target_index].account_number, target_dep, entry_id))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('transfer to', amount, get_date(), self.account_number, -1, entry_id))
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
        self.account_number = generate_account_number()  # account number
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
                entry_id = generate_entry_id()
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
                            Entry('transfer from', amount, get_date(), Accounts.log[target_index].account_number, -1, entry_id))
                        Accounts.log[target_index].ledger.append(
                            Entry('transfer to', amount, get_date(), self.account_number, source_dep, entry_id))
                else:
                    if loc_type_table.in_table(target_index) == 'bus':
                        if target_dep in Accounts.log[target_index].departments.keys():
                            Accounts.log[target_index].departments[target_dep][0]['USD'] = \
                                Accounts.log[target_index].departments[target_dep][0]['USD'] + amount
                            self.departments[source_dep][0]['USD'] = self.departments[source_dep][0]['USD'] - amount
                            self.departments[source_dep][1].append(
                                Entry('transfer from', amount, get_date(), Accounts.log[target_index].account_number, target_dep, entry_id))
                            Accounts.log[target_index].departments[target_dep][1].append(
                                Entry('transfer to', amount, get_date(), self.account_number, source_dep, entry_id))
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
                entry_id = generate_entry_id()
                self.departments[source_dep][1].append(Entry('transfer from (inner)', amount, get_date(), -1, target_dep, entry_id))
                self.departments[target_dep][1].append(Entry('transfer to (inner)', amount, get_date(), -1, source_dep, entry_id))
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
            self.departments[dep_name][1].append(Entry('deposit', amount, get_date(), -1, -1))

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
                self.departments[dep_name][1].append(Entry('withdrawal', amount, get_date(), -1, -1))
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
def generate_message_id() -> int:
    # Generate a random number between 100000000000 and 999999999999
    number = random.randint(100000000000, 999999999999)

    # Check if the random number is already assigned
    if number in existing_message_id:
        # If it is, return a number recursively
        return generate_message_id()

    # Add the random number to the set of generated numbers and return the number
    existing_message_id.add(number)
    return number


def generate_entry_id() -> int:
    # Generate a random number between 100000000000 and 999999999999
    number = random.randint(100000000000, 999999999999)

    # Check if the random number is already assigned
    if number in existing_entry_id:
        # If it is, return a number recursively
        return generate_entry_id()

    # Add the random number to the set of generated numbers and return the number
    existing_entry_id.add(number)
    return number


def generate_account_number() -> int:
    # Generate a random number between 100000000000 and 999999999999
    number = random.randint(100000000000, 999999999999)

    # Check if the random number is already assigned
    if number in existing_account_numbers:
        # If it is, return a number recursively
        return generate_account_number()

    # Add the random number to the set of generated numbers and return the number
    existing_account_numbers.add(number)
    return number


def generate_request_id() -> int:
    # Generate a random number between 100000000000 and 999999999999
    number = random.randint(100000000000, 999999999999)

    # Check if the random number is already assigned
    if number in existing_request_id:
        # If it is, return a number recursively
        return generate_request_id()

    # Add the random number to the set of generated numbers and return the number
    existing_request_id.add(number)
    return number


def handle_request(request_to_handle: Request, response: str) -> bool:
    """
    :param response: should request be approved/denied
    :param request_to_handle: request to handle
    :return: handling confirmation
    """

    # make sure response is valid
    if response != 'yes' and response != 'no':
        return False

    # move request from active requests to previous requests
    active_requests[request_to_handle.source_index] = \
        [request for request in active_requests[request_to_handle.source_index] if request.request_id != request_to_handle.request_id]
    request_to_handle.status = 'approved' if response == 'yes' else 'denied'
    previous_requests[request_to_handle.source_index].append(request_to_handle)

    # remove the entry from the account's log
    remove_entry(request_to_handle.source_index, request_to_handle.entry_id, request_to_handle.source_dep,
                 remove_entry_id=True)
    if request_to_handle.target_index != -1:
        remove_entry(request_to_handle.target_index, request_to_handle.entry_id, request_to_handle.target_dep,
                     remove_entry_id=False)

    # reverse the transaction if request is approved
    if response == 'yes':
        confirm = reverse_transaction(request_to_handle.source_index, request_to_handle.source_dep,
                                      request_to_handle.target_index, request_to_handle.target_dep,
                                      request_to_handle.action_type, request_to_handle.amount)
    else:
        confirm = True  # confirm denial of request

    # send messages to update transaction parties of the denial/approval of the request
    mes_str = 'Request to cancel transaction of type ' + request_to_handle.action_type + ' was ' + ('denied' if response == 'no' else 'approved') + ' by the bank.'
    mes_str += """
    Amount: {} (status resolved)
    If request was approved, the correct amount will be returned/removed from your account shortly.
    Thank you for filing a request, and we appologize for authorizing the transaction.
    Thank you
    """.format(str(request_to_handle.amount))
    send_message(request_to_handle.source_index,
                 'Request num: ' + str(request_to_handle.request_id) + ' status update',
                 mes_str,
                 'FinCloud Anomaly Detection Team',
                 'notif')
    if request_to_handle.target_index != -1 and response == 'yes':
        send_message(request_to_handle.target_index,
                     'Update regarding request filed by a user of the bank',
                     mes_str,
                     'FinCloud Anomaly Detection Team',
                     'notif')

    return confirm


def remove_entry(ac_index: int, id_to_remove: int, dep_name, remove_entry_id=False):
    ac_type = loc_type_table.in_table(ac_index)

    # remove entry id from existing_entry_id if flag is set to True
    if remove_entry_id:
        existing_entry_id.remove(id_to_remove)

    # remove entry from ledger
    if ac_type != 'bus':
        Accounts.log[ac_index].ledger.log = \
            np.array([entry for entry in Accounts.log[ac_index].ledger.log if entry.entry_id != id_to_remove])
    else:
        Accounts.log[ac_index].departments[dep_name][1].log = \
            np.array([entry for entry in Accounts.log[ac_index].departments[dep_name][1].log if entry.entry_id != id_to_remove])


def reverse_transaction(source_index: int, source_dep, target_index: int, target_dep, action_type: str, amount: int) -> bool:
    """
    :param source_index: index of source account
    :param source_dep: name of source department (if exists)
    :param target_index: index of target account (if exists)
    :param target_dep: name of target department (if exists)
    :param action_type: action type (d/w/tf/tt)
    :param amount: amount of funds moved in transaction
    :return: bool (whether reversal is confirmed)
    """

    save_action_type = ''
    if action_type == 'transfer from':  # if the action is transfer away, change action to deposit and save withdraw for target account
        save_action_type = 'withdrawal'
        action_type = 'deposit'
    elif action_type == 'transfer to':  # if the action is transfer to, change action to withdraw and save deposit for source account
        save_action_type = 'deposit'
        action_type = 'withdrawal'
    else:
        if action_type != 'deposit' and action_type != 'withdrawal':
            return False

    ac_type = loc_type_table.in_table(source_index)
    if action_type == 'deposit':  # deposit
        if ac_type == 'reg':
            Accounts.log[source_index].value['USD'] = Accounts.log[source_index].value['USD'] - amount
        elif ac_type == 'sav':
            Accounts.log[source_index].value = Accounts.log[source_index].value - amount
        else:
            Accounts.log[source_index].departments[source_dep][0]['USD'] = Accounts.log[source_index].departments[source_dep][0]['USD'] - amount

    elif action_type == 'withdrawal':  # withdraw
        if ac_type == 'reg':
            Accounts.log[source_index].value['USD'] = Accounts.log[source_index].value['USD'] + amount
        elif ac_type == 'sav':
            Accounts.log[source_index].value = Accounts.log[source_index].value + amount
        else:
            Accounts.log[source_index].departments[source_dep][0]['USD'] = Accounts.log[source_index].departments[source_dep][0]['USD'] + amount

    if save_action_type == '':
        return True

    # call function for target account with opposite action
    return reverse_transaction(target_index, target_dep, -1, -1, save_action_type, amount)


def send_message(ac_index: int, subject: str, message: str, sender: str, mes_type: str):
    mes = Message(subject, message, sender, mes_type)
    Accounts.log[ac_index].inbox.append(mes)


def send_announcement(subject, message, sender, mes_type: str, type_modification=None):
    mes = Message(subject, message, sender, mes_type)
    for ac_index in range(len(Accounts.log)):
        if (type_modification is None) or \
                (type_modification is not None and loc_type_table.in_table(ac_index) == type_modification):
            Accounts.log[ac_index].inbox.append(mes)


def set_fee(returns) -> int:
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
    return int(round(amount_new, 3))


def currency_rates(cur1, cur2, amount):
    try:
        return round(converter.CurrencyRates().convert(cur1, cur2, amount), 3)
    except converter.RatesNotAvailableError:
        amount_new = amount / last_rates[cur1] * last_rates[cur2]
        return int(round(amount_new, 3))


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


def security_verification(ac_index, question, answer_attempt) -> (bool, int):
    """
    :param ac_index: index of account being recovered
    :param question: number of question (1/2)
    :param answer_attempt: user answer for security verification question
    :return: verify (bool), response_code (int)
    """

    # initialize return values
    verify = False
    response_code = Responses.EMPTY_RESPONSE
    # validate the input
    if not validate_string(answer_attempt):
        response_code = Responses.INVALID_SECURITY_ANSWER
    else:
        correct_answer = security_questions[ac_index][question]
        # compare attempt with correct answer
        if answer_attempt != correct_answer:
            response_code = Responses.SECURITY_ANSWER_INCORRECT
        else:
            verify = True
            response_code = Responses.GENERAL_CONFIRM

    return verify, response_code


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


def cluster_by_date(action_clusters: {str: [Entry]}) -> {str: [[Entry]]}:
    general_clusters = {}
    for action in action_clusters.keys():
        group = action_clusters[action]
        counter = int(len(group) * CLUSTER_NUMBER_RATIO)

        # find first date (later subtract first date from all dates to cluster correctly
        first_date = date_to_num(group[0].date)
        for entry in group:
            if date_to_num(entry.date) < first_date:
                first_date = date_to_num(entry.date)

        last_date = 0
        for entry in group:
            if date_to_num(entry.date) > last_date:
                last_date = date_to_num(entry.date)

        gap = last_date / counter  # gap - jumps of amount between clusters defined by maximum amount and cluster counter

        # create a list of counter length in which each segment has a list which will include entries in the amount range
        # each index in the list 'clusters' will contain a list (each list is a cluster, entries will be divided to clusters)
        # amount range is index*gap to (index+1)*gap for each cluster, entries are organized by amount
        clusters = create_clusters(counter)
        for index in range(len(group)):
            cluster_index = find_cluster(gap, date_to_num(group[index].date) - first_date)  # find cluster index for the entry
            if group[index].amount == last_date:
                cluster_index -= 1  # if amount is largest, index will be out of bounds
            clusters[cluster_index].append(group[index])  # add entry to the correct cluster
        general_clusters[action] = clusters

    return general_clusters


def cluster_by_amount(action_clusters: {str: [Entry]}) -> {str: [[Entry]]}:
    """
    :param action_clusters: dictionary in which keys are actions and values are lists of transaction entries
    :return: action_clusters but lists of entries are divided into clusters by amounts
    """
    general_clusters = {}
    for action in action_clusters.keys():  # run algorithm for each list of entries that are organized by action type
        group = action_clusters[action]
        counter = int(len(group) * CLUSTER_NUMBER_RATIO)
        largest_amount = 0
        # find the largest amount in group
        for entry in group:
            if entry.amount > largest_amount:
                largest_amount = entry.amount

        gap = largest_amount / counter  # gap - jumps of amount between clusters defined by maximum amount and cluster counter

        # create a list of counter length in which each segment has a list which will include entries in the amount range
        # each index in the list 'clusters' will contain a list (each list is a cluster, entries will be divided to clusters)
        # amount range is index*gap to (index+1)*gap for each cluster, entries are organized by amount
        clusters = create_clusters(counter)
        for index in range(len(group)):
            cluster_index = find_cluster(gap, group[index].amount)  # find cluster index for the entry
            if group[index].amount == largest_amount:
                cluster_index -= 1  # if amount is largest, index will be out of bounds
            clusters[cluster_index].append(group[index])  # add entry to the correct cluster
        general_clusters[action] = clusters

    return general_clusters


def return_stats(entries: Log, ac_index: int) -> (int, float, float, {str: [[Entry]]}):
    """
    :param entries: list of entries
    :param ac_index: index of account (entries are from the account at ac_index in Accounts)
    :return: median of entry amounts, average of all entry amounts, average of checked entry amounts, clusters of entries
    clusters: a dictionary in which keys are actions, values are a list of lists of Entries
    """
    amounts = []
    avg = 0
    action_clusters = {}
    ledger_len = len(entries.log)
    checked_entries = entries.log[0:last_checked_entry[ac_index]]
    already_checked = len(checked_entries)
    avg_before = 0
    for entry in checked_entries:
        avg_before += entry.amount / already_checked
    for etype in entry_types:
        action_clusters[etype] = []
    for index in range(len(entries.log)):
        entry_amount = entries.log[index].amount
        avg += entry_amount / ledger_len
        amounts.append(entry_amount)
        action_clusters[entries.log[index].action].append(entries.log[index])
    amounts.sort()
    median = amounts[int(ledger_len / 2) + 1] if ledger_len % 2 == 1 \
        else (amounts[int(ledger_len / 2)] + amounts[int(ledger_len / 2) + 1]) / 2
    amount_clusters = cluster_by_amount(action_clusters)
    date_clusters = cluster_by_date(action_clusters)

    return median, avg, avg_before, amount_clusters, date_clusters


def find_anomalies(ac_ledger: Log, ac_index: int) -> (bool, []):
    """
    :param ac_ledger: ledger of account (of log type, property of the account being checked)
    :param ac_index: index of account (entries are from the account at ac_index in Accounts)
    :return: a boolean value that identifies whether red flags were found, and a list of flagged entries
    """

    # if all entries in ledger were already checked, return False and an empty list
    if len(ac_ledger.log) == last_checked_entry[ac_index] + 1:
        return False, []

    # get stats on complete entry ledger
    median, avg, avg_before, amount_clusters, date_clusters = return_stats(ac_ledger, ac_index)

    # separate entries that were not yet checked
    entries_to_check = ac_ledger.log[last_checked_entry[ac_index]::]

    # update last_checked_entry to current number of entries
    last_checked_entry[ac_index] = len(ac_ledger.log) - 1

    flagged_entries = []
    # find anomalies in new entries
    # possible flags: relatively large transaction after x time without activity,
    #                 largest every transaction by x margin
    #                 causes change in average transfer stats above x percentage points,
    #                 large standard deviation,
    #                 first transaction of certain action type with large clusters of other types
    #                 transaction from savings account to department of business account that was previously empty

    # find outliers in Entry clusters (with amount clustering and date clustering:
    # clusters with only one entry, with two adjacent clusters that are empty, will be identified as outliers
    for action in amount_clusters.keys():
        clusters = amount_clusters[action]
        lonely_clusters = []  # indices for clusters with only one entry
        empty_clusters = []  # indices for clusters with no entries
        for index in range(len(clusters)):
            if len(clusters[index]) == 1:
                lonely_clusters.append(index)
            elif len(clusters[index]) == 0:
                empty_clusters.append(index)
        red_flag_indices = []
        for index in lonely_clusters:
            if index == 0:
                if (index + 1) in empty_clusters:
                    red_flag_indices.append(index)
            elif index == len(clusters) - 1:
                if (index - 1) in empty_clusters:
                    red_flag_indices.append(index)
            else:
                if (index + 1) in empty_clusters and (index - 1) in empty_clusters:
                    red_flag_indices.append(index)
        for index in red_flag_indices:
            if clusters[index][0] in entries_to_check:
                flagged_entries.append(clusters[index][0])

    # find unreasonably large gaps in time between transactions
    for action in date_clusters.keys():
        clusters = date_clusters[action]
        lonely_clusters = []  # indices for clusters with only one entry
        empty_clusters = []  # indices for clusters with no entries
        for index in range(len(clusters)):
            if len(clusters[index]) == 1:
                lonely_clusters.append(index)
            elif len(clusters[index]) == 0:
                empty_clusters.append(index)
        red_flag_indices = []
        for index in lonely_clusters:
            if (index + 1) in empty_clusters and (index + 2) in empty_clusters:
                red_flag_indices.append(index)
            elif index == len(clusters) - 1:
                if (index - 1) in empty_clusters and (index - 2) in empty_clusters:
                    red_flag_indices.append(index)
            else:
                if (index + 1) in empty_clusters and (index + 2) in empty_clusters and (index - 1) in empty_clusters and (index - 2) in empty_clusters:
                    red_flag_indices.append(index)
        for index in red_flag_indices:
            if clusters[index][0] in entries_to_check:
                flagged_entries.append(clusters[index][0])

    # find outliers with standard deviation calculation
    amounts = [entry.amount for entry in ac_ledger.log]
    standard_deviation = statistics.stdev(amounts)
    for entry in ac_ledger.log:
        deviation = calc_deviation(entry.amount, avg, standard_deviation)
        if deviation >= MIN_DEVIATION_RATIO_TO_FLAG * standard_deviation and entry not in flagged_entries and entry in entries_to_check:
            flagged_entries.append(entry)

    # specific flags:
    # largest transfer in transaction history to an account never transferred to before
    # find the largest transfer amount (also save index of entry)
    largest_amount = 0
    largest_amount_index = 0
    for index in range(len(ac_ledger.log)):
        if ac_ledger.log[index].amount > largest_amount and ac_ledger.log[index].action == 'transfer from':
            largest_amount = ac_ledger.log[index].amount
            largest_amount_index = index

    # check if entry is in entries_to_check, if so check for flag
    if largest_amount_index > last_checked_entry[ac_index]:
        # create the following dictionary {ac number transferred to: list of amounts to this index}
        transfer_dict = {}
        for entry in ac_ledger.log:
            if entry.target_num not in transfer_dict.keys() and entry.action == 'transfer from':
                transfer_dict[entry.target_num] = []
            transfer_dict[entry.target_num].append(entry.amount)
        # go over values and check if largest amount is alone in a list (if so, flag entry)
        for amounts in transfer_dict.values():
            if len(amounts) == 1:
                if amounts[0] == largest_amount:
                    flagged_entries.append(ac_ledger.log[largest_amount_index])

    # return red_flags_found (bool value) and list of flagged entries
    if not FLAG_INNER_TRANSFERS:
        flagged_entries = [entry for entry in flagged_entries if (entry.action != 'transfer from (inner)' and entry.action != 'transfer to (inner)')]
    red_flags_found = (len(flagged_entries) != 0)
    return red_flags_found, flagged_entries


def send_anomaly_message(anomaly_entry: Entry, ac_index):
    # create subject
    date = anomaly_entry.date
    date_str = date_to_str(date)
    subject = 'Transaction of type ' + anomaly_entry.action + ' on ' + date_str + '(Entry ID: ' + str(anomaly_entry.entry_id) + ')'
    message = 'Red Flag raised for transaction:' + '\n'
    message += 'Entry ID: ' + str(anomaly_entry.entry_id) + '\n'
    message += 'Transaction date: ' + date_str + '\n'
    message += 'Action type: ' + anomaly_entry.action + '\n'
    message += 'Transferred to account number: ' + (
        str(anomaly_entry.target_num) if anomaly_entry.target_num != -1 else 'none') + '\n'
    message += 'Transferred to department: ' + (
        str(anomaly_entry.target_dep) if anomaly_entry.target_dep != -1 else 'none') + '\n'
    message += 'Amount of transaction: ' + str(anomaly_entry.amount) + '\n'
    message += 'If this transaction is an error, or you suspect that it was caused by a malicious third-party,' \
               ' please file a request to the bank.' + '\n'
    message += 'Thank you,' + '\n'
    message += 'Anomaly Detection Team'
    sender = 'Fincloud Anomaly Detection Team'
    mes_type = 'red flag'
    send_message(ac_index, subject, message, sender, mes_type)


def find_id_in_message(mes: Message) -> int:
    subject = mes.subject
    # message subject structure - 'Transaction of type <type> on <dd/mm/yyyy> (Entry ID: <id>)'
    subject_parsed = subject.split(': ')  # dividing the subject into two parts, leaving the second part as '<id>)'
    entry_id = subject_parsed[1].split(')')[0]
    return entry_id


def wait_for_flag(seconds):
    counter = 0
    while counter < seconds and data.run_server_flag:
        time.sleep(0.99999999)
        counter += 1
    return
