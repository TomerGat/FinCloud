# session timeout limit (in sec)
SESSION_LIMIT = 7200

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

# minimum length to check for anomalies in ledger (under certain limit , algorithm is not effective)
MIN_LENGTH_FOR_ANOMALY_DETECTION = 10

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

# ratio between number of entries and number of clusters to create in anomaly detection algorithm (must be full number)
CLUSTER_NUMBER_RATIO = 5  # tried 2.5, 3.75, 5.25, 4.75, 5 in tests
