# imports:
import http.server
from http.server import BaseHTTPRequestHandler
import socket
import cgi
import datetime
import random
import numpy as np
from forex_python.converter import CurrencyRates
import smtplib
import multiprocessing
import time
from enum import Enum


# import objects from main file
from server_dev import *


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

# Dictionary of Logs containing history of received packets
history = {}

# set containing addresses connected
addresses = set()

# session timeout limit
session_limit = 1200
