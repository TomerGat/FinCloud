# import general systems
from Fincloud_general_systems import *


# background functions
def session_timing():  # check for session timeout
    while True:
        for ip in addresses:
            if len(history[ip].log) >= 2:
                log_length = len(history[ip].log)
                time1 = history[ip].log[log_length - 2].lst[1]
                time2 = history[ip].log[log_length - 1].lst[1]
                timeDif = time_dif(time1, time2)
                if timeDif >= SESSION_LIMIT:
                    data.alter_brf(ip, True)
                    addresses.remove(ip)
                    history[ip] = Log()

        # for ip in addresses set
        # check if the same ip exists twice in history log
        # if so, check time dif between last two connection entries
        # if time dif is larger than session limit, set background redirect flag to true for the ip
        # if background redirect flag is set to true, delete address from addresses set and reset history log


def accounts_update():  # run update functions in savings and checking accounts
    while True:
        time.sleep(ACCOUNTS_UPDATE_CYCLE)  # update every 10 min
        if len(Accounts.log) != 0:
            for index in loc_type_table.body.keys():
                if loc_type_table.body[index] != 'bus':
                    Accounts.log[index].update()


def rates_update():  # update last currency rates to use if live rates are not available
    while True:
        time.sleep(RATES_UPDATE_CYCLE)
        for curr in last_rates.keys():
            try:
                last_rates[curr] = converter.CurrencyRates().get_rate('USD', curr)
            except converter.RatesNotAvailableError:
                pass


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
