from MongoDB.MongoDB_general import *
from Fincloud_imports import *
from Fincloud_data_structs import *
from Fincloud_general_systems import *


def get_accounts_data(db):
    # function to create departments array from item
    def item_to_departments(item):
        departments_arr = {}
        for dep_name in item.keys():
            dep_data = item[dep_name]
            departments_arr[dep_name] = (
                dict_values_tostring(dep_data['department value'], reverse=True),
                item_to_ledger(dep_data['ledger']),
                item_to_trade_ledger(dep_data['trade ledger'])
            )
        return departments_arr

    # function to create inbox from inbox item
    def item_to_inbox(item):
        ac_inbox = []
        for mes_index in item.keys():
            mes_data = item[mes_index]
            subject = mes_data['subject']
            message = mes_data['message']
            sender = mes_data['sender']
            mes_type = mes_data['message type']
            date = dict_to_date(mes_data['date'])
            mes_id = mes_data['message id']
            new_message = Message(subject, message, sender, mes_type)
            new_message.date = date
            new_message.message_id = mes_id
            ac_inbox.append(new_message)
        return ac_inbox

    # function to create ledger from ledger item
    def item_to_ledger(item):
        new_ledger = Log()
        for entry_index in item.keys():
            entry_data = item[entry_index]
            action = entry_data['action type']
            amount = float(entry_data['amount'])
            date = dict_to_date(entry_data['date'])
            target_num = entry_data['other num']
            target_dep = entry_data['other dep name']
            entry_id = entry_data['entry id']
            new_entry = Entry(action, amount, date, target_num, target_dep, entry_id)
            new_ledger.append(new_entry)
        return new_ledger

    # function to create trade ledger from trade ledger item
    def item_to_trade_ledger(item):
        new_trade_ledger = Log()
        for entry_index in item.keys():
            trade_entry_data = item[entry_index]
            cur_from = trade_entry_data['currency from']
            cur_to = trade_entry_data['currency to']
            amount = float(trade_entry_data['amount'])
            conversion = trade_entry_data['conversion rate']
            date = dict_to_date(trade_entry_data['date'])
            new_t_entry = TradeEntry(cur_from, cur_to, amount, date, conversion)
            new_trade_ledger.append(new_t_entry)
        return new_trade_ledger

    collection = db['Accounts']
    docs = list(collection.find())
    if len(docs) == 0:
        return
    for doc in docs:
        ac_type = doc['account type']
        if ac_type == 'admin' or ac_type == 'reg':
            ac_number = doc['account number']
            inbox = item_to_inbox(doc['inbox'])
            spending_limit = float(doc['monthly limit'])
            remaining_spending = float(doc['remaining spending'])
            shift_date = doc['shift date']
            last_update = dict_to_date(doc['last update'])
            new_limit = doc['new monthly limit']
            ac_value = dict_values_tostring(doc['account value'], reverse=True)
            ledger = item_to_ledger(doc['ledger'])
            trade_ledger = item_to_trade_ledger(doc['trade ledger'])
            ac = Account(spending_limit)
            ac.inbox = inbox
            ac.trade_ledger = trade_ledger
            ac.ledger = ledger
            ac.new_spending_limit = new_limit
            ac.last_update = last_update
            ac.shift_date = shift_date
            ac.remaining_spending = remaining_spending
            ac.account_number = ac_number
            ac.value = ac_value
        elif ac_type == 'sav':
            ac_number = doc['account number']
            inbox = item_to_inbox(doc['inbox'])
            ac_value = dict_values_tostring(doc['account value'], reverse=True)
            shift_date = doc['shift date']
            last_update = dict_to_date(doc['last update'])
            ledger = item_to_ledger(doc['ledger'])
            returns = doc['returns']
            fee = doc['fee']
            ac = SavingsAccount(returns)
            ac.fee = fee
            ac.inbox = inbox
            ac.ledger = ledger
            ac.last_update = last_update
            ac.shift_date = shift_date
            ac.account_number = ac_number
            ac.value = ac_value
        elif ac_type == 'bus':
            ac_number = doc['account number']
            inbox = item_to_inbox(doc['inbox'])
            departments = item_to_departments(doc['departments'])
            comp_name = doc['company name']
            ac = BusinessAccount(comp_name, [])
            ac.departments = departments
            ac.inbox = inbox
            ac.account_number = ac_number
        else:
            return

        Accounts.append(ac)


