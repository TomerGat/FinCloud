# import util functions and libraries
from Fincloud_util_functions import *


# data structures
class Log:  # object properties: log (contains a numpy array)
    # an array used to store other objects
    def __init__(self):
        self.log = np.array([])

    def append(self, val):
        self.log = np.append(self.log, [val])


class Table:  # object properties: body (contains a dictionary)
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

    def get_key(self, index):
        temp_table = reverse_dictionary(self.body)
        try:
            return temp_table[index]
        except KeyError:
            return -1


class Global:  # object properties: redirect_flags, responses, current_account, background_redirect_flags
    def __new__(cls):  # Global has only one instance so I define it as a singleton by overriding __new__ function
        if not hasattr(cls, 'instance'):
            cls.instance = super(Global, cls).__new__(cls)
        return cls.instance

    def __init__(self):  # each object property contains a dictionary {client address : data}
        self.redirect_flags = {}
        self.response_codes = {}
        self.current_account = {}
        self.background_redirect_flags = {}
        self.admin_token = hash(random.randint(0, 1000))

    def alter_rf(self, key, value):  # add/change key:value for redirect_flags
        self.redirect_flags[key] = value

    def alter_re(self, key, value):  # add/change key:value for responses
        self.response_codes[key] = value

    def alter_ca(self, key, value):  # add/change key:value for current_account
        self.current_account[key] = value

    def alter_brf(self, key, value):
        self.background_redirect_flags[key] = value

    def delete_ca(self, key):  # delete key:value from current_account
        del self.current_account[key]

    def delete_re(self, key):  # delete key:value from current_account
        del self.response_codes[key]

    def delete_brf(self, key):
        del self.background_redirect_flags[key]


# tables
name_table = Table()  # account name table - {account name: serial number}
number_table = Table()  # account number table - {account number: serial number}
pass_table = Table()  # password table - {serial number : hash value of account password}
phone_name_table = Table()  # account recovery recovery table - {hash value of phone number: account name}
loc_type_table = Table()  # account type table - {serial number: type of account (reg/bus/sav)}
value_summary_table = Table()  # value recovery table - {value summary: serial number}

# Accounts log
Accounts = Log()  # Log containing all Accounts

# class containing data that can be accessible from all locations in file
data = Global()

# set containing all existing account numbers
existing_account_numbers = set()

# existing entries id set
existing_entry_id = set()

# existing requests id set
existing_request_id = set()

# Shared Dictionary of Logs containing history of received packets  {ip address : Log}
# after session timeout, log for timed out account is erased
history = {}

# active requests, dictionary containing all current requests from accounts {ac index: [requests]}
active_requests = {}

# shared list containing addresses connected
addresses = []

# creating backup of last currency rates (relative to USD)
last_rates = create_value_table()
try:
    for cur in last_rates.keys():
        last_rates[cur] = converter.CurrencyRates().get_rate('USD', cur)
except converter.RatesNotAvailableError:
    # set to rates as of 7/2/2023
    last_rates = {'USD': 1, 'EUR': 0.93, 'JPY': 131.09, 'BGN': 1.82, 'CZK': 22.19, 'GBP': 0.83, 'CHF': 0.92,
                  'AUD': 1.44, 'BRL': 5.2, 'CAD': 1.34, 'CNY': 6.79, 'IDR': 15144.65, 'INR': 82.77,
                  'MXN': 18.91, 'SGD': 1.32}


# enum with all possible response codes
class Responses(Enum):
    # error responses
    SYSTEM_ERROR = -1
    SESSION_TIMEOUT = -2
    PROCESSING_ERROR = -3
    PHONE_NUM_NOT_FOUND = -4
    CODES_NOT_MATCH = -5
    AC_NAME_INVALID = -6
    AC_CODE_INVALID = -7
    NAME_AND_CODE_INVALID = -8
    AC_NAME_EXISTS = -9
    PHONE_NUM_INVALID = -10
    PHONE_NUM_EXISTS = -11
    INVALID_SAVING_RETURNS = -12
    COMP_NAME_INVALID = -13
    NAME_AND_COMP_INVALID = -14
    CODE_AND_COMP_INVALID = -15
    DATA_INVALID = -16
    INVALID_TRANSACTION = -17
    INVALID_INPUT_AMOUNT = -18
    DEP_NOT_FOUND = -19
    INSUFFICIENT_AMOUNT = -20
    TARGET_AC_NOT_FOUND = -21
    TARGET_DEP_WRONGLY_SET = -22
    TARGET_DEP_NOT_FOUND = -23
    TARGET_DEP_WRONGLY_UNSET = -24
    SOURCE_DEP_NOT_FOUND = -25
    CURRENCIES_NOT_FOUND = -26
    ALLOCATION_ID_INVALID = -27
    ALLOCATION_NOT_FOUND = -28
    DEP_NAME_EXISTS = -29
    DEP_NAME_INVALID = -30
    SOURCE_CUR_NOT_FOUND = -31
    TARGET_CUR_NOT_FOUND = -32
    AC_IDENTITY_INCORRECT = -33
    AC_CODE_INCORRECT = -34
    INVALID_SPENDING_LIMIT = -35

    # confirmation responses
    GENERAL_CONFIRM = 1  # general confirmation - no response output to ui
    ACCOUNT_RECOVERY_CONFIRM = 2
    NEW_ACCOUNT_CREATED = 3
    DEPOSIT_CONFIRM = 4
    WITHDRAWAL_CONFIRM = 5
    TRANSFER_CONFIRM = 6
    INNER_TRANSFER_CONFIRM = 7
    NEW_DEP_OPENED = 8
    CURRENCY_TRADE_CONFIRM = 9
    CLOUD_ALLOCATION_CONFIRM = 10
    CLOUD_WITHDRAWAL_CONFIRM = 11
    SPENDING_LIMIT_ALTERED = 12
    REQUEST_FILED = 13

    # empty response
    EMPTY_RESPONSE = 0

    # miscellaneous responses (numbers are random)
    SPENDING_LIMIT_BREACH = 717
    OVERSPEND_BY_TRANSFER = 135
    OVERSPEND_BY_WITHDRAWAL = 136
    OVERSPEND_BY_ALLOCATION = 137


# dictionary saving index of last checked entry for each account
# anomaly detection will start from this index when checking new entries
last_checked_entry = {}  # {ac index : index of last checked entry}

# possible entry types list
entry_types = ['d', 'w', 'tf', 'tt', 'tfi', 'tti']
