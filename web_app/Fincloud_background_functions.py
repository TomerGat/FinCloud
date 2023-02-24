# import general systems
from Fincloud_general_systems import *
from MongoDB.MongoDB_backup import backup_data
from MongoDB.MongoDB_general import get_database


# background functions
def session_timing():  # check for session timeout
    while data.run_server_flag:
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
    while data.run_server_flag:
        wait_for_flag(ACCOUNTS_UPDATE_CYCLE)
        if not data.run_server_flag:
            continue
        if len(Accounts.log) != 0:
            for index in loc_type_table.body.keys():
                if loc_type_table.body[index] != 'bus':
                    Accounts.log[index].update()


def rates_update():  # update last currency rates to use if live rates are not available
    while data.run_server_flag:
        wait_for_flag(RATES_UPDATE_CYCLE)
        if not data.run_server_flag:
            continue
        for curr in last_rates.keys():
            try:
                last_rates[curr] = converter.CurrencyRates().get_rate('USD', curr)
            except converter.RatesNotAvailableError:
                pass


def refresh_admin_credentials():
    while data.run_server_flag:
        wait_for_flag(CREDENTIALS_UPDATE_CYCLE)
        if not data.run_server_flag:
            continue
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


def manage_backups(run_once=False):
    if BACKUP_DATA_FLAG:
        # get connection string from file
        file_path = str(os.path.dirname(os.path.abspath(__file__))) + general_mongo_dir + mongo_dir
        try:
            with open(file_path, 'r') as file:
                connection_string = file.read()
            db = get_database(DB_NAME, connection_string)
        except FileNotFoundError:
            print('\nMongoDB access failed\n')
            return

        if run_once:
            backup_data(db)
            return
        while data.run_server_flag:
            wait_for_flag(BACKUP_DATA_CYCLE)
            backup_data(db)


def anomaly_detection():
    while data.run_server_flag:
        wait_for_flag(ANOMALY_DETECTION_CYCLE)
        if not data.run_server_flag:
            continue
        # update last_checked_entry to match number of existing accounts
        if len(last_checked_entry.keys()) != len(Accounts.log):
            counter = len(last_checked_entry.keys())
            for i in range(len(Accounts.log) - counter):
                # for each account index that does not have a key in last_checked_entry, set to 0
                last_checked_entry[counter + i] = 0

        # if Accounts is empty, skip to next cycle
        if len(Accounts.log) == 0:
            continue

        # go over Accounts log
        for index in range(len(Accounts.log)):
            ac_type = loc_type_table.in_table(index)
            if ac_type == 'Admin':
                continue
            anomalies_found = False
            anomaly_entries = []
            ledger_to_check = Log()

            # handle if account is checking or savings
            if ac_type == 'reg' or ac_type == 'sav':
                ledger_to_check = Accounts.log[index].ledger
                # check if ledger has sufficient data to run algorithm
                if len(ledger_to_check.log) >= MIN_LENGTH_FOR_ANOMALY_DETECTION:
                    # find anomalies in account ledger
                    anomalies_found, anomaly_entries = find_anomalies(ledger_to_check, index)
                    if anomalies_found:
                        # if anomalies were found, call handle function for each flagged entry
                        for entry in anomaly_entries:
                            send_anomaly_message(entry, index)
            # handle if account is business
            elif ac_type == 'bus':
                # go over each dep in business account
                for dep_name in Accounts.log[index].departments.keys():
                    ledger_to_check = Accounts.log[index].departments[dep_name][1]
                    # check if ledger has sufficient data to run algorithm
                    if len(ledger_to_check.log) >= MIN_LENGTH_FOR_ANOMALY_DETECTION:
                        # find anomalies in department ledger
                        anomalies_found, anomaly_entries = find_anomalies(ledger_to_check, index)
                        if anomalies_found:
                            # if anomalies were found, call handle function for each flagged entry
                            for entry in anomaly_entries:
                                send_anomaly_message(entry, index)
