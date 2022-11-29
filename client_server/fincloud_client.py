# check that all requests use identical methods and variables
import socket

print("Fincloud is up and running")
ip = '127.0.0.1'
my_socket = socket.socket()
my_socket.connect((ip, 9876))
print("FinCloud is up and running")
cash = input("How much cash do you have in your personal bank? ")
my_socket.send(cash.encode())

while True:
    while True:
        input(' ')
        counter = 1
        request = input("Enter request (fund allocations/my account/create account/find entry): ")
        if request == 'fund allocations':
            request = input('Would you like to allocate funds, receive funds or check allocations? ')
        elif request == 'my account':
            temp = input("Is your account regular or business: ")
            request = input("Enter request (account summary/withdraw/deposit/transfer/check balance/inner transfer - only business accounts): ")
            if temp == 'business':
                request = str(request) + ' business'
                if request == 'transfer business':
                    ans = input('Would you like to transfer to a regular account or to a business account? ')
                    if ans == 'regular':
                        request = 'transfer_bus2reg'
            else:
                if request == 'transfer':
                    ans = input('Would you like to transfer to a regular account or to a business account?')
                    if ans == 'business':
                        request = 'transfer_reg2bus'
        elif request == 'create account':
            request = input("Do you want to create a regular account or a business account: ")
        elif request == 'find entry':
            request = input("Enter request (find entry/find business account entry): ")
            ans = input('Would you like to search for a specific entry or by type? ')
            if ans == 'by type':
                request = str(request) + ' by type'
        else:
            print("Request not valid. Please try again.")
            break

        if request == 'find entry by type':
            request = 'febt'
            my_socket.send(request.encode())
            ac = input('Enter account to access: ')
            my_socket.send(ac.encode())
            optionalStop = my_socket.recv(1024).decode()
            if optionalStop == 'all good':
                code_attempt = input('Enter code to access account ledger: ')
                my_socket.send(code_attempt.encode())
                optionalStop = my_socket.recv(1024).decode()
                if optionalStop == 'yes':
                    action = input('Enter action to search for (d/w/tTo/tAway/tTo_bus2reg/tAway_reg2bus/toCloud/fromCloud: ')
                    my_socket.send(action.encode())
                    tempAmount = my_socket.recv(1024).decode()
                    print('Entries - action =', action)
                    while tempAmount != 'done':
                        print(tempAmount)
                        tempAmount = my_socket.recv(1024).decode()
                    print('request complete')
            else:
                print('request not approved')

        elif request == 'check allocations':  # in dev!!
            request = 'mac'
            my_socket.send(request.encode())
            optionalStop = my_socket.recv(1024).decode()
            if optionalStop == 'noValue':
                print('No existing cloud allocations')
            else:
                allocationCode_attempt = input('Enter code to access tempo cloud: ')
                my_socket.send(allocationCode_attempt.encode())
                approval = my_socket.recv(1024).decode()
                if approval == 'all good':
                    alloValue = my_socket.recv(1024).decode()
                    print('Tempo Cloud has a remaining allocation of:', alloValue)
                else:
                    print(approval)

        elif request == 'allocate':  # in dev!!
            request = 'maf'
            my_socket.send(request.encode())
            ac = input('Enter account/business to access: ')
            my_socket.send(ac.encode())
            option = int(my_socket.recv(1024).decode())
            if option == 1:
                code_attempt = input('Enter code to access account: ')
                my_socket.send(code_attempt.encode())
                amount = input('Enter value of funds to allocate: ')
                my_socket.send(amount.encode())
                allocationCode = input('Enter allocation code: ')
                my_socket.send(allocationCode.encode())
                approval = my_socket.recv(1024).decode()
                print(approval)
            elif option == 2:
                code_attempt = input('Enter code to access business account: ')
                my_socket.send(code_attempt.encode())
                dep = input('Enter department to access: ')
                my_socket.send(dep.encode())
                depCode_attempt = input('Enter code to access department: ')
                my_socket.send(depCode_attempt.encode())
                amount = input('Enter value of funds to allocate: ')
                my_socket.send(amount.encode())
                allocationCode = input('Enter allocation code: ')
                my_socket.send(allocationCode.encode())
                approval = my_socket.recv(1024).decode()
                print(approval)
            else:
                approval = my_socket.recv(1024).decode()
                print(approval)

        elif request == 'receive':  # in dev!!
            request = 'mrf'
            my_socket.send(request.encode())
            ac = input('Enter account/business to access: ')
            my_socket.send(ac.encode())
            option = int(my_socket.recv(1024).decode())
            if option == 1:
                code_attempt = input('Enter code to access account: ')
                my_socket.send(code_attempt.encode())
                amount = input('Enter value of funds to receive: ')
                my_socket.send(amount.encode())
                allocationCode_attempt = input('Enter allocation code to receive funds: ')
                my_socket.send(allocationCode_attempt.encode())
                approval = my_socket.recv(1024).decode()
                if approval == 'cloud reset':
                    print('request approved, cloud reset')
                else:
                    print(approval)
            elif option == 2:
                code_attempt = input('Enter code to access business account: ')
                my_socket.send(code_attempt.encode())
                dep = input('Enter department to access: ')
                my_socket.send(dep.encode())
                depCode_attempt = input('Enter code to access department: ')
                my_socket.send(depCode_attempt.encode())
                amount = input('Enter value of funds to receive: ')
                my_socket.send(amount.encode())
                allocationCode_attempt = input('Enter allocation code to receive funds: ')
                my_socket.send(allocationCode_attempt.encode())
                approval = my_socket.recv(1024).decode()
                print(approval)
            else:
                approval = my_socket.recv(1024).decode()
                print(approval)

        elif request == 'transfer_reg2bus':  # in dev!!!!!
            request = 'mt_reg2bus'
            my_socket.send(request.encode())
            ac = input('Enter account to access: ')
            my_socket.send(ac.encode())
            code_attempt = input('Enter code to access account: ')
            my_socket.send(code_attempt.encode())
            amount = input('Enter amount to transfer: ')
            my_socket.send(amount.encode())
            businessName = input('Enter name of business to transfer to: ')
            my_socket.send(businessName.encode())
            ans = my_socket.recv(1024).decode()
            if ans == 'all good':
                target_dep = input('Enter number of department to transfer to: ')
                my_socket.send(target_dep.encode())
                approval = my_socket.recv(1024).decode()
                print(approval)
            else:
                print('request not approved')

        elif request == 'account summary':
            request = 'mas'
            my_socket.send(request.encode())
            ac = input("What account would you like to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access account: ")
            my_socket.send(code_attempt.encode())
            approval = my_socket.recv(1024).decode()
            if approval == 'request approved':
                deposits = my_socket.recv(1024).decode()
                withdrawals = my_socket.recv(1024).decode()
                transactions = my_socket.recv(1024).decode()
                currentValue = my_socket.recv(1024).decode()
                print('Account cashflow summary:')
                print('Deposits:', deposits)
                print('Withdrawals:', withdrawals)
                print('Transactions:', transactions)
                print('Current balance:', currentValue)
                print(' ')
            else:
                print('request not approved')
                print(' ')

        elif request == 'withdraw':
            request = 'mw'
            my_socket.send(request.encode())
            ac = input("What account would you like to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access account: ")
            my_socket.send(code_attempt.encode())
            amount = input("Enter amount to withdraw: ")
            my_socket.send(amount.encode())
            approval = my_socket.recv(1024).decode()
            print(approval)

        elif request == 'deposit':
            request = 'md'
            my_socket.send(request.encode())
            ac = input("What account would you like to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access account: ")
            my_socket.send(code_attempt.encode())
            amount = input("Enter amount to deposit: ")
            my_socket.send(amount.encode())
            approval = my_socket.recv(1024).decode()
            print(approval)

        elif request == 'transfer':
            request = 'mt'
            my_socket.send(request.encode())
            ac = input("What account would you like to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access account: ")
            my_socket.send(code_attempt.encode())
            amount = input("Enter amount to transfer: ")
            my_socket.send(amount.encode())
            transferTo = input("Enter account to transfer to: ")
            my_socket.send(transferTo.encode())
            approval = my_socket.recv(1024).decode()
            print(approval)

        elif request == 'check balance':
            request = 'mcb'
            my_socket.send(request.encode())
            ac = input("What account would you like to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access account: ")
            my_socket.send(code_attempt.encode())
            balance = my_socket.recv(1024).decode()
            if balance[0] == 'r':
                print(balance)
            else:
                print("Your account balance is: ", int(balance))

        elif request == 'withdraw business':
            request = 'mwb'
            my_socket.send(request.encode())
            ac = input("Enter name of business to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access business account: ")
            my_socket.send(code_attempt.encode())
            dep = input("Enter number of department to access: ")
            my_socket.send(dep.encode())
            depCode_attempt = input("Enter code to access department: ")
            my_socket.send(depCode_attempt.encode())
            amount = input("Enter amount to withdraw: ")
            my_socket.send(amount.encode())
            approval = my_socket.recv(1024).decode()
            print(approval)

        elif request == 'deposit business':
            request = 'mdb'
            my_socket.send(request.encode())
            ac = input("Enter name of business to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access business account: ")
            my_socket.send(code_attempt.encode())
            dep = input("Enter number of department to access: ")
            my_socket.send(dep.encode())
            depCode_attempt = input("Enter code to access department: ")
            my_socket.send(depCode_attempt.encode())
            amount = input("Enter amount to deposit: ")
            my_socket.send(amount.encode())
            approval = my_socket.recv(1024).decode()
            print(approval)

        if request == 'transfer_bus2reg':  # in dev!!!
            request = 'mt_bus2reg'
            my_socket.send(request.encode())
            ac = input('Enter business account to access: ')
            my_socket.send(ac.encode())
            code_attempt = input('Enter code to access business account:')
            my_socket.send(code_attempt.encode())
            dep = input("Enter number of department to access: ")
            my_socket.send(dep.encode())
            depCode_attempt = input("Enter code to access department: ")
            my_socket.send(depCode_attempt.encode())
            amount = input('Enter amount to transfer: ')
            my_socket.send(amount.encode())
            targetAC = input('Enter account to transfer to: ')
            my_socket.send(targetAC.encode())
            approval = my_socket.recv(1024).decode()
            if approval == 'all good':
                print('request approved')
            else:
                print('request not approved')

        elif request == 'transfer business':
            request = 'mtb'
            my_socket.send(request.encode())
            ac = input("Enter name of business to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access business account: ")
            my_socket.send(code_attempt.encode())
            dep = input("Enter number of department to access: ")
            my_socket.send(dep.encode())
            depCode_attempt = input("Enter code to access department: ")
            my_socket.send(depCode_attempt.encode())
            amount = input("Enter amount to transfer: ")
            my_socket.send(amount.encode())
            target = input("Enter name of business to transfer to: ")
            my_socket.send(target.encode())
            optionalStop = my_socket.recv(1024).decode()
            if optionalStop != 'no':
                target_dep = input("Enter number of department to transfer to: ")
                my_socket.send(target_dep.encode())
                approval = my_socket.recv(1024).decode()
                print(approval)
            else:
                approval = my_socket.recv(1024).decode()
                print(approval)

        elif request == 'check balance business':
            request = 'mcbb'
            my_socket.send(request.encode())
            ac = input("Enter account to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access account: ")
            my_socket.send(code_attempt.encode())
            dep = input("Enter department to access: ")
            my_socket.send(dep.encode())
            depCode_attempt = input("Enter code to access department: ")
            my_socket.send(depCode_attempt.encode())
            balance = my_socket.recv(1024).decode()
            if balance[0] == 'r':
                print(balance)
            else:
                print("Your account balance is: ", int(balance))

        elif request == 'inner transfer business':
            request = 'mitb'
            my_socket.send(request.encode())
            ac = input("Enter name of business to access: ")
            my_socket.send(ac.encode())
            code_attempt = input("Enter code to access business account: ")
            my_socket.send(code_attempt.encode())
            dep = input("Enter number of department to access: ")
            my_socket.send(dep.encode())
            depCode_attempt = input("Enter code to access department: ")
            my_socket.send(depCode_attempt.encode())
            amount = input("Enter amount to transfer: ")
            my_socket.send(amount.encode())
            target = input("Enter number of department to transfer to: ")
            my_socket.send(target.encode())
            approval = my_socket.recv(1024).decode()
            print(approval)

        elif request == 'regular account':
            request = 'ca'
            my_socket.send(request.encode())
            name = input("Enter name for account: ")
            nameL = input("Enter name for ledger: ")
            my_socket.send(name.encode())
            my_socket.send(nameL.encode())
            code = input("Enter code for account: ")
            my_socket.send(code.encode())
            print("Account saved")

        elif request == 'business account':
            request = 'cba'
            my_socket.send(request.encode())
            Bname = input("Enter name for account: ")
            BnameL = input("Enter name for ledger: ")
            my_socket.send(Bname.encode())
            my_socket.send(BnameL.encode())
            companyName = input("Enter the name of the company: ")
            my_socket.send(companyName.encode())
            code = input("Enter code for account: ")
            my_socket.send(code.encode())
            depNum = input("Enter number of departments: ")
            my_socket.send(depNum.encode())
            for i in range(int(depNum)):
                print("enter code for department", (i + 1), end=": ")
                depCode = input("")
                my_socket.send(depCode.encode())
            print("Business account saved")

        elif request == 'find entry':  # in dev!!
            request = 'fe'
            my_socket.send(request.encode())
            ac = input('Enter account to access: ')
            my_socket.send(ac.encode())
            ans = my_socket.recv(1024).decode()
            if ans == 'all good':
                code_attempt = input('Enter code to access account ledger: ')
                my_socket.send(code_attempt.encode())
                approval = my_socket.recv(1024).decode()
                if approval == 'yes':
                    entryNum = input('Entry entry to search for: ')
                    my_socket.send(entryNum.encode())
                    amount = my_socket.recv(1024).decode()
                    action = my_socket.recv(1024).decode()
                    print('The entry is a', action, '- amount =', amount)
                else:
                    print('request not approved')
            else:
                print('request not approved')

        elif request == 'find business account entry':  # in dev!!
            request = 'fbe'
            my_socket.send(request.encode())
            ac = input('Enter business account to access: ')
            my_socket.send(ac.encode())
            optionalStop = my_socket.recv(1024).decode()
            if optionalStop == 'all good':
                code_attempt = input('Enter code to access business ledger: ')
                my_socket.send(code_attempt.encode())
                dep = input('Enter department to access: ')
                my_socket.send(dep.encode())
                depCode_attempt = input('Enter code to access department ledger: ')
                my_socket.send(depCode_attempt.encode())
                approval = my_socket.recv(1024).decode()
                if approval == 'yes':
                    entryNum = input('Enter entry to search for: ')
                    my_socket.send(entryNum.encode())
                    amount = my_socket.recv(1024).decode()
                    action = my_socket.recv(1024).decode()
                    dep = my_socket.recv(1024).decode()
                    print('The entry is a', action, '- department =', dep, '- amount =', amount)
                else:
                    print('request not approved')
            else:
                print('request not approved')
