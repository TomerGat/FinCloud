# To do list:
# entry searching, cloud creation + transfers, account/business account summary - complete?
# allow transfer from regular to business accounts, business to regular accounts - complete?
# create protocol for bad input + allow scenario with no input
# print request summary on server side - details
# entry search by action
# test all situations!
# create combined array for all accounts
# check names of other accounts in create account function
# current create account function doesn't work because of endless loop in case of identical account name
# allow several allocations (with different codes), use array inside tempo cloud

# for final project:
# build encryption
# change code to fit http server (support multiple users)
# use hash table to check existence of account names
# change recv/send to built function
# use global variables when needed (append ledger function, create account function)
# red flag abnormal transfers (if account has over 5 entries, and a transfer/withdrawal is double the  average action)
# maybe hash table for entries? maybe not instead of ledger, but in addition for red flag identifications
# maybe log with ip addresses that connected to server (hash table with ip addresses and account names), phone numbers?
# allow multi-threading, create function for handling requests, use existing ui?
# use append ledger functions instead of repeating complicated action
# find solution for updating Ledgers/Accounts log in functions
# allow multiple actions in current account after verification
# think about how to do a "remember me" function (maybe with ip hash table? after connecting to server ask user)


# imports:
import socket
import numpy as np
import datetime
from forex_python.converter import CurrencyRates

# general setup:
S_Ledgers = np.array([])
S_Accounts = np.array([])
Ledgers = np.array([])
Accounts = np.array([])
BusinessLedgers = np.array([])
BusinessAccounts = np.array([])
c = CurrencyRates()


# returns for savings accounts(calculated with java program):
annualReturn_reg = 1.02  # regular annual return
monthlyReturn_reg = 1.00165  # regular monthly return
dailyReturn_reg = 1.00005425  # regular daily return
annualReturn_prem = 1.04  # premium annual return
monthlyReturn_prem = 1.0033  # premium monthly return
dailyReturn_prem = 1.000109  # premium daily return

# other constants (request answers):
approve = 'request approved'
refuse = 'request not approved'

# sockets setup:
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 9876))
server_socket.listen()
print("FinCloud is up and running")
(client_socket, client_address) = server_socket.accept()
print("Client connected")


# classes:
class HashTable:
    def __init__(self):
        self.body = {}

    def add_value(self, val):
        loc = len(self.body)
        self.body[hash_function(val)] = loc

    def in_table(self, val):
        try:
            return self.body[hash_function(val)]
        except KeyError:
            return -1


class Entry:
    def __init__(self, amount, action):
        self.amount = amount
        self.action = action


class businessEntry:
    def __init__(self, amount, action, department):
        self.amount = amount
        self.action = action
        self.department = department


