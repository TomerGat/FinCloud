# session timeout limit (in sec)
SESSION_LIMIT = 600

# time to wait after updating history logs before checking background redirect flags
REQUEST_WAIT = 0.75

# limit for length of hash function output (hash values)
HASH_LENGTH_LIMIT = 30

# returns options for savings accounts (annual %)
RETURNS_PREMIUM = 4
RETURNS_MEDIUM = 2.75
RETURNS_MINIMUM = 2

# background threads data - time (in sec) to wait between running of functions
ACCOUNTS_UPDATE_CYCLE = 600
RATES_UPDATE_CYCLE = 7200
CREDENTIALS_UPDATE_CYCLE = 28800
ANOMALY_DETECTION_CYCLE = 64800
BACKUP_DATA_CYCLE = 300

# minimum length to check for anomalies in ledger (under certain limit , algorithm is not effective)
MIN_LENGTH_FOR_ANOMALY_DETECTION = 15

# ratio between product of deviation percentage times the spending limit, and the fee for the deviation
OVERSPENDING_FEE_RATIO = 0.2

# percentage of total account value set as maximum underspending bonus
UNDERSPENDING_BONUS_RATIO = 0.025

# minimum percentage of spending limit used to be entitled to underspending bonus
MINIMUM_SPENDING_RATIO_FOR_BONUS = 0.15

# fee incurred for different returns
PREMIUM_RETURNS_FEE = 100
MEDIUM_RETURNS_FEE = 80
MINIMUM_RETURNS_FEE = 50

# ratio between number of entries and number of clusters to create in anomaly detection algorithm
CLUSTER_NUMBER_RATIO = 0.75

# minimum deviation from standard to flag transaction
MIN_DEVIATION_RATIO_TO_FLAG = 2.75

# whether or not to flag inner transfers (config - can be changed)
FLAG_INNER_TRANSFERS = False

# mongodb credentials dir
mongo_dir = '\\mongo_credentials\\mongo_connection_string.txt'

# general mongodb files dir
general_mongo_dir = '\\MongoDB'

# admin credentials dir
admin_dir = '\\credentials'

# admin credentials file path
admin_file_path = '\\Admin_credentials.txt'

# database name
DB_NAME = 'FinCloud_Database'

# whether or not to access data on MongoDB (config - set to False to run without db connection)
BACKUP_DATA_FLAG = True

logo_path = '/fincloud_logo'

logo_dir = '\\vault\\logo_transparent.png'