def get_tables_data(db):
    collection = db['Tables']
    docs = list(collection.find())  # this collection should only have one document
    if len(docs) == 0:
        return
    doc = docs[0]
    name_table.body = dict_values_tostring(doc['name table'], reverse=True)
    number_table.body = dict_values_tostring(dict_keys_tostring(doc['number table'], reverse=True), reverse=True)
    pass_table.body = dict_values_tostring(dict_keys_tostring(doc['pass table'], reverse=True), reverse=True)
    phone_name_table.body = dict_keys_tostring(doc['phone name table'], reverse=True)
    loc_type_table.body = dict_keys_tostring(doc['loc type table'], reverse=True)


def get_existing_numbers_data(db):
    collection = db['Existing_IDs']
    docs = list(collection.find())  # this collection should only have one document
    if len(docs) == 0:
        return
    doc = docs[0]
    existing_account_numbers.add(int(num) for num in doc['existing account numbers'].keys())
    existing_entry_id.add(int(num) for num in doc['existing entry id'].keys())
    existing_request_id.add(int(num) for num in doc['existing request id'].keys())
    existing_message_id.add(int(num) for num in doc['existing message id'].keys())


def get_requests_data(db):
    # function to create request from item
    def item_to_request(request_item):
        src_index = request_item['source index']
        src_dep = request_item['source dep']
        target_index = request_item['target index']
        target_dep = request_item['target dep']
        action = request_item['action type']
        amount = float(request_item['amount'])
        request_id = request_item['request id']
        date = dict_to_date(request_item['date'])
        entry_id = request_item['entry id']
        status = request_item['status']
        new_request = Request(Entry(action, amount, date, number_table.get_key(target_index), target_dep, entry_id), src_index, src_dep)
        new_request.status = status
        new_request.request_id = request_id
        return new_request

    collection = db['Requests']
    docs = list(collection.find())  # this collection should only have one document
    if len(docs) == 0:
        return
    doc = docs[0]
    active_requests_data = doc['active requests']  # type is {<index>: {<request>: ''}}
    for ac_index in active_requests_data.keys():
        active_requests[ac_index] = []
        requests_items = list(active_requests_data[ac_index].keys())
        for item in requests_items:
            request = item_to_request(item)
            active_requests[ac_index].append(request)

    previous_requests_data = doc['previous requests']  # type is {<index>: {<request>: ''}}
    for ac_index in previous_requests_data.keys():
        previous_requests[ac_index] = []
        requests_items = list(previous_requests_data[ac_index].keys())
        for item in requests_items:
            request = item_to_request(item)
            previous_requests[ac_index].append(request)


def get_security_data(db):
    collection = db['Security_Questions']
    docs = list(collection.find())  # this collection should only have one document
    if len(docs) == 0:
        return
    doc = docs[0]
    for key in doc:
        if key != '_id':
            security_questions[int(key)] = dict_values_tostring(doc[key], reverse=True)


def get_rates_data(db):
    collection = db['Last_Currency_Rates']
    docs = list(collection.find())  # this collection should only have one document
    if len(docs) == 0:
        return
    doc = docs[0]
    for key in doc:
        if key != '_id':
            last_rates[key] = doc[key]


def get_checked_data(db):
    collection = db['Last_Checked_Entry']
    docs = list(collection.find())  # this collection should only have one document
    if len(docs) == 0:
        return
    doc = docs[0]
    for key in doc:
        if key != '_id':
            last_checked_entry[int(key)] = doc[key]


def retrieve_data():
    if not BACKUP_DATA_FLAG:
        return
    # get connection string from file
    file_path = str(os.path.dirname(os.path.abspath(__file__))) + mongo_dir
    try:
        with open(file_path, 'r') as file:
            connection_string = file.read()
        db = get_database(DB_NAME, connection_string)
    except FileNotFoundError:
        print('\nMongoDB credentials not found. Set BACKUP_DATA_FLAG to False to run without MongoDB access.\n')
        return

    # retrieve data from database into server data structures
    try:
        get_accounts_data(db)
        get_tables_data(db)
        get_existing_numbers_data(db)
        get_requests_data(db)
        get_security_data(db)
        get_rates_data(db)
        get_checked_data(db)
    except KeyError:
        print('\nError while processing MongoDB data: KeyError.\n')
    except IndexError:
        print('\nError while processing MongoDB data: IndexError.\n')
    except errors.OperationFailure:
        print('\nMongoDB access failed.\n')
        return