class BusinessAccount:
    def __init__(self, code, companyName, departmentsArray):
        self.code = code
        self.companyName = companyName
        self.departmentsArray = departmentsArray

    def withdraw(self, cash, businessLedger):
        verify, source = businessVerification(self)
        if verify == True:
            amount = int(client_socket.recv(1024).decode())
            if cash.value >= amount:
                cash.value = cash.value + amount
                self.departmentsArray[source].value = self.departmentsArray[source].value - amount
                businessLedger.departmentsArray[source].array = np.append(businessLedger.departmentsArray[source].array, [businessEntry(amount, 'w', source)])
                client_socket.send('request approved'.encode())
            else:
                client_socket.send('request not approved'.encode())
        else:
            client_socket.send('request not approved'.encode())

    def checkBalance(self):
        verify, target = businessVerification(self)
        if verify == True:
            balance = str(self.departmentsArray[target].value)
            client_socket.send(balance.encode())
        else:
            client_socket.send('request not approved'.encode())

    def deposit(self, cash, businessLedger):
        verify, target = businessVerification(self)
        if verify == True:
            amount = int(client_socket.recv(1024).decode())
            if cash.value >= amount:
                cash.value = cash.value - amount
                self.departmentsArray[target].value = self.departmentsArray[target].value + amount
                businessLedger.departmentsArray[target].array = np.append(businessLedger.departmentsArray[target].array, [businessEntry(amount, 'd', target)])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())

    def departmentalTransfer(self, businessLedger):
        verify, source = businessVerification(self)
        if (verify == True):
            amount = int(client_socket.recv(1024).decode())
            if (self.departmentsArray[source].value >= amount):
                target = int(client_socket.recv(1024).decode()) - 1
                self.departmentsArray[source].value = self.departmentsArray[source].value - amount
                self.departmentsArray[target].value = self.departmentsArray[target].value + amount
                businessLedger.departmentsArray[source].array = np.append(businessLedger.departmentsArray[source].array, [businessEntry(amount, 'dtAway', target)])
                businessLedger.departmentsArray[target].array = np.append(businessLedger.departmentsArray[target].array, [businessEntry(amount, 'dtTo', source)])
                client_socket.send('request approved'.encode())
            else:
                client_socket.send('request not approved'.encode())
        else:
            client_socket.send('request not approved'.encode())

    def outerTransfer_bus2reg(self, businessLedger, Ledgers):  # in dev!!!!
        verify, source = businessVerification(self)
        if verify == True:
            amount = int(client_socket.recv(1024).decode())
            if self.departmentsArray[source].value >= amount:
                targetAC = client_socket.recv(1024).decode()
                found = False
                for i in range(Accounts.size):
                    if Accounts[i].name == targetAC:
                        client_socket.send('all good'.encode())
                        targetAC = i
                        found = True
                        break
                if found == True:
                    self.departmentsArray[source].value = self.departmentsArray[source].value - amount
                    Accounts[targetAC].value = Accounts[targetAC].value + amount
                    businessLedger.departmentsArray[source].array = np.append(businessLedger.departmentsArray[source].array, [businessEntry(amount, 'tAway_bus2reg', source)])
                    Ledgers[targetAC - 1].array = np.append(Ledgers[targetAC - 1].array, [Entry(amount, 'tTo_bus2reg')])
                else:
                    client_socket.send('nope'.encode())
            else:
                client_socket.send('request not approved'.encode())
        else:
            client_socket.send('request not approved'.encode())

    def outerTransfer(self, businessLedger):
        verify, source = businessVerification(self)
        if (verify == True):
            amount = int(client_socket.recv(1024).decode())
            if (self.departmentsArray[source].value >= amount):
                target = client_socket.recv(1024).decode()
                found = False
                for i in range(BusinessAccounts.size):
                    if BusinessAccounts[i].companyName == target:
                        client_socket.send('yes'.encode())
                        target = i
                        found = True
                        break
                if found == True:
                    target_dep = int(client_socket.recv(1024).decode()) - 1
                    self.departmentsArray[source].value = self.departmentsArray[source].value - amount
                    BusinessAccounts[target].departmentsArray[target_dep].value = \
                    BusinessAccounts[target].departmentsArray[target_dep].value + amount
                    businessLedger.departmentsArray[source].array = np.append(businessLedger.departmentsArray[source].array, [businessEntry(amount, 'otAway', source)])
                    BusinessLedgers[target].departmentsArray[target_dep].array = np.append(BusinessLedgers[target].departmentsArray[target_dep].array, [businessEntry(amount, 'otTo', target_dep)])
                    client_socket.send('request approved'.encode())
                else:
                    client_socket.send('no'.encode())
                    client_socket.send('request not approved'.encode())
            else:
                client_socket.send('request not approved'.encode())
        else:
            client_socket.send('request not approved'.encode())


class businessLedger:
    def __init__(self, departmentsArray):
        self.departmentsArray = departmentsArray


