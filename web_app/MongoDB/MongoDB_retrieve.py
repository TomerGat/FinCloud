from MongoDB.MongoDB_general import *
from Fincloud_imports import *
from Fincloud_data_structs import *
from Fincloud_general_systems import *


def get_accounts_data(db):
    # function to create ledger from ledger item
    def item_to_ledger(item):
        return 1  # continue

    # function to create ledger from ledger item
    def item_to_trade_ledger(item):
        return 1  # continue

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

        # Accounts.log.append(ac)


def retrieve_data():
    # get connection string from file
    file_path = str(os.path.dirname(os.path.abspath(__file__))) + mongo_dir
    with open(file_path, 'r') as file:
        connection_string = file.read()
    db = get_database(DB_NAME, connection_string)

    # retrieve data from database into server data structures
    get_accounts_data(db)


retrieve_data()
