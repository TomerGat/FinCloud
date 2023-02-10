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


def create_id_amount_dict(group: [Entry]) -> {int, int}:
    amounts_dict = {}
    keys = [ent.entry_id for ent in group]
    values = [ent.amount for ent in group]
    for index, keys in enumerate(keys):
        amounts_dict[keys] = values[index]
    return amounts_dict


def find_cluster(gap: int, amount: int) -> int:
    segment = int(amount/gap)
    return segment


def create_clusters(counter: int) -> [[]]:
    segments = []
    for i in range(counter):
        segments.append([])
    return segments


def cluster_by_amount(action_clusters: {str: [Entry]}) -> {str: [[Entry]]}:
    general_clusters = {}
    for action in action_clusters.keys():
        group = action_clusters[action]
        counter = int(len(group) * CLUSTER_NUMBER_RATIO)
        largest_amount = 0
        # find largest amount in group
        for entry in group:
            if entry.amount > largest_amount:
                largest_amount = entry.amount
        gap = largest_amount / counter  # gap - jumps of amount between segments defined by maximum amount and segment counter
        # create an array of counter length in which each segment has a list which will include entries in the amount range
        # amount range is index*gap to (index+1)*gap
        clusters = create_clusters(counter)
        for index in range(len(group)):
            cluster_index = find_cluster(gap, group[index].amount)
            if group[index].amount == largest_amount:
                cluster_index -= 1  # if amount is largest, index will be out of bounds
            clusters[cluster_index].append(group[index])
        general_clusters[action] = clusters
    return general_clusters


def return_stats(entries: Log, ac_index: int) -> (int, float, {str: [[Entry]]}):
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
    clusters = cluster_by_amount(action_clusters)
    return median, avg, avg_before, clusters


def find_anomalies(ac_ledger: Log, ac_index: int, temp_indices: []) -> (bool, []):
    # if all entries in ledger were already checked, return False and an empty list
    if len(ac_ledger.log) == last_checked_entry[ac_index] + 1:
        return False, []

    # get stats on complete entry ledger
    median, avg, avg_before, general_clusters = return_stats(ac_ledger, ac_index)

    # separate entries that were not yet checked
    entries_to_check = ac_ledger.log[last_checked_entry[ac_index] + 1::]

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
    # call function recursively if there are additional new entries (each call add index to parameter 'temp_indices')

    # find outliers in clusters and add to flagged_entries:
    for action in general_clusters.keys():
        clusters = general_clusters[action]
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


def anomaly_detection():  # background func
    while True:
        time.sleep(ANOMALY_DETECTION_CYCLE)  # wait

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