class Account:
    def __init__(self, value, code, name):
        self.value = value
        self.code = code
        self.name = name

    def transferFrom_reg2bus(self, Ledger, BusinessLedgers):  # transfer from self to a business account - in dev!!!!
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if self.value >= amount:
                counter = 0
                businessName = client_socket.recv(1024).decode()
                for i in range(BusinessAccounts.size):
                    if BusinessAccounts[i].companyName == businessName:
                        transferTo = i
                        break
                    else:
                        counter = counter + 1
                if BusinessAccounts.size == counter:
                    client_socket.send('request not approved'.encode())
                else:
                    client_socket.send('all good'.encode())
                    self.value = self.value - amount
                    targetDep = int(client_socket.recv(1024).decode())
                    BusinessAccounts[transferTo].departmentsArray[targetDep].value = BusinessAccounts[transferTo].departmentsArray[targetDep].value + amount
                    Ledger.array = np.append(Ledger.array, [Entry(amount, 'tAway_reg2bus')])
                    BusinessLedgers[transferTo].departmentsArray[targetDep].array = np.append(BusinessLedgers[transferTo].departmentsArray[targetDep].array, [businessEntry(amount, 'tTo_reg2bus', targetDep)])
                    client_socket.send('request approved'.encode())
            else:
                client_socket.send('request not approved'.encode())
        else:
            client_socket.send('request not approved'.encode())

    def transferFrom(self, Ledger, Ledgers):  # transfer from self
        verify = verification(self)
        if verify == True:
            amount = int(client_socket.recv(1024).decode())
            if self.value >= amount:
                transferTo = client_socket.recv(1024).decode()
                for i in range(Accounts.size):
                    if Accounts[i].name == transferTo:
                        acc = Accounts[i]
                        transferTo = i
                        break
                acc.value = acc.value + amount
                self.value = self.value - amount
                Ledgers[transferTo - 1].array = np.append(Ledgers[transferTo - 1].array, [Entry(amount, "tTo")])
                Ledger.array = np.append(Ledger.array, [Entry(amount, "tAway")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())

    def deposit(self, cash, ledger):  # deposit to self
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if cash.value >= amount:
                cash.value = cash.value - amount
                self.value = self.value + amount
                ledger.array = np.append(ledger.array, [Entry(amount, "d")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())

    def withdraw(self, cash, ledger):  # withdraw from self
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if self.value >= amount:
                cash.value = cash.value + amount
                self.value = self.value - amount
                ledger.array = np.append(ledger.array, [Entry(amount, "w")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())

    def checkBalance(self):  # print account balance
        verify = verification(self)
        if verify == True:
            balance = str(self.value)
            client_socket.send(balance.encode())
        else:
            client_socket.send("request not approved".encode())


class Account2:
    def __init__(self, code, name):
        global password_table
        global accountName_table
        self.value = create_value_table()
        self.code = code
        self.name = name
        password_table.add_value(code)
        accountName_table.add_value(name)

    def getValue(self): # delete later - assist for dev
        return self.value

    def startMining(self):
        verify = verification(self)
        if verify:
            mining_rate = client_socket.recv(1024).decode()  # number of bitcoins per year
            mining_fine = mining_rate * c.convert('BTC', 'USD', 1) * 0.6
            if (self.value[1][0] >= mining_fine) or (self.value[1][15] >= mining_rate*int(0.6)):
                self.value[1][17] = get_date()
                self.value[1][18] = mining_rate
                self.value[1][19] = mining_fine
                client_socket.send('request approved. Account now mining BTC'.encode())
                if self.value[1][0] >= mining_fine:
                    self.value[1][0] = self.value[1][0] - mining_fine
                else:
                    self.value[1][15] = self.value[1][15] - mining_rate * int(0.6)
            else:
                client_socket.send('request not approved'.encode())

        else:
            client_socket.send('request not approved'.encode())

    def updateBTCmining(self):
        temp = self.value[1][20]
        self.value[1][15] = self.value[1][15] - temp
        self.value[1][20] = 0
        currentDate = get_date()
        days = 365*(self.value[1][17]-currentDate[0])  # years dif
        days = days + 30*(self.value[1][17]-currentDate[1])  # months dif
        days = days + (self.value[1][17]-currentDate[2])  # days dif
        time = days/365
        self.value[1][20] += time * self.value[1][18]
        self.value[1][20] += temp
        self.value[1][15] += self.value[1][20]

    def deposit(self, ledger_num):  # deposit to self
        global Ledgers
        global cash
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if cash.value >= amount:
                cash.value = cash.value - amount
                self.value[1][0] = self.value[1][0] + amount
                Ledgers[ledger_num].array = np.append(Ledgers[ledger_num].array, [Entry(amount, "d")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())

    def withdraw(self, ledger_num):  # withdraw from self
        global Ledgers
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if self.value[1][0] >= amount:
                cash.value = cash.value + amount
                self.value[1][0] = self.value[1][0] - amount
                Ledgers[ledger_num].array = np.append(Ledgers[ledger_num].array, [Entry(amount, "w")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())

    def checkBalanceUSD(self):  # print account balance
        verify = verification(self)
        if verify:
            balance = str(self.value[1][0])
            client_socket.send(balance.encode())
        else:
            client_socket.send("request not approved".encode())

    def printBalances(self):
        verify = verification(self)
        if verify:
            for i in range(16):
                if i != 15:
                    print('{}: {}'.format(self.value[0][i], self.value[1][i]), end=', ')
                else:
                    print('{}: {}'.format(self.value[0][i], self.value[1][i]))
        else:
            print('request not approved')

    def transferFrom_USD(self, ledger_num):  # transfer from self
        global Ledgers
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if self.value[1][0] >= amount:
                transferTo = client_socket.recv(1024).decode()
                for i in range(Accounts.size):
                    if Accounts[i].name == transferTo:
                        acc = Accounts[i]
                        transferTo = i
                        break
                acc.value[1][0] = acc.value[1][0] + amount
                self.value[1][0] = self.value[1][0] - amount
                Ledgers[transferTo - 1].array = np.append(Ledgers[transferTo - 1].array, [Entry(amount, "tTo")])
                Ledgers[ledger_num].array = np.append(Ledgers[ledger_num].array, [Entry(amount, "tAway")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())

    def transferFrom_reg2bus_USD(self, ledger_num):  # transfer from self to a business account - in dev!!!
        global BusinessLedgers
        global Ledgers
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if self.value[1][0] >= amount:
                counter = 0
                businessName = client_socket.recv(1024).decode()
                for i in range(BusinessAccounts.size):
                    if BusinessAccounts[i].companyName == businessName:
                        transferTo = i
                        break
                    else:
                        counter = counter + 1
                if BusinessAccounts.size == counter:
                    client_socket.send('request not approved'.encode())
                else:
                    client_socket.send('all good'.encode())
                    self.value[1][0] = self.value[1][0] - amount
                    targetDep = int(client_socket.recv(1024).decode())
                    BusinessAccounts[transferTo].departmentsArray[targetDep].value = BusinessAccounts[transferTo].departmentsArray[targetDep].value + amount
                    Ledgers[ledger_num].array = np.append(Ledgers[ledger_num].array, [Entry(amount, 'tAway_reg2bus')])
                    BusinessLedgers[transferTo].departmentsArray[targetDep].array = np.append(BusinessLedgers[transferTo].departmentsArray[targetDep].array, [businessEntry(amount, 'tTo_reg2bus', targetDep)])
                    client_socket.send('request approved'.encode())
            else:
                client_socket.send('request not approved'.encode())
        else:
            client_socket.send('request not approved'.encode())

    def tradeBTC(self):
        verify = verification(self)
        if verify:
            action = client_socket.recv(1024).decode()
            if action == 'buy':
                amount = client_socket.recv(1024).decode()
                if self.value[1][0] >= amount:
                    self.value[1][15] = self.value[1][15] + amount
                    self.value[1][0] = self.value[1][0] - amount
            else:
                amount = client_socket.recv(1024).decode()
                if self.value[1][15] >= amount:
                    self.value[1][15] = self.value[1][15] - amount
                    self.value[1][0] = self.value[1][0] + amount
            client_socket.send('request approved'.encode())
        else:
            client_socket.send('request not approved'.encode())

    def trade_currencies(self):
        verify = verification(self)
        if verify:
            targetC = ''
            sourceC = ''
            targetC_index = 0
            sourceC_index = 0
            check = False
            if self.value[1][16] == False:
                sourceC = 'USD'
                sourceC_index = 0
                check = True
                self.value[1][16] = check
            else:
                sourceC = str(client_socket.recv(1024).decode())
                for i in range(16):
                    if self.value[0][i] == sourceC:
                        check = True
                        sourceC_index = i
            if check:
                self.value[1][16] = True
                check = False
                targetC = str(client_socket.recv(1024).decode())
                for i in range(16):
                    if (self.value[0][i] == targetC) and (targetC != sourceC):
                        check = True
                        targetC_index = i
                if check:
                    amount = int(client_socket.recv(1024).decode())
                    self.value[1][sourceC_index] = self.value[1][sourceC_index] - amount
                    amount = c.convert(sourceC, targetC, amount)
                    self.value[1][targetC_index] = self.value[1][targetC_index] + amount
                    client_socket.send('request approved'.encode())
                else:
                    client_socket.send('Request not approved'.encode())
            else:
                client_socket.send('Request not approved'.encode())

class Ledger:
    def __init__(self, array):
        self.array = array


class SavingsAccount: # in dev!!!!!
    def __init__(self, value, code, name, returns):
        self.code = code
        self.name = name
        self.returns = returns
        self.lastUpdate = get_date()
        if returns == annualReturn_prem:
            self.value = value * 0.975
        else:
            self.value = value

    def fee(self):
        if self.value >= 25:
            self.value = self.value - 25

    def update(self):
        currentDate = get_date()
        days = 365*(self.lastUpdate[0]-currentDate[0])  # years dif
        days = days + 30*(self.lastUpdate[1]-currentDate[1])  # months dif
        days = days + (self.lastUpdate[2]-currentDate[2])  # days dif
        self.lastUpdate = currentDate
        if self.returns == annualReturn_prem:
            temp = dailyReturn_prem
        else:
            temp = dailyReturn_reg
        self.value = self.value * (temp ** days)

    def deposit(self, cash, Ledger):  # deposit to self
        self.update()
        verify = verification(self)
        if verify == True:
            amount = int(client_socket.recv(1024).decode())
            if (cash.value >= amount):
                cash.value = cash.value - amount
                self.value = self.value + amount
                Ledger.array = np.append(Ledger.array, [Entry(amount, "d")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())
        self.fee()

    def withdraw(self, cash, Ledger):  # withdraw from self
        self.update()
        verify = verification(self)
        if verify:
            amount = int(client_socket.recv(1024).decode())
            if self.value >= amount:
                cash.value = cash.value + amount
                self.value = self.value - amount
                Ledger.array = np.append(Ledger.array, [Entry(amount, "w")])
                client_socket.send("request approved".encode())
            else:
                client_socket.send("request not approved".encode())
        else:
            client_socket.send("request not approved".encode())
        self.fee()


class tempo:  # in dev!!!!!!!
    def __init__(self, value, allocationCode):
        self.value = value
        self.allocationCode = allocationCode

    def checkValue(self):  # in dev!!
        if self.value == 0:
            client_socket.send('noValue'.encode())
        else:
            client_socket.send('all good'.encode())
        code_attempt = int(client_socket.recv(1024).decode())
        if self.allocationCode == code_attempt:
            toSend = str(self.value)
            client_socket.send('all good'.encode())
            client_socket.send(toSend.encode())
        else:
            client_socket.send('request not approved'.encode())

    def receive(self):  # from account to cloud
        allocation = 0
        ac = client_socket.recv(1024).decode()
        regORbus = 0
        for i in range(Accounts.size):
            if Accounts[i].name == ac:
                ac = i
                regORbus = 1
                break
        if regORbus == 0:
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].companyName == ac:
                    ac = i
                    regORbus = 2
                    break
        option = str(regORbus)
        client_socket.send(option.encode())
        if regORbus == 0:
            client_socket.send('request not approved'.encode())
        else:
            if regORbus == 1:
                verify = verification(Accounts[ac])
                if verify == True:
                    amount = int(client_socket.recv(1024).decode())
                    if Accounts[ac].value >= amount:
                        allocation_code = int(client_socket.recv(1024).decode())
                        self.allocationCode = allocation_code
                        self.value = self.value + amount
                        Accounts[ac].value = Accounts[ac].value - amount
                        Ledgers[ac - 1].array = np.append(Ledgers[ac - 1].array, [Entry(amount, 'toCloud')])
                        client_socket.send('request approved'.encode())
                    else:
                        client_socket.send('request not approved'.encode())
                else:
                    client_socket.send('request not approved'.encode())
            else:
                verify, source = businessVerification(BusinessAccounts[ac])
                if verify == True:
                    amount = client_socket.recv(1024).decode()
                    if BusinessAccounts[ac].departmentsArray[source].value >= amount:
                        allocation_code = int(client_socket.recv(1024).decode())
                        self.allocationCode = allocation_code
                        self.value = self.value + amount
                        BusinessAccounts[ac].departmentsArray[source].value = BusinessAccounts[ac].departmentsArray[source].value - amount
                        BusinessLedgers[ac].departmentsArray[source].array = np.append(BusinessLedgers[ac].departmentsArray[source].array, [businessEntry(amount, 'toCloud', source)])
                        client_socket.send('request approved'.encode())
                    else:
                        client_socket.send('request not approved'.encode())
                else:
                    client_socket.send('request not approved'.encode())

    def allocate(self):  # from cloud to account
        ac = recv_message(client_socket, 'str')
        regORbus = 0
        for i in range(Accounts.size):
            if Accounts[i].name == ac:
                ac = i
                regORbus = 1
                break
        if regORbus == 0:
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].companyName == ac:
                    ac = i
                    regORbus = 2
                    break
        option = str(regORbus)
        send_message(client_socket, option)
        if regORbus == 1:
            verify = verification(Accounts[ac])
            if verify == True:
                amount = recv_message(client_socket, 'int')
                if self.value >= amount:
                    send_message(client_socket, 'yes')
                    code_attempt = recv_message(client_socket, 'int')
                    if self.allocationCode == code_attempt:
                        send_message(client_socket, 'yes')
                        Accounts[ac].value = Accounts[ac].value + amount
                        self.value = self.value - amount
                        Ledgers[ac - 1].array = np.append(Ledgers[ac - 1].array, [Entry(amount, 'fromCloud')])
                        if self.value == 0:
                            self.allocationCode = 0
                            send_message(client_socket, 'cloud reset')
                        else:
                            send_message(client_socket, refuse)
                    else:
                        send_message(client_socket, refuse)
                else:
                    send_message(client_socket, refuse)
            else:
                send_message(client_socket, refuse)
        elif regORbus == 2:
            verify, target = businessVerification(BusinessAccounts[ac])
            if verify == True:
                amount = recv_message(client_socket, 'int')
                if self.value >= amount:
                    code_attempt = recv_message(client_socket, 'int')
                    if self.allocationCode == code_attempt:
                        BusinessAccounts[ac].departmentsArray[target].value = BusinessAccounts[ac].departmentsArray[target].value + amount
                        self.value = self.value - amount
                        BusinessLedgers[ac].departmentsArray[target].array = np.append(
                            BusinessLedgers[ac].departmentsArray[target].array,
                            [businessEntry(amount, 'fromCloud', target)])
                        send_message(client_socket, approve)
                    else:
                        send_message(client_socket, refuse)
                else:
                    send_message(client_socket, refuse)
            else:
                send_message(client_socket, refuse)
        else:
            send_message(client_socket, refuse)


# functions:
def create_value_table():
    value_options = np.array(['USD', 'EUR', 'JPY', 'BGN', 'CZK', 'GBP', 'CHF', 'AUD', 'BRL', 'CAD', 'CNY', 'IDR', 'INR', 'MXN', 'SGD', 'BTC', 'history', 'mining start date', 'mining rate', 'mining fine', 'mined BTC'])
    for i in value_options:
        value_options = np.append(value_options, [0])
    value_options = np.reshape(value_options, (2, 21))
    value_options[1][16] = False
    return value_options


def hash_function(text):
    text = str(text)
    val = 0
    for ch in text:
        val = (val*281 ^ ord(ch)*997) & 0xFFFFFFFF
    return val


def recv_message(skt, type):
    if type == 'int':
        return int(skt.recv(1024).decode())
    elif type == 'str':
        return str(skt.recv(1024).decode())


def send_message(skt, msg):
    skt.send(msg.encode())


def verification(acc):
    code_attempt = int(client_socket.recv(1024).decode())
    if code_attempt == acc.code:
        return True
    else:
        return False


def get_date():
    now = str(datetime.datetime.now())
    year = now[0:4]
    month = now[5:7]
    day = now[8:10]
    date = np.array([year, month, day])
    return date


def businessVerification(BusinessAccount):
    code_attempt = int(client_socket.recv(1024).decode())
    if code_attempt == BusinessAccount.code:
        dep = int(client_socket.recv(1024).decode()) - 1
        depCode_attempt = int(client_socket.recv(1024).decode())
        if depCode_attempt == BusinessAccount.departmentsArray[dep].code:
            return True, dep
        else:
            return False, 0
    else:
        return False, 0


def findEntry():
    global Accounts
    global Ledgers
    ac = client_socket.recv(1024).decode()
    counter = 0
    ledger_ = 0
    for i in range(Accounts.size):
        if Accounts[i].companyName == ac:
            ledger_ = i - 1
            break
        else:
            counter = counter + 1
    if Accounts.size == counter:
        client_socket.send('request not approved'.encode())
    else:
        client_socket.send('all good'.encode())
        verify = verification(Accounts[ledger_])
        if verify == True:
            client_socket.send('yes'.encode())
            index = int(client_socket.recv(1024).decode()) - 1
            amount_ = str(Ledgers[ledger_].array[index].amount)
            action_ = str(Ledgers[ledger_].array[index].action)
            client_socket.send(amount_.encode())
            client_socket.send(action_.encode())
        else:
            client_socket.send('request not approved'.encode())


def findEntry_bytype():  # in dev!!!
    global Accounts
    global Ledgers
    tempAmount = 0
    ac = client_socket.recv(1024).decode()
    counter = 0
    ledger_ = 0
    for i in range(Accounts.size):
        if Accounts[i].name == ac:
            ledger_ = i - 1
            break
        else:
            counter = counter + 1
    if counter == Accounts.size:
        client_socket.send('request not approved'.encode())
    else:
        client_socket.send('all good'.encode())
        verify = verification(Accounts[ledger_])
        if verify:
            client_socket.send('yes'.encode())
            action = client_socket.recv(1024).decode()
            for i in Ledgers[ledger_].array:
                if i.action == action:
                    tempAmount = i.value
                client_socket.send(str(tempAmount).encode())
            client_socket.send('done'.encode())
        else:
            client_socket.send('request not approved'.encode())


def findBusinessEntry():
    global BusinessAccounts
    global BusinessLedgers
    ac = client_socket.recv(1024).decode()
    counter = 0
    ledger_ = 0
    for i in range(BusinessAccounts.size):
        if BusinessAccounts[i].companyName == ac:
            ledger_ = i
            break
        else:
            counter = counter + 1
    if BusinessAccounts.size == counter:
        client_socket.send('request not approved'.encode())
    else:
        client_socket.send('all good'.encode())
        verify, target = businessVerification(BusinessAccounts[ledger_])
        if verify:
            client_socket.send('yes'.encode())
            index = int(client_socket.recv(1024).decode()) - 1
            amount_ = str(BusinessLedgers[ledger_].departmentsArray[target].array[index].amount)
            action_ = str(BusinessLedgers[ledger_].departmentsArray[target].array[index].action)
            department_ = str(BusinessLedgers[ledger_].departmentsArray[target].array[index].department)
            client_socket.send(amount_.encode())
            client_socket.send(action_.encode())
            client_socket.send(department_.encode())
        else:
            client_socket.send('request not approved'.encode())


def findIndex(Array, Element):
    elementSearch = globals()[Element]
    return np.where(Array == elementSearch)


def createTempo():  # in dev!!!
    temp = tempo(0, 0)
    return temp


def createBusinessAccount(name, newLedger):
    confirm = True
    counter = 0
    for i in range(BusinessAccounts.size):
        if BusinessAccounts[i].companyName == name:
            confirm = False
            break
    while confirm == False: # change loop, receive new input each time
        counter = 0
        for i in range(BusinessAccounts.size):
            if BusinessAccounts[i].companyName == name:
                break
            else:
                counter = counter + 1
        if counter == BusinessAccounts.size:
            confirm = True
    temp = str(name)
    name = BusinessAccount(0, "none", np.array([]))
    name.companyName = client_socket.recv(1024).decode()
    name.code = int(client_socket.recv(1024).decode())
    newLedger = businessLedger(np.array([]))
    depNum = int(client_socket.recv(1024).decode())
    for i in range(depNum):
        newLedger.departmentsArray = np.append(newLedger.departmentsArray, [Ledger(np.array([]))])
    for i in range(depNum):
        depCode = int(client_socket.recv(1024).decode())
        name.departmentsArray = np.append(name.departmentsArray, [Account(0, depCode, ('dep_' + str(i)))])
    return name, newLedger


def create_account(name):  # updated
    global Accounts
    global Ledgers
    confirm = False
    while not confirm:
        if accountName_table.in_table(name) != -1:
            send_message(client_socket, 'password exists, please try again.')
            name = recv_message(client_socket, 'str')
        else:
            confirm = True
            accountName_table.add_value(name)
    confirm = False
    code = recv_message(client_socket, 'int')
    while not confirm:
        if password_table.in_table(code) != -1:
            send_message(client_socket, 'password exists, please try again.')
            code = recv_message(client_socket, 'int')
        else:
            confirm = True
            password_table.add_value(code)
    nameAccount = Account2(0, '')
    nameAccount.code = code
    nameAccount.name = name
    new_array = np.array([])
    new_ledger = Ledger(new_array)
    nameL = name + "_L"
    globals()[name], globals()[nameL] = nameAccount, new_ledger
    Accounts = np.append(Accounts, globals()[name])
    Ledgers = np.append(Ledgers, globals()[nameL])


def createSavingsA(name, newLedger):
    returns = int(client_socket.recv(1024).decode())
    confirm = True
    counter = 0
    for i in range(S_Accounts.size):
        if S_Accounts[i].name == name:
            confirm = False
            break
    while confirm == False: # change loop, receive new input each time
        counter = 0
        for i in range(S_Accounts.size):
            if S_Accounts[i].name == name:
                break
            else:
                counter = counter + 1
        if counter == S_Accounts.size:
            confirm = True
    temp_code = int(client_socket.recv(1024).decode())
    nameAccount = SavingsAccount(0, temp_code, '', returns)
    nameAccount.name = name
    newArray = np.array([])
    newLedger = Ledger(newArray)
    return nameAccount, newLedger


def accountSummary(ac_index, led_index):
    global Accounts
    global Ledgers
    deposited = 0
    withdrawn = 0
    transactions = 0
    cloudTransactions = 0
    verify = verification(Accounts[ac_index])
    if verify:
        for i in range(len(Ledgers[led_index].array)):
            if Ledgers[led_index].array[i].action == "d":
                deposited = deposited + Ledgers[led_index].array[i].amount
            elif Ledgers[led_index].array[i].action == "w":
                withdrawn = withdrawn + Ledgers[led_index].array[i].amount
            elif Ledgers[led_index].array[i].action == "tAway":
                transactions = transactions - Ledgers[led_index].array[i].amount
            elif Ledgers[led_index].array[i].action == "tTo":  # add later - transfer to self
                transactions = transactions + Ledgers[led_index].array[i].amount
            elif Ledgers[led_index].array[i].action == "toCloud":
                cloudTransactions = cloudTransactions - Ledgers[led_index].array[i].amount
            elif Ledgers[led_index].array[i].action == "fromCloud":
                cloudTransactions = cloudTransactions + Ledgers[led_index].array[i].amount
        client_socket.send('request approved'.encode())
        client_socket.send(str(deposited).encode())
        client_socket.send(str(withdrawn).encode())
        client_socket.send(str(transactions).encode())
        client_socket.send(str(Accounts[ac_index].value).encode())
    else:
        client_socket.send('request not approved'.encode())


def binary_digit_sum(num):
    bin_sum = 0
    while num >= 1:
        bin_sum += num % 10
        num = int(num / 10)
    return bin_sum


# encryption to use for data storage
def encrypt(initial_num):  # max is 7 digits for correct decryption
    key = ()
    temp_in = initial_num
    digit_counter = 0
    current_digit = 0
    bin_num = 0
    binary_sum = ()
    temp_sum = 0
    current_bit = 0
    bin_current_loc = 0
    while initial_num >= 1:
        current_digit = initial_num % 10
        initial_num = int(initial_num / 10)
        bin_num = int((str(bin(current_digit))).replace("0b", ""))
        temp_sum = binary_digit_sum(bin_num)
        temp_tuple = (str(temp_sum),)
        binary_sum = binary_sum + temp_tuple
        digit_counter += 1
        bin_current_loc = 0
        while bin_num >= 1:
            bin_current_loc += 1
            current_bit = bin_num % 10
            bin_num = int(bin_num / 10)
            if current_bit == 1:
                temp_tuple = (str(bin_current_loc),)
                key = key + temp_tuple
    initial_num = temp_in
    key = "".join(key)
    key = int(key)
    binary_sum = "".join(binary_sum)
    binary_sum = int(binary_sum)
    return digit_counter, binary_sum, key


def decrypt(a, b, c):  # max is 7 digits for correct decryption
    binary_numbers = np.array([])
    current_counter = 0
    key_pos = 0
    current_number = -1
    num = 0
    while b >= 1:
        current_number += 1
        current_counter = b % 10
        b = int(b / 10)
        for i in range(current_counter):
            key_pos = c % 10
            c = int(c / 10)
            num += (10 ** (key_pos - 1))
        binary_numbers = np.append(binary_numbers, num)
        num = 0
    binary_numbers = binary_numbers.astype(int)
    for i in range(binary_numbers.size):
        binary_numbers[i] = int(str(binary_numbers[i]), 2)
    decrypted_num = 0
    binary_numbers = np.flipud(binary_numbers)
    check = 0
    for i in range(binary_numbers.size):
        decrypted_num += binary_numbers[i] * (10 ** i)
        check += 1
    if a != check:
        a = a - check
        while a > 0:
            decrypted_num *= 10
            a -= 1
    return decrypted_num


# Additional setup:
tempoCloud = createTempo()
value = int(client_socket.recv(1024).decode())
if value == '':
    value = 0
cashAccount = Account(value, 0000, 'cash')
Accounts = np.append(Accounts, [cashAccount])
amount_temp = 0
account_name = ''
account2_name = ''
password_table = HashTable()
accountName_table = HashTable()

while True:
    request = client_socket.recv(1024).decode()

    if request[0] == 'c':

        if request == 'ca':
            name = str(client_socket.recv(1024).decode())
            nameL = str(client_socket.recv(1024).decode())
            create_account(name)
            print('Account created -', name)

        if request == 'cba':
            Bname = str(client_socket.recv(1024).decode())
            BnameL = str(client_socket.recv(1024).decode())
            globals()[Bname], globals()[BnameL] = createBusinessAccount(Bname, BnameL)
            BusinessAccounts = np.append(BusinessAccounts, globals()[Bname])
            BusinessLedgers = np.append(BusinessLedgers, globals()[BnameL])
            print('Business account created -', Bname)

    if request[0] == 'm':

        if request == 'mt_bus2reg':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].businessName == ac:
                    BusinessAccounts[i].outerTransfer_bus2reg(BusinessLedgers[i], Ledgers)
                    break
                else:
                    counter = counter + 1
            if BusinessAccounts.size == counter:
                client_socket.send('request not approved'.encode())

        if request == 'mas':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(Accounts.size):
                if Accounts[i].name == ac:
                    accountSummary(i, i - 1)
                    break
                else:
                    counter = counter + 1
            if counter == Accounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'md':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(Accounts.size):
                if Accounts[i].name == ac:
                    Accounts[i].deposit(cashAccount, Ledgers[i - 1])
                    print('deposit to account -', ac)
                    break
                else:
                    counter = counter + 1
            if counter == Accounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mw':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(Accounts.size):
                if Accounts[i].name == ac:
                    Accounts[i].withdraw(cashAccount, Ledgers[i - 1])
                    print('withdraw from account -', ac)
                    break
                else:
                    counter = counter + 1
            if counter == Accounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mt':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(Accounts.size):
                if Accounts[i].name == ac:
                    Accounts[i].transferFrom(Ledgers[i - 1], Ledgers)
                    print('transfer from account -', ac)
                    break
                else:
                    counter = counter + 1
            if counter == Accounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mcb':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(Accounts.size):
                if Accounts[i].name == ac:
                    Accounts[i].checkBalance()
                    break
                else:
                    counter = counter + 1
            if counter == Accounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mdb':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].companyName == ac:
                    BusinessAccounts[i].deposit(cashAccount, BusinessLedgers[i])
                    print('deposit to business account -', ac)
                    break
                else:
                    counter = counter + 1
            if counter == BusinessAccounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mwb':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].companyName == ac:
                    BusinessAccounts[i].withdraw(cashAccount, BusinessLedgers[i])
                    print('withdraw from business account -', ac)
                    break
                else:
                    counter = counter + 1
            if counter == BusinessAccounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mitb':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].companyName == ac:
                    BusinessAccounts[i].departmentalTransfer(BusinessLedgers[i])
                    print('inner transfer in business account -', ac)
                    break
                else:
                    counter = counter + 1
            if counter == BusinessAccounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mtb':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].companyName == ac:
                    BusinessAccounts[i].outerTransfer(BusinessLedgers[i])
                    print('transfer from business account -', ac)
                    break
                else:
                    counter = counter + 1
            if counter == BusinessAccounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mcbb':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(BusinessAccounts.size):
                if BusinessAccounts[i].companyName == ac:
                    BusinessAccounts[i].checkBalance()
                    break
                else:
                    counter = counter + 1
            if counter == BusinessAccounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'mt_reg2bus':
            counter = 0
            ac = client_socket.recv(1024).decode()
            for i in range(Accounts.size):
                if Accounts[i].name == ac:
                    Accounts[i].transferFrom_reg2bus(Ledgers[i - 1], BusinessLedgers)
                    break
                else:
                    counter = counter + 1
            if counter == Accounts.size:
                client_socket.send('request not approved'.encode())

        if request == 'maf':  # in dev!!
            tempoCloud.receive()

        if request == 'mrf':  # in dev!!
            tempoCloud.allocate()

        if request == 'mac':  # in dev!!
            tempoCloud.checkValue()

        if request[0] == 'f':

            if request == 'fe':
                findEntry()

            if request == 'fbe':
                findBusinessEntry()

            if request == 'febt':
                findEntry_bytype()