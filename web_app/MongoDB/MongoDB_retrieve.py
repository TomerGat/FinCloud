from MongoDB.MongoDB_general import *
from Fincloud_imports import *
from Fincloud_data_structs import *
from Fincloud_general_systems import *


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


def get_accounts_data(db):
    # function to create ledger from ledger item
    def item_to_ledger(item):
        new_ledger = Log()
        for entry_index in item.keys():
            entry_data = item[entry_index]
            action = entry_data['action type']
            amount = entry_data['amount']
            date = dict_to_date(entry_data['date'])
            target_num = entry_data['other num']
            target_dep = entry_data['other dep name']
            entry_id = entry_data['entry id']
            new_entry = Entry(action, amount, date, target_num, target_dep, entry_id)
            new_ledger.append(new_entry)

        return new_ledger

    # function to create ledger from ledger item
    def item_to_trade_ledger(item):
        new_trade_ledger = Log()
        for entry_index in item.keys():
            trade_entry_data = item[entry_index]
            cur_from = trade_entry_data['currency from']
            cur_to = trade_entry_data['currency to']
            amount = trade_entry_data['amount']
            conversion = trade_entry_data['conversion rate']
            date = dict_to_date(trade_entry_data['date'])
            new_t_entry = TradeEntry(cur_from, cur_to, amount, date, conversion)

    # function to create ledger from ledger item
    def item_to_inbox(item):
        return 1  # continue

    collection = db['Accounts']
    docs = list(collection.find())
    for doc in docs:
        ac_type = doc['account type']
        if ac_type == 'admin' or ac_type == 'reg':
            ac_number = doc['account number']
            inbox = item_to_inbox(doc['inbox'])
            spending_limit = doc['monthly limit']
            remaining_spending = doc['remaining spending']
            shift_date = doc['shift date']
            last_update = dict_to_date(doc['last update'])
            new_limit = doc['new monthly limit']
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
        elif ac_type == 'sav':
            pass
        elif ac_type == 'bus':
            pass
        else:
            return

        # Accounts.append(ac)


def retrieve_data():
    if not BACKUP_DATA_FLAG:
        return
    # get connection string from file
    file_path = str(os.path.dirname(os.path.abspath(__file__))) + mongo_dir
    with open(file_path, 'r') as file:
        connection_string = file.read()
    db = get_database(DB_NAME, connection_string)

    # retrieve data from database into server data structures
    get_accounts_data(db)
