from FinCloud.web_app.Fincloud_general_systems import *


def handle_anomaly(anomaly_entry: Entry, ac_index):
    # create subject
    date = anomaly_entry.date
    date_str = str(date[0]) + '/' + str(date[1]) + '/' + str(date[2])
    subject = 'Transaction of type ' + anomaly_entry.action + ' on ' + date_str
    message = 'Red Flag raised for transaction:' + '\n'
    message += 'Transaction date: ' + date_str + '\n'
    message += 'Action type: ' + anomaly_entry.action + '\n'
    message += 'Transferred to account number: ' + (str(anomaly_entry.target_num) if anomaly_entry.target_num != -1 else 'none') + '\n'
    message += 'Transferred to department: ' + (str(anomaly_entry.target_dep) if anomaly_entry.target_dep != -1 else 'none') + '\n'
    message += 'Amount of transaction: ' + str(anomaly_entry.amount) + '\n'
    message += 'If this transaction is an error, or you suspect that it was caused by a malicious third-party, please file a request to the bank.' + '\n'
    message += 'Thank you,' + '\n'
    message += 'Transaction Anomaly Detection Team'
    send_message(ac_index, subject, message)


def return_stats(entries: Log) -> (int, float, {str: [Entry]}):
    amounts = []
    avg = 0
    clusters = {}
    ledger_len = len(entries.log)
    for etype in entry_types:
        clusters[etype] = []
    for entry in entries.log:
        entry_amount = entry.amount
        avg += entry_amount / ledger_len
        amounts.append(entry_amount)
        clusters[entry.action].append(entry)
    amounts.sort()
    median = amounts[int(ledger_len / 2) + 1] if ledger_len % 2 == 1 \
        else (amounts[int(ledger_len / 2)] + amounts[int(ledger_len / 2) + 1]) / 2
    return median, avg, clusters


def find_anomalies(ac_ledger: Log, ac_index: int, temp_indices: []) -> (bool, []):
    # if all entries in ledger were already checked, return False and an empty list
    if len(ac_ledger.log) == last_checked_entry[ac_index] + 1:
        return False, []

    # get stats on complete entry ledger
    median, avg, clusters = return_stats(ac_ledger)

    # separate entries that were not yet checked
    check_entries = ac_ledger.log[last_checked_entry[ac_index] + 1::]

    # update last_checked_entry to current number of entries
    last_checked_entry[ac_index] = len(ac_ledger.log) - 1

    # find anomalies in new entries
    # possible flags: relatively large transaction after x time without activity,
    #                 largest every transaction by x margin
    #                 causes change in average transfer stats above x percentage points,
    #                 large standard deviation,
    #                 first transaction of certain action type with large clusters of other types
    #                 transaction from savings account to department of business account that was previously empty
    # call function recursively if there are additional new entries (each call add index to parameter 'temp_indices')


def anomaly_detection():  # background func
    while True:
        time.sleep(7200)  # wait

        # update last_checked_entry to match number of existing accounts
        if len(last_checked_entry.keys()) != len(Accounts.log):
            counter = len(last_checked_entry.keys())
            for i in range(len(Accounts.log) - len(last_checked_entry.keys())):
                # for each account index that does not have a key in last_checked_entry, set to 0
                last_checked_entry[counter + i] = 0

        # go over Accounts log
        for index in range(len(Accounts.log)):
            ac_type = loc_type_table.in_table(index)
            anomalies_found = False
            anomaly_entry_indices = []
            ledger_to_check = Log()

            # handle if account is checking or savings
            if ac_type == 'reg' or ac_type == 'sav':
                ledger_to_check = Accounts.log[index].ledger
                # check if ledger has sufficient data to run algorithm
                if len(ledger_to_check.log) >= MIN_LENGTH_FOR_ANOMALY_DETECTION:
                    # find anomalies in account ledger
                    anomalies_found, anomaly_entry_indices = find_anomalies(ledger_to_check, index, [])
                    if anomalies_found:
                        # if anomalies were found, call handle function for each flagged entry
                        for entry_index in anomaly_entry_indices:
                            handle_anomaly(ledger_to_check[entry_index], index)
            # handle if account is business
            else:
                # go over each dep in business account
                for dep_name in Accounts.log[index].departments.keys():
                    ledger_to_check = Accounts.log[index].departments[dep_name][1]
                    # check if ledger has sufficient data to run algorithm
                    if len(ledger_to_check.log) >= MIN_LENGTH_FOR_ANOMALY_DETECTION:
                        # find anomalies in department ledger
                        anomalies_found, anomaly_entry_indices = find_anomalies(ledger_to_check, index, [])
                        if anomalies_found:
                            # if anomalies were found, call handle function for each flagged entry
                            for entry_index in anomaly_entry_indices:
                                handle_anomaly(ledger_to_check[entry_index], index)
