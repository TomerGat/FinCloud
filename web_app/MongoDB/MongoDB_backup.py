from Fincloud_data_structs import *
from Fincloud_finals import *
from MongoDB.MongoDB_general import *


# backup functions
def backup_accounts(db):
    # function to create item for each account
    def create_account_item(ac_index):
        # function to create item for each ledger
        def create_ledger_item(log):
            ledger_item = {}
            for entry_index in range(len(log)):
                entry = log[entry_index]
                ledger_item[entry_index] = {
                    'action type': entry.action,
                    'amount': str(entry.amount),
                    'date': date_to_dict(entry.date),
                    'other num': entry.target_num,
                    'other dep name': entry.target_dep,
                    'entry id': entry.entry_id
                }
            return ledger_item

        # function to create item for each trade ledger
        def create_trade_ledger_item(log):
            trade_ledger_item = {}
            for entry_index in range(len(log)):
                trade_entry = log[entry_index]
                trade_ledger_item[entry_index] = {
                    'currency from': trade_entry.cur_from,
                    'currency to': trade_entry.cur_to,
                    'amount': str(trade_entry.amount),
                    'conversion rate': trade_entry.conversion_rate,
                    'date': date_to_dict(trade_entry.date)
                }
            return trade_ledger_item

        # function to create item for each inbox
        def create_inbox_item(message_list):
            inbox_item = {}
            for message_index in range(len(message_list)):
                message = message_list[message_index]
                inbox_item[message_index] = {
                    'subject': message.subject,
                    'message': message.message,
                    'sender': message.sender,
                    'message type': message.message_type,
                    'date': date_to_dict(message.date),
                    'message id': message.message_id
                }
            return inbox_item

        def create_departments_item(departments):
            departments_item = {}
            for dep_name in departments.keys():
                departments_item[dep_name] = {
                    'department value': dict_values_tostring(departments[dep_name][0]),
                    'ledger': create_ledger_item(departments[dep_name][1].log),
                    'trade ledger': create_trade_ledger_item(departments[dep_name][2].log)
                }
            return departments_item

        ac = Accounts.log[ac_index]
        ac_type = loc_type_table.in_table(ac_index)
        if ac_type == 'reg' or ac_type == 'admin':
            item = {
                'account type': ac_type,
                'account number': ac.account_number,
                'monthly limit': ac.monthly_spending_limit,
                'remaining spending': ac.remaining_spending,
                'shift date': ac.shift_date,
                'last update': date_to_dict(ac.last_update),
                'new monthly limit': ac.new_spending_limit,
                'account value': dict_values_tostring(ac.value),
                'ledger': create_ledger_item(ac.ledger.log),
                'trade ledger': create_trade_ledger_item(ac.trade_ledger.log),
                'inbox': create_inbox_item(ac.inbox)
            }
        elif ac_type == 'sav':
            item = {
                'account type': ac_type,
                'account value': str(ac.value),
                'returns': ac.returns,
                'last update': date_to_dict(ac.last_update),
                'shift date': ac.shift_date,
                'account number': ac.account_number,
                'ledger': create_ledger_item(ac.ledger.log),
                'fee': ac.fee,
                'inbox': create_inbox_item(ac.inbox)
            }
        elif ac_type == 'bus':
            item = {
                'account type': ac_type,
                'account number': ac.account_number,
                'inbox': create_inbox_item(ac.inbox),
                'departments': create_departments_item(ac.departments),
                'company name': ac.company_name
            }
        else:
            item = {}
        return item

    collection = db['Accounts']
    items = []
    for index in range(len(Accounts.log)):
        ac_item = create_account_item(index)
        items.append(ac_item)

    if len(items) == 0:
        return

    accounts_data = json.loads(json.dumps(items, cls=CustomEncoder))
    collection.delete_many({})
    collection.insert_many(accounts_data)


def backup_tables(db):
    tables_item = {}
    for table in [name_table, number_table, pass_table, phone_name_table, loc_type_table]:
        table_body = dict_values_tostring(dict_keys_tostring(table.body))
        tables_item[table.name] = table_body

    collection = db['Tables']
    collection.delete_many({})
    collection.insert_one(tables_item)


def backup_existing_numbers(db):
    def create_set_item(id_set):
        item = {}
        for number in id_set:
            item[number] = ''
        return item

    existing_numbers_item = {
        'existing account numbers': create_set_item(set_tostring(existing_account_numbers)),
        'existing entry id': create_set_item(set_tostring(existing_entry_id)),
        'existing request id': create_set_item(set_tostring(existing_request_id)),
        'existing message id': create_set_item(set_tostring(existing_message_id))
    }

    collection = db['Existing_IDs']
    collection.delete_many({})
    collection.insert_one(existing_numbers_item)


def backup_requests(db):  # use create_request_item() inner function
    def create_single_request_item(request):
        request_item = {
            'source index': request.source_index,
            'source dep': request.source_dep,
            'target index': request.target_index,
            'target dep': request.target_dep,
            'action type': request.action_type,
            'amount': request.amount,
            'request id': request.request_id,
            'date': date_to_dict(request.date),
            'entry_id': request.entry_id,
            'status': request.status
        }
        return request_item

    def create_requests_item(requests):
        requests_item = {}
        for index in range(len(requests)):
            requests_item[create_single_request_item(requests[index])] = ''
        return requests_item

    item = {
        'active requests': {},
        'previous requests': {}
    }
    for key in active_requests.keys():
        item['active requests'][key] = create_requests_item(active_requests[key])
    for key in previous_requests.keys():
        item['previous requests'][key] = create_requests_item(previous_requests[key])

    collection = db['Requests']
    collection.delete_many({})
    collection.insert_one(item)


def backup_security_questions(db):
    security_questions_item = dict_keys_tostring(security_questions)
    collection = db['Security_Questions']
    collection.delete_many({})
    collection.insert_one(security_questions_item)


def backup_last_rates(db):
    last_rates_item = last_rates
    collection = db['Last_Currency_Rates']
    collection.delete_many({})
    collection.insert_one(last_rates_item)


def backup_last_checked(db):
    last_checked_item = last_checked_entry
    collection = db['Last_Checked_Entry']
    collection.delete_many({})
    collection.insert_one(last_checked_item)


def backup_data(db):
    # delete current data in db and backup updated data
    try:
        backup_accounts(db)
        backup_tables(db)
        backup_existing_numbers(db)
        backup_requests(db)
        backup_security_questions(db)
        backup_last_rates(db)
        backup_last_checked(db)
    finally:
        pass
