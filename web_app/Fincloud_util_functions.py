# import libraries file
from Fincloud_imports import *
from Fincloud_finals import *


# util functions
def digit_count(num: int) -> int:
    str_num = str(num)
    counter = 0
    for ch in str_num:
        counter += 1
    return counter


def multiple(vec: list) -> int:
    mul = 1
    for i in vec:
        mul *= i
    return mul


def sum_vec(vec: list) -> int:
    s = 0
    for i in vec:
        s += i
    return s


def limit_length(num: int) -> int:
    while digit_count(num) < HASH_LENGTH_LIMIT:
        num *= 10
    return num % (10**HASH_LENGTH_LIMIT)


def create_value_table():
    value_table = {'USD': 0, 'EUR': 0, 'JPY': 0, 'BGN': 0, 'CZK': 0, 'GBP': 0, 'CHF': 0, 'AUD': 0, 'BRL': 0, 'CAD': 0,
                   'CNY': 0, 'IDR': 0, 'INR': 0, 'MXN': 0, 'SGD': 0}
    return value_table


def validate_phone_number(phone):
    return validate_number(phone) and (len(str(phone)) == 10)


def validate_number(num):
    valid = True
    decimal_counter = 0
    num = str(num)
    if num[0] == '-':
        num = num[1::]
    for i in num:
        if not ((ord(i) > 47) and (ord(i) < 58)):
            if i == '.':
                decimal_counter += 1
            else:
                valid = False
                break
    if decimal_counter > 1:
        valid = False
    return valid


def validate_string(word):
    word = str(word)
    characters = []
    valid = True
    non_valid = [':', '(', '{', ')', '}', ',', '^', '<', '>', '+', '-', '*', '/', '%', '=', '|']
    counter = 0
    while counter < len(word):
        ch = word[counter]
        if ch in non_valid:
            valid = False
            break
        else:
            counter += 1
    return valid


def check_for_spaces(word):
    confirm = False
    for ch in word:
        if ch == ' ':
            confirm = True
            break
    return confirm


def divide_to_words(words):
    wordList = []
    temp_str = ''
    for ch in words:
        if ch != ' ':
            temp_str += ch
        else:
            if temp_str != '':
                wordList.append(temp_str)
            temp_str = ''
    if temp_str != '':
        wordList.append(temp_str)
    return wordList


def validate_comp_name(comp_name):
    if check_for_spaces(comp_name):
        valid = True
        for word in divide_to_words(comp_name):
            valid = validate_string(word)
            if not valid:
                return False
        return True
    else:
        return validate_string(comp_name)


def organize_comp_name(comp_name):
    words = divide_to_words(comp_name)
    new_name = ''
    for i in range(len(words)):
        new_name += words[i]
        if i != len(words)-1:
            new_name += " "
    return new_name


def generate_code():
    number = random.randint(100000, 999999)
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
    year = int(now[0:4])
    month = int(now[5:7])
    day = int(now[8:10])
    return np.array([year, month, day])


def get_precise_time():
    now = str(datetime.datetime.now())
    year = int(now[0:4])
    month = int(now[5:7])
    day = int(now[8:10])
    hour = int(now[11:13])
    minute = int(now[14:16])
    second = int(now[17:19])
    return np.array([year, month, day, hour, minute, second])


def time_dif(last, current):
    delta = current[5] - last[5]  # add seconds
    delta += 60 * (current[4] - last[4])  # add minutes
    delta += 60 * 60 * (current[3] - last[3])  # add hours
    delta += 24 * 60 * 60 * (current[2] - last[2])  # add days
    delta += 30 * 24 * 60 * 60 * (current[1] - last[1])  # add months
    delta += 365 * 24 * 60 * 60 * (current[0] - last[0])  # add years
    return delta  # time delta in seconds
