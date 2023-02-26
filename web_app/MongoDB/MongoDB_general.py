from Fincloud_imports import *


def get_database(db_name, connection_string):
    # connect using MongoClient
    client = pymongo.MongoClient(connection_string)

    # return the database
    return client[db_name]


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(CustomEncoder, self).default(obj)
