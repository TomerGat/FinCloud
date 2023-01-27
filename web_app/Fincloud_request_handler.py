# import general systems
from Fincloud_general_systems import *


# HTTP request handler for HTTP server
class FinCloudHTTPRequestHandler(BaseHTTPRequestHandler):

    def clear(self):
        output = '<html><body>'
        output += '<script type="text/javascript">document.body.innerHTML = ""</script>'
        output += '</body></html>'
        self.wfile.write(output.encode())

    def start(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()

    def redirect(self, path):
        self.send_response(301)
        self.send_header('content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def system_error(self):  # redirect to main page, set redirect flag to true, set response code to -1 to display error
        if self.client_address[0] in data.current_account.keys():
            data.delete_ca(self.client_address[0])
        data.alter_rf(self.client_address[0], True)
        data.alter_re(self.client_address[0], Responses.SYSTEM_ERROR)
        self.redirect('/')

    def timeout_session(self):
        if self.client_address[0] in data.current_account.keys():
            data.delete_ca(self.client_address[0])
        data.alter_rf(self.client_address[0], True)
        data.alter_re(self.client_address[0], Responses.SESSION_TIMEOUT)
        data.alter_brf(self.client_address[0], False)
        self.redirect('/')

    def do_GET(self):  # GET handling function

        # if client address does not have a redirect flag set (first connections), initialize flag to false
        if self.client_address[0] not in data.redirect_flags.keys():
            data.alter_rf(self.client_address[0], False)

        # if client address not in history (first connection), add the address
        if self.client_address[0] not in history.keys():
            history[self.client_address[0]] = Log()

        # add request to history
        history[self.client_address[0]].append(ConnectionEntry('get', get_precise_time()))

        # if address not in background redirect flags, initialize flag to false
        if self.client_address[0] not in data.background_redirect_flags.keys():
            data.alter_brf(self.client_address[0], False)

        # wait before checking background redirect flag
        time.sleep(REQUEST_WAIT)

        # check background redirect flag
        if data.background_redirect_flags[self.client_address[0]]:
            self.timeout_session()

        # if address not yet in addresses (first connection/session time out), add to addresses list
        if self.client_address[0] not in addresses:
            addresses.append(self.client_address[0])

        # handle get requests according to path
        if self.path.endswith('/'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<head><title>FinCloud.com</title></head>'
            output += '<h1>FinCloud - A modern solution for you</h1>'
            output += '<h3><a href="/About">Learn about us</a></h3>'
            output += '<h3><a href="/login">Sign in</a></h3>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.redirect_flags[self.client_address[0]] = False
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.SYSTEM_ERROR:
                    output += '<h4>System error. Please try again later.</h4>'
                if response_code == Responses.SESSION_TIMEOUT:
                    output += '<h4>Session timed out.</h4>'
                data.alter_re(self.client_address[0], 0)
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/About'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>What is FinCloud?</h1>'
            output += 'Fincloud is a state of the art financial network...'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/login'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Log in   |   Continue to FinCloud</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/login">'
            output += 'Account name/number: ' + '<input name="username" type="text">' + '</br>'
            output += 'Account access Code: ' + '<input name="code" type="text">' + '</br>' + '</br>'
            output += '<input type="submit" value="Login">'
            output += '</form>'
            temp = '<p style = "color: black" style = "text-decoration: none">Forgot your password?</p>'
            output += '<h5><a href="/forgot">' + temp + '</a></h5>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.AC_IDENTITY_INCORRECT:
                    output += '<h4>Account name/number is incorrect. Please try again.</h4>'
                elif response_code == Responses.AC_CODE_INCORRECT:
                    output += '<h4>Password is incorrect. Please try again.</h4>'
                elif response_code == Responses.PROCESSING_ERROR:
                    output += '<h4>Processing error. Please try again at a later time.</h4>'
                elif response_code == Responses.ACCOUNT_RECOVERY_CONFIRM:
                    output += '<h4>Account recovered. Password reset.</h4>'
                elif response_code == Responses.NEW_ACCOUNT_CREATED:
                    output += '<h4>New account created.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '________      or      ________' + '</br></br></br>'
            output += 'New to FinCloud? ' + '<a href="/new">Get started</a></br></br></br>'
            output += 'Return to home page ' + '<a href="/">Here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/logout'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            output += '<h1>Your Account: ' + account_name + '</h1>'
            output += '<h2><Are you sure you want to log out of your account?</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/logout">'
            output += '<input type="submit" value="Confirm">' + '</form>'
            output += '<h4><a href="/account/home">Cancel logout</a></h4>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/forgot'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Recover your account</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/forgot">'
            output += 'Enter your account name/number: ' + '<input name="user" type="text">' + '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your new account password: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.PHONE_NUM_NOT_FOUND:
                    output += '<h4>Phone number does not exist in out system.</h4>'
                elif response_code == -Responses.AC_IDENTITY_INCORRECT:
                    output += '<h4>Account name/number incorrect.</h4>'
                elif response_code == Responses.CODES_NOT_MATCH:
                    output += '<h4>Codes do not match</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>'
            output += '<h4><a href="/login">Return to log in page</a></h4>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open an account</h1>'
            output += '<h3>Select an account that fits your needs</h3>'
            output += 'From personal accounts to specialized accounts for business, ' \
                      'FinCloud offers the best service you can find.' + '</br>' + '</br>'
            output += '<h2>Select the best account for you</h2>'
            output += '<h4><a href="/new/business">Specialized Business Account</a></h4>'
            output += 'Specialized accounts that allow simple and effective' \
                      ' management of funds throughout multiple departments'
            output += '<h4><a href="/new/checking">Personal Checking Account</a></h4>'
            output += 'Personal accounts that allow for dynamic management of personal funds.' \
                      ' Our personal accounts also offer users the option to distribute' \
                      ' their capital and purchase multiple currencies.'
            output += '<h4><a href="/new/savings">Personal Savings Account</a></h4>'
            output += 'Personal accounts that support savings at an interest determined by you.'
            output += '</br>' + '</br>' + '</br>' + '</br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new/checking'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open a personal checking account</h1>'
            output += 'Personal checking accounts allow for dynamic management of personal funds.' \
                      ' Our personal accounts also offer you the option to distribute' \
                      ' your capital and purchase multiple currencies.'
            output += '</br>' + '</br>'
            output += '<h2>Create Your Account</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/new/checking">'
            output += 'Enter a name for your account: ' + '<input name="user" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter a password for your account: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.AC_NAME_INVALID:
                    output += '<h4>Account name is invalid. Please try again.</h4>'
                elif response_code == Responses.AC_CODE_INVALID:
                    output += '<h4>Account code is invalid: do not use symbols. Please try again.</h4>'
                elif response_code == Responses.NAME_AND_CODE_INVALID:
                    output += '<h4>Account name and code are invalid: do not use symbols.' \
                              ' Please try again.</h4>'
                elif response_code == Responses.AC_NAME_EXISTS:
                    output += '<h4>An account with this name already exists. Please try again.</h4>'
                elif response_code == Responses.PHONE_NUM_INVALID:
                    output += '<h4>Phone number not valid.</h4>'
                elif response_code == Responses.PHONE_NUM_EXISTS:
                    output += '<h4>Phone number already registered to an existing account.</h4>'
                elif response_code == Responses.CODES_NOT_MATCH:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new/savings'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open a personal savings account</h1>'
            output += 'Personal savings accounts allow for safe and profitable storage for your savings.' \
                      ' Our personal savings accounts provide preset annual returns guaranteed and backed by our funds.'
            output += '<h4>Options for account returns:</h4>'
            output += 'Premium: 4% annual returns, $100 monthly fee' + '</br>'
            output += 'Regular: 2.75% annual returns, $80 monthly fee' + '</br>'
            output += 'Safe: 2% annual returns, $50 monthly fee' + '</br>'
            output += '</br></br></br>'
            output += '<h2>Create Your Account</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/new/savings">'
            output += 'Enter a name for your account: ' + '<input name="user" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter a password for your account: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += 'Select preferred returns for your savings account: '
            output += '<select id="returns" name="returns">'
            output += '<option value = "premium">Premium - 4% annually</option>'
            output += '<option value = "medium">Regular - 2.75% annually</option>'
            output += '<option value = "minimum">Safe - 2% annually</option>'
            output += '</select>'
            output += '</br></br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.AC_NAME_INVALID:
                    output += '<h4>Account name is invalid. Please try again.</h4>'
                elif response_code == Responses.AC_CODE_INVALID:
                    output += '<h4>Account code is invalid: do not use symbols. Please try again.</h4>'
                elif response_code == Responses.NAME_AND_CODE_INVALID:
                    output += '<h4>Account name and code are invalid: do not use symbols.' \
                              ' Please try again.</h4>'
                elif response_code == Responses.AC_NAME_EXISTS:
                    output += '<h4>An account with this name already exists. Please try again.</h4>'
                elif response_code == Responses.PHONE_NUM_INVALID:
                    output += '<h4>Phone number not valid.</h4>'
                elif response_code == Responses.PHONE_NUM_EXISTS:
                    output += '<h4>Phone number already registered to an existing account.</h4>'
                elif response_code == Responses.CODES_NOT_MATCH:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                elif response_code == Responses.INVALID_SAVING_RETURNS:
                    output += '<h4>Returns are invalid for this type of account.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new/business'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Open a business account</h1>'
            output += 'Business accounts allow for optimal and dynamic management of company resources.' \
                      'Our business account offer distribution of funds throughout company departments, ' \
                      'while also offering the option to invest company capital in international currencies.'
            output += '</br>' + '</br>'
            output += '<h2>Create Your Account</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/new/business">'
            output += 'Enter the name of the company: ' + '<input name="comp_name" type="text">' + '</br></br>'
            output += 'Enter a name for your account: ' + '<input name="user" type="text">' + '</br></br>'
            output += 'Enter a password for your account: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br></br>'
            output += 'After opening the account, you will have the option to open departments and ' \
                      'distribute company funds' + '</br></br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br>'

            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.AC_NAME_INVALID:
                    output += '<h4>Account name is invalid. Please try again.</h4>'
                elif response_code == Responses.AC_CODE_INVALID:
                    output += '<h4>Account code is invalid. Please try again.</h4>'
                elif response_code == Responses.COMP_NAME_INVALID:
                    output += '<h4>Company name is invalid. Please try again.</h4>'
                elif response_code == Responses.NAME_AND_CODE_INVALID:
                    output += '<h4>Account name and code are invalid. Please try again.</h4>'
                elif response_code == Responses.NAME_AND_COMP_INVALID:
                    output += '<h4>Account name and company name are invalid. Please try again.</h4>'
                elif response_code == Responses.CODE_AND_COMP_INVALID:
                    output += '<h4>Account code and company name are invalid. Please try again.</h4>'
                elif response_code == Responses.DATA_INVALID:
                    output += '<h4>Invalid data (account name, account code, company name). Please try again.</h4>'
                elif response_code == Responses.PHONE_NUM_INVALID:
                    output += '<h4>Phone number is invalid. Please try again.</h4>'
                elif response_code == Responses.PHONE_NUM_EXISTS:
                    output += '<h4>Phone number already registered to an existing account.</h4>'
                elif response_code == Responses.AC_NAME_EXISTS:
                    output += '<h4>Account name already registered to an existing account.</h4>'
                elif response_code == Responses.CODES_NOT_MATCH:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/admin_access/' + str(data.admin_token)):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<a href="/admin_access/' + str(data.admin_token) + '/account_list">Accounts list</a></br></br>'
            output += '<a href="/admin_access/' + str(data.admin_token) + '/cloud_watch">Cloud allocations</a></br></br>'
            output += '<a href="/account/logout">Log out</a>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/admin_access/' + str(data.admin_token) + '/account_list'):
            self.start()
            self.clear()
            output = '<table>' + '<tr>'
            output += '<th>Index</th>' + '<th> | Account name</th>' + '<th> | Account number</th>' + '<th> | Account type</th>' + '<th> | Total account value in USD</th>' + '</tr>'
            for i in range(len(Accounts.log)):
                output += '<tr><td> | ' + str(i) + '</td>'
                output += '<td> | <a href="/admin_access/account_list/' + name_table.get_key(i) + '/' + str(data.admin_token) + '/account_watch/details">' + name_table.get_key(i) + '</a></td>'
                output += '<td> | ' + str(number_table.get_key(i)) + '</td>'
                output += '<td> | ' + loc_type_table.in_table(i) + '</td>'
                output += '<td> | ' + Accounts.log[i].get_value_usd() + '</td></tr>'
            output += '</table>'
            self.wfile.write(output.encode())

        elif self.path.endswith(str(data.admin_token) + '/account_watch/details'):
            pass

        elif self.path.endswith('/admin_access/' + str(data.admin_token) + '/cloud_watch'):
            pass

        elif self.path.endswith('/account/home'):
            if name_table.get_key(data.current_account[self.client_address[0]]) == 'Admin':
                data.admin_token = hash_function(generate_code())
                self.redirect('/admin_access/' + str(data.admin_token))
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            account_number = str(number_table.get_key(ac_index))
            output += '<h1>Account name: ' + account_name + '</h1>'
            output += '<h2>Account number: ' + account_number + '</h2>'
            val = Accounts.log[ac_index].get_value_usd()
            if loc_type_table.body[ac_index] == 'bus':
                comp_name = str(Accounts.log[ac_index].company_name)
                output += '<h2>Company name: ' + comp_name + '</h2>'
            output += '</br><h2>Current value in USD: ' + val + '</h2>'
            if loc_type_table.body[ac_index] == 'reg':
                output += '<h3>See current holdings ' + '<a href="/account/holdings">Here</a></h3>'
            elif loc_type_table.body[ac_index] == 'bus':
                output += '<h3>See company departments ' + '<a href="/account/business/departments">Here</a></h3>'
            if loc_type_table.body[ac_index] == 'bus':
                output += '</br>'
                output += '<h3>Open a new department for your business account ' + \
                          '<a href="/account/business/open_dep">now</a></h3>'
            output += '</br>' + '</br>'

            output += '<h3>To deposit funds ' + '<a href="/account/deposit_funds">Click here</a></h3>'
            output += '<h3>To withdraw funds ' + '<a href="/account/withdraw_funds">Click here</a></h3>'
            output += '<h3>To transfer funds to other accounts ' + \
                      '<a href="/account/transfer_funds">Click here</a></h3>'
            if loc_type_table.body[ac_index] == 'bus':
                output += '</br>'
                output += '<h3><a href="/account/business/inner_transfer">Transfer between business departments</a></h3>'
            output += '</br>'
            output += '<h3>To use Financial Cloud ' + '<a href="/account/cloud">Click here</a></h3>'
            output += '</br>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.DEPOSIT_CONFIRM:
                    output += '<h4>Deposit confirmed.</h4>'
                elif response_code == Responses.WITHDRAWAL_CONFIRM:
                    output += '<h4>Withdrawal confirmed.</h4>'
                elif response_code == Responses.TRANSFER_CONFIRM:
                    output += '<h4>Transfer confirmed.</h4>'
                elif response_code == Responses.INNER_TRANSFER_CONFIRM:
                    output += '<h4>Departmental transfer processed.</h4>'
                elif response_code == Responses.NEW_DEP_OPENED:
                    output += '<h4>New department established.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br></br>' + '<h4><a href="/account/logout">Log out</a></h4>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/deposit_funds'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output += '<h1>Deposit Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/deposit_funds">'
            output += 'Enter amount to deposit: ' + '<input name="amount" type="text">' + '</br></br>'
            if loc_type_table.body[ac_index] == 'bus':
                output += 'Enter department to deposit to: ' + '<input name="dep_name" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.DEP_NOT_FOUND:
                    output += '<h4>Department name not found</h4>'
                data.alter_re(self.client_address[0], False)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/withdraw_funds'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output += '<h1>Withdraw Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/withdraw_funds">'
            output += 'Enter amount to withdraw: ' + '<input name="amount" type="text">' + '</br></br>'
            if loc_type_table.body[ac_index] == 'bus':
                output += 'Enter department to withdraw from: ' + '<input name="dep_name" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.INSUFFICIENT_AMOUNT:
                    output += '<h4>Account value in USD is insufficient for this withdrawal.</h4>'
                elif response_code == Responses.DEP_NOT_FOUND:
                    output += '<h4>Department name not found</h4>'
                data.alter_re(self.client_address[0], False)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/transfer_funds'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.body[ac_index]
            output = '<html><body>'
            output += '<h1>Transfer Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/transfer_funds">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Enter name/number of account to transfer to: ' + '<input name="target" type="text">' + '</br>'
            output += 'If you are transferring to a business account, enter name of department to transfer to: ' + \
                      '<input name="target_dep" type="text">' + '</br>'
            if ac_type == 'bus':
                output += '</br>' + 'Enter name of department to transfer from: ' + \
                          '<input name="source_dep" type="text">' + '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.TARGET_AC_NOT_FOUND:
                    output += '<h4>Target account not found.</h4>'
                elif response_code == Responses.INSUFFICIENT_AMOUNT:
                    output += '<h4>Account value in USD is insufficient for this transfer.</h4>'
                elif response_code == Responses.TARGET_DEP_WRONGLY_SET:
                    output += '<h4>Target department set although target account is not a business account.</h4>'
                elif response_code == Responses.TARGET_DEP_NOT_FOUND:
                    output += '<h4>Target department not found.</h4>'
                elif response_code == Responses.TARGET_DEP_WRONGLY_UNSET:
                    output += '<h4>Target department not set although target account is a business account.</h4>'
                elif response_code == Responses.SOURCE_DEP_NOT_FOUND:
                    output += '<h4>Source department not found.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/holdings'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            output = '<html><body>'
            output += '<h1>Account Holdings</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h2>Current currency holdings:</h2>'

            value_table = Accounts.log[ac_index].value
            output += create_table_output(value_table)

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.CURRENCY_TRADE_CONFIRM:
                    output += '<h4>Currency trade confirmed.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br></br>' + 'To trade and invest in different currencies ' + \
                      '<a href="/account/holdings/trade_currency">Click here</a>' + '</br></br>'
            output += 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/business/departments'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            comp_name = Accounts.log[ac_index].company_name
            output = '<html><body>'
            output += '<h1>Business Departments</h1>' + '</br>'
            output += '<h2>Company: ' + comp_name + '</h2>'
            output += '<h2>Account name: ' + account_name + '</h2>' + '</br></br>'
            output += '<h1>Company Departments and holdings: </h1>'
            if len(Accounts.log[ac_index].departments.keys()) == 0:
                output += '<h3>Account has no departments.</h3></br></br>'
            for dep in Accounts.log[ac_index].departments.keys():
                output += '</br><h2>Holdings for department "' + dep + '":</h2>'
                output += create_table_output(Accounts.log[ac_index].departments[dep][0]) + '</br>'
                output += 'Trade currencies with ' + dep + ' department capital: ' + \
                          '<a href="/account/business/departments/' + dep + '/invest_capital/trade_currencies">Here</a></br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.CURRENCY_TRADE_CONFIRM:
                    output += '<h4>Currency trade confirmed.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/holdings/trade_currency'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            value_table = Accounts.log[ac_index].value
            available_currencies = [currency for currency in value_table.keys() if value_table[currency] > 0]
            output = '<html><body>'
            output += '<h1>Currencies - Trade & Invest</h1>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += 'We offer you the opportunity to distribute and invest your account capital throughout' \
                      ' multiple international currencies. '
            output += 'Transfer funds between an array of currencies at market value without additional cost.' + '</br></br>'
            if len(available_currencies) == 0:
                output += '<h2>No funds available.</h2></br>'
            output += '<h2>Trade currencies:</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/holdings/trade_currency">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Select currency to transfer from: '
            output += '<select id="source_cur" name="source_cur">'
            for curr in available_currencies:
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br>'
            output += 'Select currency to transfer to: '
            output += '<select id="source_cur" name="target_cur">'
            for curr in value_table.keys():
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br></br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.INSUFFICIENT_AMOUNT:
                    output += '<h4>Insufficient funds in source currency.</h4>'
                elif response_code == Responses.SOURCE_CUR_NOT_FOUND:
                    output += '<h4>Source currency not found.</h4>'
                elif response_code == Responses.TARGET_CUR_NOT_FOUND:
                    output += '<h4>Target currency not found.</h4>'
                elif response_code == Responses.CURRENCIES_NOT_FOUND:
                    output += '<h4>Source and target currencies not found.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account holdings page ' + '<a href="/account/holdings">Click here</a>'
            output += '</br>' + '</br>' + 'Return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/invest_capital/trade_currencies'):
            self.start()
            self.clear()
            url_parsed = self.path.split('/')
            dep_name = url_parsed[4]
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            value_table = Accounts.log[ac_index].departments[dep_name][0]
            available_currencies = [currency for currency in value_table.keys() if value_table[currency] > 0]
            output = '<html><body>'
            output += '<h1>Currencies - Trade & Invest</h1>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h2>Department name: ' + dep_name + '</h2>'
            output += 'We offer you the opportunity to distribute and invest your account capital throughout' \
                      ' multiple international currencies. '
            output += 'Transfer funds between an array of currencies at market value without additional cost.' + '</br></br>'
            if len(available_currencies) == 0:
                output += '<h2>No funds available.</h2></br>'
            output += '<h2>Trade currencies:</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/business/departments/' + dep_name + '/invest_capital/trade_currencies">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Select currency to transfer from: '
            output += '<select id="source_cur" name="source_cur">'
            for curr in available_currencies:
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br>'
            output += 'Select currency to transfer to: '
            output += '<select id="source_cur" name="target_cur">'
            for curr in value_table.keys():
                output += '<option value = "' + curr + '">' + curr + '</option>'
            output += '</select></br></br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.INSUFFICIENT_AMOUNT:
                    output += '<h4>Insufficient funds in source currency.</h4>'
                elif response_code == Responses.SOURCE_CUR_NOT_FOUND:
                    output += '<h4>Source currency not found.</h4>'
                elif response_code == Responses.TARGET_CUR_NOT_FOUND:
                    output += '<h4>Target currency not found.</h4>'
                elif response_code == Responses.CURRENCIES_NOT_FOUND:
                    output += '<h4>Source and target currencies not found.</h4>'
                elif response_code == Responses.PROCESSING_ERROR:
                    output += '<h4>Processing error. Please try again later.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account holdings page ' + '<a href="/account/business/departments">Click here</a>'
            output += '</br>' + '</br>' + 'Return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/business/inner_transfer'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            account_number = str(number_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output = '<html><body>'
            output += '<h1>Departmental Transfer</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Account number: ' + account_number + '</h3>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/business/inner_transfer">'
            output += 'Enter amount to transfer: ' + '<input name="amount" type="text">' + '</br>'
            output += 'Enter name of department to transfer from: ' + '<input name="source_dep" type="text">' + '</br>'
            output += 'Enter name of department to transfer to: ' + '<input name="target_dep" type="text">' + '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.SOURCE_DEP_NOT_FOUND:
                    output += '<h4>Source department not found.</h4>'
                elif response_code == Responses.TARGET_DEP_NOT_FOUND:
                    output += '<h4>Target department not found.</h4>'
                elif response_code == Responses.INSUFFICIENT_AMOUNT:
                    output += '<h4>Department value in USD is insufficient for this transfer.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/cloud'):
            self.start()
            self.clear()
            output = '<html><body>'
            output += '<h1>Our Financial Cloud</h1>'
            output += '<h2>Why use Financial cloud?</h2>'
            output += 'Our Financial cloud offers allocation, management, and storage of funds in a secure and anonymous way.'
            output += '</br></br>'
            output += '<h3>Allocate funds <a href="/account/cloud/allocate">now</a></h3>'
            output += '<h3>Withdraw funds to your account <a href="/account/cloud/allocate">here</a></h3></br></br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.CLOUD_ALLOCATION_CONFIRM:
                    output += '<h4>Funds allocation confirmed.</h4>'
                elif response_code == Responses.CLOUD_WITHDRAWAL_CONFIRM:
                    output += '<h4>Funds withdrawal confirmed.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/cloud/allocate'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.body[ac_index]
            output = '<html><body>'
            output += '<h1>Allocate Funds With Fincloud</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/cloud/allocate">'
            output += 'Enter amount to allocate: ' + '<input name="amount" type="text">' + '</br>'
            if ac_type == 'bus':
                output += '</br>' + 'Enter name of department to allocate from: ' + '<input name="source_dep" type="text">' + '</br>'
            output += 'Enter allocation number (used to access funds): ' + '<input name="allocation_id" type="text">' + '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.ALLOCATION_ID_INVALID:
                    output += '<h4>Allocation ID is invalid.</h4>'
                elif response_code == Responses.INSUFFICIENT_AMOUNT:
                    output += '<h4>Insufficient funds in your account to complete allocation.</h4>'
                elif response_code == Responses.PROCESSING_ERROR:
                    output += '<h4>Processing error: account not found. Please try again later</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to Fincloud page ' + '<a href="/account/cloud">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/cloud/withdraw'):
            self.start()
            self.clear()
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.body[ac_index]
            output = '<html><body>'
            output += '<h1>Withdraw Funds From Fincloud</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/cloud/withdraw">'
            output += 'Enter amount to allocate: ' + '<input name="amount" type="text">' + '</br>'
            if ac_type == 'bus':
                output += '</br>' + 'Enter name of department to withdraw to: ' + '<input name="source_dep" type="text">' + '</br>'
            output += 'Enter allocation number to access funds: ' + '<input name="allocation_id" type="text">' + '</br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_TRANSACTION:
                    output += '<h4>Invalid transaction (null or negative values).</h4>'
                elif response_code == Responses.INVALID_INPUT_AMOUNT:
                    output += '<h4>Invalid input (amount).</h4>'
                elif response_code == Responses.ALLOCATION_ID_INVALID:
                    output += '<h4>Allocation ID is invalid.</h4>'
                elif response_code == Responses.INSUFFICIENT_AMOUNT:
                    output += '<h4>Insufficient funds allocated to complete transaction.</h4>'
                elif response_code == Responses.PROCESSING_ERROR:
                    output += '<h4>Processing error: account not found. Please try again later</h4>'
                elif response_code == Responses.ALLOCATION_NOT_FOUND:
                    output += '<h4>Allocation not found</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to Fincloud page ' + '<a href="/account/cloud">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/business/open_dep'):
            self.start()
            self.clear()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            output += '<h1>Your Account: ' + account_name + '</h1>'
            comp_name = str(Accounts.log[ac_index].company_name)
            output += '<h1>Company: ' + comp_name + '</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/business/open_dep">'
            output += 'Enter name for new department: ' + '<input name="new_dep" type="text">'
            output += '</br></br>'
            output += '<input type="submit" value="Open department">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.DEP_NAME_EXISTS:
                    output += '<h4>Department name already exists.</h4>'
                if response_code == Responses.DEP_NAME_INVALID:
                    output += '<h4>Department name invalid. Please try again.</h4>'
                data.alter_re(self.client_address[0], 0)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        else:
            self.system_error()

    def do_POST(self):  # POST handling function

        # check if address not in addresses list/history log (system error -> redirect to home page)
        if self.client_address[0] not in addresses or self.client_address[0] not in history.keys():
            self.system_error()

        # add request to history
        history[self.client_address[0]].append(ConnectionEntry('post', get_precise_time()))

        # wait before checking background redirect flag
        time.sleep(REQUEST_WAIT)

        # check background redirect flag
        if data.background_redirect_flags[self.client_address[0]]:
            self.timeout_session()

        # handle post requests according to path
        if self.path.endswith('/login'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                user_attempt = fields.get('username')[0]
                code_attempt = fields.get('code')[0]

                # verification process with input from user
                verify, response_code, index = verification(user_attempt, code_attempt)
                if verify:
                    data.alter_ca(self.client_address[0], index)
                    self.redirect('/account/home')
                else:
                    data.alter_re(self.client_address[0], response_code)
                    data.alter_rf(self.client_address[0], True)
                    self.redirect('/login')
            else:
                self.system_error()

        if self.path.endswith('/account/logout'):
            # logout page does not request input, any post request signals logging out of account
            data.delete_ca(self.client_address[0])
            self.redirect('/login')

        if self.path.endswith('/new/savings'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                phone_number = fields.get('phone')[0]
                code = fields.get('code')[0]
                code_confirm = fields.get('code_confirm')[0]
                account_name = fields.get('user')[0]
                returns_str = fields.get('returns')[0]
                returns_dict = {'premium': 4, 'medium': 2.75, 'safe': 2}  # to determine returns in numbers
                returns = returns_dict[returns_str]
                # create account with user input
                if code == code_confirm:
                    confirm, index, response_code = create_savings_account(account_name, code, phone_number, returns)
                    if confirm:
                        data.alter_re(self.client_address[0], Responses.NEW_ACCOUNT_CREATED)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/login')
                    else:
                        data.alter_re(self.client_address[0], response_code)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/new/savings')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                    self.redirect('/new/savings')
            else:
                self.system_error()

        if self.path.endswith('/new/business'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                phone_number = fields.get('phone')[0]
                code = fields.get('code')[0]
                code_confirm = fields.get('code_confirm')[0]
                account_name = fields.get('user')[0]
                company_name = fields.get('comp_name')[0]
                # create account with user input
                if code == code_confirm:
                    confirm, index, response_code = create_business_account(account_name, company_name, code, phone_number)
                    if confirm:
                        data.alter_re(self.client_address[0], Responses.NEW_ACCOUNT_CREATED)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/login')
                    else:
                        data.alter_re(self.client_address[0], response_code)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/new/business')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                    self.redirect('/new/business')
            else:
                self.system_error()

        if self.path.endswith('/new/checking'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                phone_number = fields.get('phone')[0]
                code = fields.get('code')[0]
                code_confirm = fields.get('code_confirm')[0]
                account_name = fields.get('user')[0]
                # create account with user input
                if code == code_confirm:
                    confirm, index, response_code = create_checking_account(account_name, code, phone_number)
                    if confirm:
                        data.alter_re(self.client_address[0], Responses.NEW_ACCOUNT_CREATED)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/login')
                    else:
                        data.alter_re(self.client_address[0], response_code)
                        data.alter_rf(self.client_address[0], True)
                        self.redirect('/new/checking')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                    self.redirect('/new/checking')
            else:
                self.system_error()

        if self.path.endswith('/forgot'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                phone_number = fields.get('phone')[0]
                new_code = fields.get('code')[0]
                code_confirm = fields.get('code_confirm')[0]
                user = fields.get('user')[0]

                # account code reset process with user input
                if new_code == code_confirm:
                    if (name_table.in_table(user) != -1) or (number_table.in_table(user) != -1):
                        if phone_name_table.in_table(hash_function(phone_number)) != -1:
                            account_name = phone_name_table.in_table(hash_function(phone_number))
                            account_loc = name_table.in_table(account_name)
                            pass_table.alter_key_index(account_loc, hash_function(new_code))

                            # redirect to login page and send approval
                            data.alter_rf(self.client_address[0], True)
                            data.alter_re(self.client_address[0], Responses.ACCOUNT_RECOVERY_CONFIRM)
                            self.redirect('/login')
                        else:
                            # redirect to forgot page and send error message (phone number does not exist in our system)
                            data.alter_rf(self.client_address[0], True)
                            data.alter_re(self.client_address[0], Responses.PHONE_NUM_NOT_FOUND)
                            self.redirect('/forgot')
                    else:
                        # redirect to forgot page and send error message (account name/number incorrect)
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], Responses.AC_IDENTITY_INCORRECT)
                        self.redirect('/forgot')
                else:
                    if not (name_table.in_table(user) != -1) and not (number_table.in_table(user) != -1):
                        # redirect to forgot page and send error message (account name/number incorrect)
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], Responses.AC_IDENTITY_INCORRECT)
                        self.redirect('/forgot')
                    else:
                        # redirect to forgot page send error message (codes do not match)
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                        self.redirect('/forgot')
            else:
                self.system_error()

        if self.path.endswith('/account/deposit_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                amount = fields.get('amount')[0]
                is_bus_account = False
                if loc_type_table.body[data.current_account[self.client_address[0]]] == 'bus':
                    is_bus_account = True
                index = data.current_account[self.client_address[0]]
                if not is_bus_account:
                    confirm, response_code = Accounts.log[index].deposit(amount)
                else:
                    confirm, response_code = Accounts.log[index].deposit(amount, fields.get('dep_name')[0])
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.DEPOSIT_CONFIRM)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/deposit_funds')
            else:
                self.system_error()

        if self.path.endswith('/account/withdraw_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                amount = fields.get('amount')[0]
                is_bus_account = False
                if loc_type_table.body[data.current_account[self.client_address[0]]] == 'bus':
                    is_bus_account = True
                ac_index = data.current_account[self.client_address[0]]
                if not is_bus_account:
                    confirm, response_code = Accounts.log[ac_index].withdraw(amount)
                else:
                    confirm, response_code = Accounts.log[ac_index].withdraw(amount, fields.get('dep_name')[0])
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.WITHDRAWAL_CONFIRM)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/withdraw_funds')
            else:
                self.system_error()

        if self.path.endswith('/account/transfer_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                is_bus_account = False
                target_account = fields.get('target')[0]
                target_dep = fields.get('target_dep')[0]
                amount = fields.get('amount')[0]
                if target_dep == "":
                    target_dep = "none"
                ac_index = data.current_account[self.client_address[0]]
                if loc_type_table.body[ac_index] == 'bus':
                    is_bus_account = True
                if not is_bus_account:
                    confirm, response_code = Accounts.log[ac_index].transfer(amount, target_account, target_dep)
                else:
                    confirm, response_code = \
                        Accounts.log[ac_index].transfer(amount, fields.get('source_dep')[0], target_account, target_dep)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.TRANSFER_CONFIRM)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/transfer_funds')
            else:
                self.system_error()

        if self.path.endswith('/account/business/inner_transfer'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                target_dep = fields.get('target_dep')[0]
                source_dep = fields.get('source_dep')[0]
                amount = fields.get('amount')[0]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].inner_transfer(source_dep, target_dep, amount)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.INNER_TRANSFER_CONFIRM)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/business/inner_transfer')
            else:
                self.system_error()

        if self.path.endswith('/account/business/open_dep'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                new_dep = fields.get('new_dep')[0]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].add_department(new_dep)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.NEW_DEP_OPENED)
                    self.redirect('/account/home')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/business/open_dep')
            else:
                self.system_error()

        if self.path.endswith('/account/holdings/trade_currency'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                source_cur = fields.get('source_cur')[0]
                target_cur = fields.get('target_cur')[0]
                amount = fields.get('amount')[0]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].trade_currency(amount, source_cur, target_cur)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CURRENCY_TRADE_CONFIRM)
                    self.redirect('/account/holdings')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/holdings/trade_currency')
            else:
                self.system_error()

        if self.path.endswith('/invest_capital/trade_currencies'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                source_cur = fields.get('source_cur')[0]
                target_cur = fields.get('target_cur')[0]
                amount = fields.get('amount')[0]
                url_parsed = self.path.split('/')
                dep_name = url_parsed[4]
                ac_index = data.current_account[self.client_address[0]]
                confirm, response_code = Accounts.log[ac_index].trade_currency(dep_name, source_cur, target_cur, amount)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CURRENCY_TRADE_CONFIRM)
                    self.redirect('/account/business/departments')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/business/departments/' + dep_name + '/invest_capital/trade_currencies')
            else:
                self.system_error()

        if self.path.endswith('/account/cloud/allocate'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                allocation_id = fields.get('allocation_id')[0]
                amount = fields.get('amount')[0]
                ac_index = data.current_account[self.client_address[0]]
                if loc_type_table.body[ac_index] == 'bus':
                    dep_name = fields.get('dep_name')[0]
                else:
                    dep_name = "none"
                confirm, response_code = Cloud().allocate(amount, allocation_id, name_table.get_key(ac_index), dep_name)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CLOUD_ALLOCATION_CONFIRM)
                    self.redirect('/account/cloud')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/cloud/allocate')
            else:
                self.system_error()

        if self.path.endswith('/account/cloud/withdraw'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                allocation_id = fields.get('allocation_id')[0]
                amount = fields.get('amount')[0]
                ac_index = data.current_account[self.client_address[0]]
                if loc_type_table.body[ac_index] == 'bus':
                    dep_name = fields.get('dep_name')[0]
                else:
                    dep_name = "none"
                confirm, response_code = Cloud().withdraw(amount, allocation_id, name_table.get_key(ac_index), dep_name)
                if confirm:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CLOUD_WITHDRAWAL_CONFIRM)
                    self.redirect('/account/cloud')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/cloud/withdraw')
            else:
                self.system_error()
