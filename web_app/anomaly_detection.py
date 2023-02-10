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


def find_cluster(gap: int, amount: int) -> int:
    cluster = int(amount/gap)
    return cluster


def calc_deviation(amount, avg, stdev):
    deviation = abs(amount - avg) / stdev
    return deviation


def create_clusters(counter: int) -> [[]]:
    segments = []
    for i in range(counter):
        segments.append([])
    return segments


def cluster_by_amount(action_clusters: {str: [Entry]}) -> {str: [[Entry]]}:
    general_clusters = {}
    for action in action_clusters.keys():  # run algorithm for each list of entries that are organized by action type
        group = action_clusters[action]
        counter = int(len(group) * CLUSTER_NUMBER_RATIO)
        largest_amount = 0
        # find largest amount in group
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
    clusters = cluster_by_amount(action_clusters)
    return median, avg, avg_before, clusters


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
    median, avg, avg_before, general_clusters = return_stats(ac_ledger, ac_index)

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
    # call function recursively if there are additional new entries (each call add index to parameter 'temp_indices')

    # find outliers in Entry clusters:
    # clusters with only one entry, with two adjacent clusters that are empty, will be identified as outliers
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

    # find outliers with standard deviation calculation
    amounts = [entry.amount for entry in ac_ledger.log]
    standard_deviation = statistics.stdev(amounts)
    for entry in ac_ledger.log:
        deviation = calc_deviation(entry.amount, avg, standard_deviation)
        if deviation >= MIN_DEVIATION_TO_FLAG and entry not in flagged_entries and entry in entries_to_check:
            flagged_entries.append(entry)

    # continue with additional options for flags
 

def anomaly_detection():  # background func
    while True:
        time.sleep(ANOMALY_DETECTION_CYCLE)  # wait

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
                            handle_anomaly(entry, index)
            # handle if account is business
            else:
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
                                handle_anomaly(entry, index)
