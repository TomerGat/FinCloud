# imports:
import http.server
from http.server import BaseHTTPRequestHandler
import socket
import cgi
import datetime
import random
import numpy as np
from forex_python import converter
import smtplib
import multiprocessing
import threading
import time
from enum import Enum
import os


# necessary functions for data structure implementations
def reverse_dictionary(dic):
    keys = list(dic.keys())
    values = list(dic.values())
    reversed_dic = {}
    for i in range(len(keys)):
        reversed_dic[values[i]] = keys[i]
    return reversed_dic


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
        self.responses = {}
        self.current_account = {}
        self.background_redirect_flags = {}
        self.admin_token = hash(random.randint(0, 1000))

    def alter_rf(self, key, value):  # add/change key:value for redirect_flags
        self.redirect_flags[key] = value

    def alter_re(self, key, value):  # add/change key:value for responses
        self.responses[key] = value

    def alter_ca(self, key, value):  # add/change key:value for current_account
        self.current_account[key] = value

    def alter_brf(self, key, value):
        self.background_redirect_flags[key] = value

    def delete_ca(self, key):  # delete key:value from current_account
        del self.current_account[key]

    def delete_re(self, key):  # delete key:value from current_account
        del self.responses[key]

    def delete_brf(self, key):
        del self.background_redirect_flags[key]


# enum containing response codes
class Response(Enum):
    wrong_name = 1
    wrong_pass = 1
    # continue


# returns for savings account
returns_premium = 4
returns_medium = 2.75
returns_minimum = 2

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

# Shared Dictionary of Logs containing history of received packets  {ip address : Log}
# after session timeout, log for timed out account is erased
history = {}

# shared list containing addresses connected
addresses = []

# session timeout limit (in sec)
session_limit = 1200

# creating backup of last currency rates (relative to USD)
c = converter.CurrencyRates()
last_rates = {'USD': 0, 'EUR': 0, 'JPY': 0, 'BGN': 0, 'CZK': 0, 'GBP': 0, 'CHF': 0, 'AUD': 0, 'BRL': 0, 'CAD': 0,
              'CNY': 0, 'IDR': 0, 'INR': 0, 'MXN': 0, 'SGD': 0}
for cur in last_rates.keys():
    last_rates[cur] = c.get_rate('USD', cur)
