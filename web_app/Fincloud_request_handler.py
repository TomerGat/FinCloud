# import general systems
from Fincloud_general_systems import *


# HTTP request handler for HTTP server
class FinCloudHTTPRequestHandler(BaseHTTPRequestHandler):

    def start(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()

    def redirect(self, path):
        self.send_response(301)
        self.send_header('content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def system_error(
            self):  # redirect to main page, set redirect flag to true, set response code to -1 to display error
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

        # check if first action in history log is of post type (system error / attempt by user to exploit)
        if history[self.client_address[0]].log[0].lst[0] == 'post':
            self.system_error()

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

        # redirecting if new user or timed out user is trying to enter page that requires verification
        if self.path.split('/')[1] == 'account' and self.client_address[0] not in data.current_account.keys():
            self.timeout_session()

        # handle get requests according to path
        if self.path.endswith('/'):
            self.start()
            
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
            
            output = '<html><body>'
            output += '<h1>What is FinCloud?</h1>'
            output += 'FinCloud is a state of the art financial network...'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/login'):
            self.start()

            response_output = ''
            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.AC_IDENTITY_INCORRECT:
                    response_output += '<h4>Account name/number is incorrect. Please try again.</h4>'
                elif response_code == Responses.AC_CODE_INCORRECT:
                    response_output += '<h4>Password is incorrect. Please try again.</h4>'
                elif response_code == Responses.PROCESSING_ERROR:
                    response_output += '<h4>Processing error. Please try again at a later time.</h4>'
                elif response_code == Responses.ACCOUNT_RECOVERY_CONFIRM:
                    response_output += '<h4>Account recovered. Username/password reset.</h4>'
                elif response_code == Responses.NEW_ACCOUNT_CREATED:
                    response_output += '<h4>New account created.</h4>'
                elif response_code == Responses.SECURITY_ANSWER_INCORRECT:
                    response_output += '<h4>Security verification failed: Incorrect answer. Please try again later.</h4>'
                elif response_code == Responses.INVALID_SECURITY_ANSWER:
                    response_output += '<h4>Security verification failed: Invalid answer. Please try again later.</h4>'
                data.alter_re(self.client_address[0], 0)

            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vault', 'logo_transparent.png')

            # define the html, css, and js variables
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Page</title>
                <style>
                    /* CSS styles */
                    header {
                        font-family: Arial, sans-serif;
                        background-color: #001F54;
                        color: white;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 16px;
                    }
                    .title {
                        font-weight: bold;
                        margin: 0;
                        font-size: 28px;
                    }
                    .logo {
                        height: 2rem;
                    }
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                    }
                    .content {
                        margin: 2rem;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }
                    form {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        margin-bottom: 2rem;
                    }
                    form input {
                        margin-bottom: 1rem;
                        padding: 0.5rem;
                        border-radius: 0.25rem;
                        border: 1px solid lightgray;
                        width: 100%;
                        box-sizing: border-box;
                    }
                    form button {
                        padding: 0.5rem;
                        border-radius: 0.25rem;
                        border: none;
                        background-color: #001F54;
                        color: white;
                        cursor: pointer;
                    }
                    .links {
                        display: flex;
                        justify-content: space-between;
                        width: 100%;
                        margin-bottom: 1rem;
                    }
                    .links a {
                        color: navy;
                        text-decoration: none;
                    }
                    .response {
                        width: 100%;
                        margin-bottom: 1rem;
                    }
                    .response p {
                        color: black;
                    }
                    .divide {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin-bottom: 1rem;
                    }
                    .divide:before, .divide:after {
                        content: "";
                        border-top: 1px solid lightgray;
                        width: 100%;
                        margin: 0 0.5rem;
                    }
                    .cta {
                        width: 100%;
                        display: flex;
                        justify-content: space-between;
                        align-items: left;
                    }
                    .cta a {
                        padding: 0.5rem;
                        border-radius: 0.25rem;
                        border: 1px white;
                        color: navy;
                        text-decoration: none;
                        cursor: pointer;
                    }
                    .cta a:hover {
                        background-color: navy;
                        color: white;
                        text-decoration: none;
                    }
                    a:hover {
                        text-decoration: underline;
                    }
                </style>
            </head>
            <header>
                <h1 class="title">Login to Your Account</h1>
                <div class="logo">
                    <img src="''' + logo_path + '''" alt="FinCloud logo">
                </div>
            </header>
            <body>
                <div class="content">
                    <h3>Enter Login Details</h3>
                    <form method="POST" enctype="multipart/form-data" action="/login">
                        <input type="text" name="username" placeholder="Account Name/Number" required>
                        <input type="password" name="code" placeholder="Access Code" required>
                        <button type="submit">Login</button>
                    </form>
                    </br></br>
                    <div class="links">
                        <a href="/forgot_data">Forgot your username & password?</a>
                    </div>
                    </br></br>
                    <div class="response">''' + response_output + '''</div>
                </div>
                <div class="content">
                    </br></br></br></br>
                    <div class="cta">
                        <a href="/new">New to FinCloud? Get started</a>
                    </div>
                    </br>
                    <div class="cta">
                        <a href="/">Return to main page</a>
                    </div>
                </div>
            </body>
            </html>
            '''
            output = html
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/logout'):
            self.start()
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            output += '<h1>Your Account: ' + account_name + '</h1>'
            output += '<h2><Are you sure you want to log out of your account?</h2>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/logout">'
            output += '<input type="submit" value="Confirm Logout">' + '</form>'
            output += '<h4><a href="/account/home">Cancel and return to account home page</a></h4>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/confirm_identity'):
            self.start()
            
            question_num = random.randint(1, 2) - 1
            recovery_data = data.response_codes[self.client_address[0]]
            ac_index = recovery_data['index']
            questions = list(security_questions[ac_index].keys())
            question_to_ask = questions[question_num]
            data.response_codes[self.client_address[0]]['question'] = question_to_ask
            output = '<html><body>'
            output += '<h1>Confirm Identity - Security Question</h1>'
            output += '<h2>Answer a security question to confirm your identity and recover your account</h3>'
            output += 'Security question: ' + question_to_ask + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/confirm_identity">'
            output += 'Enter your answer: ' + '<input name="answer" type="text">' + '</br></br>'
            output += '<input type="submit" value="Recover Account"></form></br>'
            output += '</br><h4><a href="/login">Return to log in page</a></h4>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/forgot_data'):
            self.start()
            
            output = '<html><body>'
            output += '<h1>Recover your account</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/forgot_data">'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your new account password: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Continue">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.PHONE_NUM_NOT_FOUND:
                    output += '<h4>Phone number does not exist in out system.</h4>'
                elif response_code == Responses.CODES_NOT_MATCH:
                    output += '<h4>Codes do not match</h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>'
            output += '<h4><a href="/forgot">Only recover password</a></h4>'
            output += '<h4><a href="/login">Cancel and return to log in page</a></h4>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/forgot'):
            self.start()
            
            output = '<html><body>'
            output += '<h1>Recover your account</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/forgot">'
            output += 'Enter your account name/number: ' + '<input name="user" type="text">' + '</br>'
            output += 'Enter your phone number: ' + '<input name="phone" type="text">' + '</br>'
            output += '</br>'
            output += 'Enter your new account password: ' + '<input name="code" type="text">' + '</br>'
            output += 'Confirm your new account password: ' + '<input name="code_confirm" type="text">' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Continue">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.PHONE_NUM_NOT_FOUND:
                    output += '<h4>Phone number does not exist in out system.</h4>'
                elif response_code == Responses.AC_IDENTITY_INCORRECT:
                    output += '<h4>Account name/number incorrect.</h4>'
                elif response_code == Responses.CODES_NOT_MATCH:
                    output += '<h4>Codes do not match</h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>'
            output += '<h4><a href="/login">Return to log in page</a></h4>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new'):
            self.start()
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vault', 'logo_transparent.png')

            output = '''
                <!DOCTYPE html>
                <html>
                    <head>
                    <title>Open An Account</title>
                        <style>
                            /* CSS styles */
                            header {
                                font-family: Arial, sans-serif;
                                background-color: #001F54;
                                color: white;
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                padding: 16px;
                            }
                            .title {
                                font-weight: bold;
                                margin: 0;
                                font-size: 28px;
                            }
                            .logo {
                                height: 2rem;
                            }
                            body {
                                margin: 0px;
                                padding: 0px;
                            }
                            .content {
                                width: 100%;
                                margin: 0.25%;
                            }
                            .content h1 {
                                font-size: 35px;
                            }
                            .content p {
                                font-size: 18px;
                            }
                            .content a {
                                color: navy;
                                text-decoration: none;
                            }
                            .content a:hover {
                                text-decoration: underline;
                            }
                            accounttypes {
                                position: relative;
                                left: 15%;
                                width: 70%;
                                margin: 0;
                                padding: 0;
                                display: flex;
                                flex-wrap: wrap;
                                justify-content: space-evenly;
                                align-items: stretch;
                            }
                            .container {
                                width: 17%;
                                height: 450px;
                                border: 1px solid;
                                border-color: darkgray;
                                border-radius: 25px;
                                padding: 0.35%;
                            }
                            .container h4 {
                               text-align: center;
                               font-size: 28px;
                            }
                            .container p {
                                font-size: 20px;
                                padding-left: 2px;
                            }
                            .container a {
                                color: navy;
                                text-decoration: none;
                            }
                            .container a:hover {
                                text-decoration: underline;
                            }
                            return {
                                margin: 0;
                                padding: 0;
                            }
                            return a {
                                color: navy;
                                text-decoration: none;
                            }
                            return a:hover {
                                text-decoration: underline;
                            }
                            return h3 {
                                padding: 0.35%;
                            }
                            center-text {
                                display: flex;
                                flex-wrap: wrap;
                                justify-content: space-evenly;
                                align-items: stretch;
                                margin: 0;
                                padding: 0;
                                text-align: center;
                
                            }
                        </style>
                    </head>
                    <header>
                        <h1 class="title">Open An Account</h1>
                        <div class="logo">
                            <img src="''' + logo_path + '''" alt="FinCloud logo">
                        </div>
                    </header>
                    <body>
                        <div class="content">
                            <h1>Select an account that fits your needs</h1> 
                            <p>From personal accounts to specialized accounts for business, FinCloud offers the best service you can find.</p> </br>
                        </div>
                    </body>
                    <center-text>
                        <h1>Select the best account for you</h1>
                    </center-text>
                    <accounttypes>
                        <div class="container">
                            <h4><a href="/new/business">Specialized Business Account</a></h4>
                            <p>Specialized accounts that allow simple and effective management of funds throughout multiple departments.</p>
                        </div>
                        <div class="container">
                            <h4><a href="/new/checking">Personal Checking Account</a></h4>
                            <p>Personal accounts that allow for dynamic management of personal funds. Our personal accounts also offer users the option to distribute their capital and purchase multiple currencies.</p>
                        </div>
                        <div class="container">
                            <h4><a href="/new/savings">Personal Savings Account</a></h4>
                            <p>Personal accounts that support savings at an interest determined by you.</p>
                        </div>
                    </accounttypes>
                      
                    </br></br></br></br>
                    <return>
                        <h3>Already have an account? <a href="/login">Sign in here</a></h3>
                    </return>
                </html>
            '''

            self.wfile.write(output.encode())

        elif self.path.endswith('/new123'):
            self.start()

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

        elif self.path.endswith('/new/set_security_details'):
            self.start()
            
            output = '<html><body>'
            output += '<h1>Complete Your Account</h1>'
            output += '<h2>Set security question:</h2>'
            output += 'The security questions you set will allow us to verify your identity in case you ever need to recover your account. '
            output += 'Choose questions that you are certain you will always be able to answer, and make sure the question is private enough to be secure.'
            output += 'Enter the answer to each question, and make sure your answer is correct and that you are confident in your ability to remember it.'
            output += 'Enter two different questions. When you recover your account we will randomly choose one to protect your account as much as possible.'
            output += 'Remember: the security question is critical in case you need to recover you account!'
            output += 'So make sure you do not make mistakes when entering you answers, and make sure you remember them!'
            output += '<form method="POST" enctype="multipart/form-data" action="/new/set_security_details">'
            output += '<h3>Question 1:</h3>'
            output += '</br>Enter your question here: ' + '<input name="question1" type="text">' + '</br>'
            output += '</br>Enter your answer here: ' + '<input name="answer1" type="text">' + '</br></br>'
            output += '<h3>Question 2:</h3>'
            output += '</br>Enter your question here: ' + '<input name="question2" type="text">' + '</br>'
            output += '</br>Enter your answer here: ' + '<input name="answer2" type="text">' + '</br></br>'
            output += '<input type="submit" value="Create Account">'
            output += '</form>' + '</br></br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_SECURITY_DETAILS:
                    output += '</h4>Invalid input. Please try again.</h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br><a href="/new">Cancel account creation</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new/checking'):
            self.start()
            
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
            output += 'Enter initial monthly spending limit: ' + '<input name="spending_limit" type="text">' + '</br>'
            output += 'The monthly spending limit you enter here will be relevant for the next month' \
                      ' and until you alter it in the home page of your account.' + '</br>'
            output += '</br>'
            output += '<input type="submit" value="Continue">'
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
                    output += '<h4>Phone number is not valid.</h4>'
                elif response_code == Responses.PHONE_NUM_EXISTS:
                    output += '<h4>Phone number already registered to an existing account.</h4>'
                elif response_code == Responses.INVALID_SPENDING_LIMIT:
                    output += '<h4>Monthly spending limit is invalid.</h4>'
                elif response_code == Responses.CODES_NOT_MATCH:
                    output += '<h4>Code confirmation does not match the code you entered. Please try again.</h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new/savings'):
            self.start()
            
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
            output += '<option value = "premium">Premium - ' + str(RETURNS_PREMIUM) + '% annually</option>'
            output += '<option value = "medium">Regular - ' + str(RETURNS_MEDIUM) + '% annually</option>'
            output += '<option value = "minimum">Safe - ' + str(RETURNS_MINIMUM) + '% annually</option>'
            output += '</select>'
            output += '</br></br>'
            output += '<input type="submit" value="Continue">'
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new/business'):
            self.start()
            
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
            output += '<input type="submit" value="Continue">'
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += 'Want to check out different options? ' + '<a href="/new">Check them out here</a>'
            output += '</br></br></br>'
            output += 'Already have an account? ' + '<a href="/login">Sign in here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/admin_access/' + str(data.admin_token)):
            self.start()
            
            output = '<html><body>'
            output += '<a href="/admin_access/' + str(data.admin_token) + '/account_list">Accounts list</a></br></br>'
            output += '<a href="/admin_access/' + str(
                data.admin_token) + '/cloud_watch">Cloud allocations</a></br></br>'
            output += '<a href="/admin_access/' + str(
                data.admin_token) + '/send_announcements">Send Announcements</a></br></br>'
            output += '<a href="/account/logout">Log out</a></br></br></br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.MESSAGE_SENT:
                    output += '</h4>Announcement sent.</h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            self.wfile.write(output.encode())

        elif self.path.endswith('/admin_access/' + str(data.admin_token) + '/send_announcements'):
            self.start()
            
            output = '<html><body>'
            output += '<h1>Send an Announcement</h1>'
            path = '/admin_access/' + str(data.admin_token) + '/send_announcements'
            output += '<form method="POST" enctype="multipart/form-data" action="' + path + '">'
            output += 'Enter announcement subject: ' + '<input name="subject" type="text"></br>'
            output += 'Enter announcement message: ' + '<input name="message" type="text"></br>'
            output += 'From: ' + '<input name="sender" type="text"></br>'
            output += '<input type="submit" value="Send Announcement">'
            output += '</form></br>'

            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_MESSAGE_INPUT:
                    output += '<h4>Message Invalid. Please try again.<h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            self.wfile.write(output.encode())

        elif self.path.endswith('/admin_access/' + str(data.admin_token) + '/account_list'):
            self.start()
            
            output = '<table>' + '<tr>'
            output += '<th>Index</th>' + '<th> | Account name</th>' + '<th> | Account number</th>' + '<th> | Account type</th>' + '<th> | Total account value in USD</th>' + '<th> | Current active requests</th>' + '</tr>'
            for i in range(len(Accounts.log)):
                output += '<tr><td> | ' + str(i) + '</td>'
                output += '<td> | <a href="/admin_access/account_list/' + name_table.get_key(i) + '/' + str(
                    data.admin_token) + '/account_watch/details">' + name_table.get_key(i) + '</a></td>'
                output += '<td> | ' + str(number_table.get_key(i)) + '</td>'
                output += '<td> | ' + loc_type_table.in_table(i) + '</td>'
                output += '<td> | ' + Accounts.log[i].get_value_usd() + '</td>'
                active_request_count = str(0)
                if i in active_requests.keys():
                    active_request_count = str(len(active_requests[i]))
                output += '<td> | ' + active_request_count + '</td></tr>'
            output += '</table>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/' + str(data.admin_token) + '/account_watch/details'):
            self.start()
            
            url_parsed = self.path.split('/')
            ac_name = url_parsed[2]
            ac_index = name_table.in_table(ac_name)
            output = '<html><body>'
            ac_values = create_table_output(Accounts.log[ac_index].value)
            ac_type = loc_type_table.in_table(ac_index)
            ac_spending_info = [Accounts.log[ac_index].monthly_spending_limit,
                                Accounts.log[ac_index].remaining_spending]
            ac_number = number_table.get_key(ac_index)
            output += '<h1>Account Watch - ' + ac_name + '</h1>'
            output += '<h2>Account number - ' + ac_number + '</h2>'
            output += '<h2>Account Type - ' + ac_type + '</h2>'
            output += '<h3>Spending for this month: ' + ac_spending_info[1] + '/' + ac_spending_info[0] + '</h3>'
            output += '<h3>Account holdings:</h3>'
            output += ac_values
            self.wfile.write(output.encode())

        elif self.path.endswith('/admin_access/' + str(data.admin_token) + '/cloud_watch'):
            self.start()
            
            output = '<html><body>'
            allocations = Cloud().allocated
            output += '<h1>Cloud Allocations</h1></br>'
            output += '<table><tr><th>Allocation Code</th><th> | Allocated Funds</th></tr>'
            for alloc_code in allocations.keys():
                output += '<tr><td> | ' + str(alloc_code) + '</td>'
                output += '<td>' + str(allocations[alloc_code]) + '</td></tr>'
            output += '</table>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/home'):
            if name_table.get_key(data.current_account[self.client_address[0]]) == 'Admin':
                data.admin_token = hash_function(generate_code())
                self.redirect('/admin_access/' + str(data.admin_token))

            self.start()
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vault', 'logo_transparent.png')
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            account_number = str(number_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            comp_name = ''
            remaining_spending = 0
            spending_limit = 0
            ac_type = loc_type_table.in_table(ac_index)
            if ac_type == 'bus':
                comp_name = str(Accounts.log[ac_index].company_name)
            if ac_type == 'reg':
                spending_limit = Accounts.log[ac_index].monthly_spending_limit
                remaining_spending = Accounts.log[ac_index].remaining_spending

            response_output = ''
            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.DEPOSIT_CONFIRM:
                    response_output += '<h4>Deposit confirmed.</h4>'
                elif response_code == Responses.WITHDRAWAL_CONFIRM:
                    response_output += '<h4>Withdrawal confirmed.</h4>'
                elif response_code == Responses.TRANSFER_CONFIRM:
                    response_output += '<h4>Transfer confirmed.</h4>'
                elif response_code == Responses.INNER_TRANSFER_CONFIRM:
                    response_output += '<h4>Departmental transfer processed.</h4>'
                elif response_code == Responses.NEW_DEP_OPENED:
                    response_output += '<h4>New department established.</h4>'
                elif response_code == Responses.SPENDING_LIMIT_ALTERED:
                    response_output += '<h4>Spending limit changed. Your monthly spending limit will be updated at the end of the month.'
                elif response_code == Responses.REQUEST_FILED:
                    response_output += '<h4>Your request will be filed to the bank. Your will receive an update to your personal inbox.'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)
            if type(data.response_codes) is not int:
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Account Home Page</title>
                <style type="text/css">
                    /* general styling */
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                    }
                    a {
                        text-decoration: none;
                    }
                /* header styling */
                header {
                    background-color: #001F54;
                    color: #fff;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px;
                }
                .logo {
                    height: 50px;
                }
                .title {
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0;
                }

                /* main content styling */
                main {
                    display: flex;
                    justify-content: space-between;
                    padding: 20px;
                }
                .transactions {
                    width: 25%;
                    border-left: 3px solid #fff;
                    border-left-color: #001F54;
                    padding-left: 20px;
                    padding-right: 10px;
                    text-align: left;
                    margin-right: 20px
                }
                .transactions h2 {
                    font-size: 26px;
                    margin-bottom: 10px;
                }
                .transactions ul {
                    list-style-type: none;
                    margin-left: 10px;
                    padding: 0;
                }
                .transactions li {
                    margin-bottom: 10px;
                }
                .transactions li a {
                    font-size: 20px;
                }
                .cloud {
                    margin-top: 20px;
                }
                .account-info {
                    width: 70%;
                    padding-left: 10px;
                }
                .account-info h1 {
                    font-size: 40px;
                }
                .account-info p {
                    font-size: 22px;
                    margin: 0;
                }
                .account-manage {
                    width: 100%;
                    padding-left: 10px;
                }
                .account-manage h2 {
                    font-size: 26px;
                    margin-bottom: 10px;
                }
                .account-manage p {
                    font-size: 20px;
                    margin: 0;
                }
                .account-manage a {
                    font-size: 18px;
                }
                .account-manage ul {
                    list-style-type: none;
                }
                a {
                    color: navy;
                }
                a:hover {
                    text-decoration: underline;
                }
                .horizontal-line {
                    border-bottom: 1px solid #D9D9D9;
                    margin: 10px 0;
                }
                .logout {
                    padding-left: 10px;
                }
            </style>
            </head>
            <body>
                <header>
                    <h1 class="title">Account Home Page</h1>
                    <img class="logo" src="''' + logo_path + '''" alt="FinCloud Logo">
                </header>
                <main>
                    <div class="account-info">
                        <h1>Your Account</h1>
                        <p>Account Name: {}</p>
                        <p>Account Number: {}</p>
                        {}
                        </br>
                        </br>
                    </div>
                    <div class="transactions">
                        <h2>Transactions</h2>
                        <ul>
                            <li><a href="/account/deposit_funds">Deposit Funds</a></li>
                            <li><a href="/account/withdraw_funds">Withdraw Funds</a></li>
                            <li><a href="/account/transfer_funds">Transfer Funds</a></li>
                            {}
                            </br></br></br>
                            <li class="cloud"><a href="/account/cloud">Cloud Storage</a></li>
                            <li><a href="/account/transaction_history">Transaction History</a></li>
                        </ul>
                    </div>
                </main>
                <hr class="horizontal-line">
                <main>
                    <div class="account-manage">
                        <p>
                            Current account value in USD: ${}
                        </p>
                        <p>
                            {}
                        </p>
                        <h2>Manage Account:</h2>
                        <h3><a href="/account/info">Account Info</a><h3>
                        <h3><a href="/account/inbox">Account Inbox</a></h3>
                        {}
                        {}
                        </br></br>
                        <h3>{}</h3>
                        </br></br>
                    </div>
                </main>
                <main>
                    <div class="logout">
                        <a href="/account/logout">Logout of your account</a>
                    </div>
                </main>
            </body>
            </html>
            '''.format(account_name, account_number, '<p>Company: {}</p>'.format(comp_name) if ac_type == 'bus' else '', '<li><a href="/account/business/inner_transfer">Inner Transfer</a></li>' if ac_type == 'bus' else '', val, 'Remaining spending for the month: ${} out of ${}'.format(remaining_spending, spending_limit) if ac_type == 'reg' else '',
                       '<h3><a href="/account/business/open_dep">Open new department</a></h3>' if ac_type == 'bus' else '', '<h3><a href="/account/change_spending_limit">Change spending limit</a></h3>' if ac_type == 'reg' else '', response_output)

            output = html
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/info'):
            pass

        elif self.path.endswith('/account/transaction_history'):
            self.start()
            
            ac_index = data.current_account[self.client_address[0]]
            ac_type = loc_type_table.in_table(ac_index)
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vault', 'logo_transparent.png')
            if ac_type != 'bus':
                entries = [entry for entry in Accounts.log[ac_index].ledger.log]
            else:
                entries = []
                for dep_name in Accounts.log[ac_index].departments.keys():
                    for entry in Accounts.log[ac_index].departments[dep_name][1].log:
                        entries.append(entry)

            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vault', 'logo_transparent.png')

            # Define HTML/CSS/JS for transaction history page

            output = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Transaction History</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    /* Define page styles */
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f5f5f5;
                    }
                    .page-container {
                        margin: 0 auto;
                        background-color: white;
                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
                    }
                    .header {
                        background-color: #001F54;
                        color: #fff;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 16px;
                    }
                    .title {
                        font-size: 28px;
                        font-weight: bold;
                        margin: 0;
                    }
                    .entry {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 16px;
                        border-bottom: 1px solid #e0e0e0;
                    }
                    .entry-details {
                        display: none;
                        margin-top: 16px;
                        padding: 16px;
                        border-radius: 4px;
                        background-color: #f5f5f5;
                        font-size: 14px;
                    }
                    .entry:hover .entry-details {
                        display: block;
                    }
                    .entry-id {
                        font-size: 14px;
                        color: #999;
                    }
                    .entry-action {
                        font-size: 16px;
                        font-weight: bold;
                        margin: 0;
                    }
                    .entry-date {
                        font-size: 14px;
                        margin: 0;
                    }
                    .entry-amount {
                        margin: 8px 0;
                    }
                    .entry-target {
                        margin: 8px 0;
                    }
                </style>
            </head>
            <body>
                <div class="page-container">
                    <div class="header">
                        <h1 class="title">Transaction History</h1>
                    </div>
            '''

            # Generate HTML for each transaction in the entries list
            transactions_html = ""
            for entry in entries:
                details_html = f'''
                    <div class="entry-details">
                        <p class="entry-amount">Amount: {entry.amount}</p>
                        <p class="entry-target">Target/source account number: {entry.target_num}</p>
                        <p class="entry-target">Target/source department name: {entry.target_dep}</p>
                    </div>
                '''
                transaction_html = f'''
                    <div class="entry">
                        <div>
                            <p class="entry-id">Entry ID: {entry.entry_id}</p>
                            <p class="entry-action">{entry.action}</p>
                            <p class="entry-date">{date_to_str(entry.date)}</p>
                        </div>
                        {details_html}
                    </div>
                '''
                transactions_html += transaction_html

            # Add transaction entries to the output HTML
            output += transactions_html
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/inbox'):
            self.start()
            
            ac_index = data.current_account[self.client_address[0]]
            messages = Accounts.log[ac_index].inbox
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vault', 'logo_transparent.png')

            # Define the CSS styling for the page
            css = """
                body {
                    background-color: #F9F9F9;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    margin: 0;
                }

                header {
                    background-color: #001F54;
                    color: #fff;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px;
                }
                
                .file-request-link {
                    display: inline-block;
                    float: right;
                    color: #fff;
                    text-decoration: none;
                    margin-right: 10px;
                }
            
                .file-request-link:hover {
                    text-decoration: underline;
                }
                
                .logo img {
                    display: inline-block;
                    float: right;
                    height: 60px;
                }

                .title {
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0;
                }
                
                .message {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                }

                .message-details {
                    display: none;
                    margin-top: 10px;
                    text-align: left;
                    margin-left: 20px;
                }

                .subject {
                    font-weight: bold;
                }

                .show-details {
                    color: #001F54;
                    cursor: pointer;
                    text-decoration: underline;
                }

                .hide-details {
                    color: #001F54;
                    cursor: pointer;
                    text-decoration: underline;
                }

                .horizontal-line {
                    border-bottom: 1px solid #D9D9D9;
                    margin: 10px 0;
                }

                .red-flag {
                    color: red;
                }

                .no-messages {
                    font-size: 32px;
                    font-weight: bold;
                    text-align: center;
                    margin-top: 50px;
                }
            """
            # Generate HTML for each message in the messages list
            messages_html = ""
            for message in messages:
                details_html = f"""
                    <div class="message-details" id="message-details-{message.message_id}">
                        <p><b>Message:</b> {message.message}</p>
                        <p><b>Message ID:</b> {message.message_id}</p>
                    </div>
                    <hr class="horizontal-line">
                """
                if message.message_type == 'red flag':
                    message_html = f"""
                    <div class="message red-flag" id="message-{message.message_id}">
                        <div>
                            <p class="subject">{message.subject}</p>
                            <p>{message.sender}</p>
                        </div>
                        <div>
                            <p>{date_to_str(message.date)}</p>
                            <p class="show-details" onclick="showDetails({message.message_id})">Show Details</p>
                            <p class="hide-details" onclick="hideDetails({message.message_id})" style="display:none">Hide Details</p>
                        </div>
                    </div>
                    {details_html}
                """
                else:
                    message_html = f"""
                        <div class="message" id="message-{message.message_id}">
                            <div>
                                <p class="subject">{message.subject}</p>
                                <p>{message.sender}</p>
                            </div>
                            <div>
                                <p>{date_to_str(message.date)}</p>
                                <p class="show-details" onclick="showDetails({message.message_id})">Show Details</p>
                                <p class="hide-details" onclick="hideDetails({message.message_id})" style="display:none">Hide Details</p>
                            </div>
                        </div>
                        {details_html}
                    """
                messages_html += message_html
            if messages:
                page_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <title>Account Inbox</title>
                <style>{css}</style>
                <script>
                function showDetails(message_id) {{
                var details = document.getElementById("message-details-" + message_id);
                var showLink = document.querySelector("#message-" + message_id + " .show-details");
                var hideLink = document.querySelector("#message-" + message_id + " .hide-details");
                details.style.display = "block";
                showLink.style.display = "none";
                hideLink.style.display = "inline";
                }}
                            function hideDetails(message_id) {{
                                var details = document.getElementById("message-details-" + message_id);
                                var showLink = document.querySelector("#message-" + message_id + " .show-details");
                                var hideLink = document.querySelector("#message-" + message_id + " .hide-details");
                                details.style.display = "none";
                                showLink.style.display = "inline";
                                hideLink.style.display = "none";
                            }}
                        </script>
                    </head>
                    <body>
                        <header>
                            <h1 class="title">Account Inbox</h1>
                            <a class="file-request-link" href="/account/inbox/file_requests">File Request</a>
                            <div class="logo">
                                <img src="{logo_path}" alt="Logo">
                            </div>
                        </header>
                        <div class="horizontal-line"></div>
                        {messages_html}
                    </body>
                    </html>
                """
            else:
                page_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <title>Account Inbox</title>
                <style>{css}</style>
                </head>
                <body>
                <header>
                <h1 class="title">Account Inbox</h1>
                <div class="logo">
                <img src="{logo_path}" alt="Logo">
                </div>
                </header>
                <div class="horizontal-line"></div>
                <p class="no-messages">No messages to display</p>
                </body>
                </html>
                """
            output = page_html
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/inbox/file_requests'):
            self.start()
            
            ac_index = data.current_account[self.client_address[0]]
            messages = Accounts.log[ac_index].inbox
            red_flag_messages = [message for message in messages if message.message_type == 'red flag']
            red_flag_message_id_list = [message.message_id for message in red_flag_messages]
            output = '<html><body>'
            output += '<h1>File Request</h1>'
            output += 'If you have been notified regarding red flags in your account history, ' \
                      'you have the option to file a request to the bank to reverse the transaction. ' \
                      'If you receive a red flag notification for a transaction, and believe it was done unintentionally, ' \
                      'or by a malicious third party, please file a request to the bank and we will notify you shortly. ' \
                      'Thank you, FinCloud Anomaly Detection Team'

            output += '<form method="POST" enctype="multipart/form-data" action="/account/inbox/file_requests">'
            output += 'Enter account password: ' + '<input name="code" type="text">' + '</br>'
            output += 'Select message id for red flag: '
            output += '<select id="message_id" name="message_id">'
            for rf_id in red_flag_message_id_list:
                rf_id = str(rf_id)
                output += '<option value = "' + rf_id + '">' + rf_id + '</option>'
            output += '</select></br></br>'
            output += '<input type="submit" value="Submit Request">'
            output += '</form>' + '</br>'

            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_MESSAGE_ID:
                    output += '<h4>Message ID is not valid.</h4>'
                elif response_code == Responses.REQUEST_ALREADY_FILED:
                    output += '<h4>Request has already been filed for this message ID.</h4>'
                elif response_code == Responses.AC_CODE_INVALID:
                    output += '<h4>Account password is not valid.</h4>'
                elif response_code == Responses.AC_CODE_INCORRECT:
                    output += '<h4>Account password is incorrect.</h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br><h4><a href="/account/inbox">Cancel Request</a></h4>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/confirm_spending'):
            self.start()
            
            output = '<html><body>'
            output += '<h1>Transaction Confirmation</h1>'
            output += '<h3>Completing this transaction will place you in a monthly sending deficit and likely result in fees.</h3>'
            output += 'If you proceed with the transaction, a fee will be deducted form your account!'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/confirm_spending">'
            output += '<input type="submit" value="Confirm Transaction">'
            output += '</form>' + '</br>'
            output += '<h4><a href="/account/home">Cancel transaction</a></h4>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/change_spending_limit'):
            self.start()
            
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            output += '<h1>Change Monthly Spending limit</h1>' + '</br>'
            output += '<h3>Current spending limit per month: ' + str(Accounts.log[
                ac_index].monthly_spending_limit) + '</h3></br>'
            output += 'Your monthly spending limit allows you to maintain expenses on your account. ' \
                      'If you overspend you will encounter a fee,' \
                      ' but spending less than you monthly spending limit could add value to your account,' \
                      ' courtesy of the funds management team.'
            output += '</br>'
            output += '<h2>Update your spending limit for next month: </h2></br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/change_spending_limit">'
            output += 'Enter new monthly spending limit: ' + '<input name="new_limit" type="text">' + '</br></br>'
            output += '<input type="submit" value="Submit">'
            output += '</form>' + '</br>'

            # print error/response message if redirect flag is set to True
            if data.redirect_flags[self.client_address[0]]:
                data.alter_rf(self.client_address[0], False)
                response_code = data.response_codes[self.client_address[0]]
                if response_code == Responses.INVALID_SPENDING_LIMIT:
                    output += '<h4>Spending limit is not valid.</h4>'
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br></br>' + 'To cancel and return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/deposit_funds'):
            self.start()
            
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output += '<h1>Deposit Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/deposit_funds">'
            output += 'Enter amount to deposit: ' + '<input name="amount" type="text">' + '</br></br>'
            if loc_type_table.in_table(ac_index) == 'bus':
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/withdraw_funds'):
            self.start()
            
            output = '<html><body>'
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            output += '<h1>Withdraw Funds</h1>' + '</br>'
            output += '<h2>Your Account: ' + account_name + '</h2>'
            output += '<h3>Current value in USD: ' + val + '</h3>' + '</br>' + '</br>'
            output += '<form method="POST" enctype="multipart/form-data" action="/account/withdraw_funds">'
            output += 'Enter amount to withdraw: ' + '<input name="amount" type="text">' + '</br></br>'
            if loc_type_table.in_table(ac_index) == 'bus':
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/transfer_funds'):
            self.start()
            
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.in_table(ac_index)
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/holdings'):
            self.start()
            
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br></br>' + 'To trade and invest in different currencies ' + \
                      '<a href="/account/holdings/trade_currency">Click here</a>' + '</br></br>'
            output += 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/business/departments'):
            self.start()
            
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br></br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/holdings/trade_currency'):
            self.start()
            
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>' + '</br>' + 'To return to account holdings page ' + '<a href="/account/holdings">Click here</a>'
            output += '</br>' + '</br>' + 'Return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/invest_capital/trade_currencies'):
            self.start()
            
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>' + '</br>' + 'To return to account holdings page ' + '<a href="/account/business/departments">Click here</a>'
            output += '</br>' + '</br>' + 'Return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/business/inner_transfer'):
            self.start()
            
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/cloud'):
            self.start()
            
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)
            if type(data.response_codes) is not int:
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>' + '</br>' + 'To return to account home page ' + '<a href="/account/home">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/cloud/allocate'):
            self.start()
            
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.in_table(ac_index)
            output = '<html><body>'
            output += '<h1>Allocate Funds With FinCloud</h1>' + '</br>'
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>' + '</br>' + 'To return to FinCloud page ' + '<a href="/account/cloud">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/cloud/withdraw'):
            self.start()
            
            ac_index = data.current_account[self.client_address[0]]
            account_name = str(name_table.get_key(ac_index))
            val = Accounts.log[ac_index].get_value_usd()
            ac_type = loc_type_table.in_table(ac_index)
            output = '<html><body>'
            output += '<h1>Withdraw Funds From FinCloud</h1>' + '</br>'
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

            output += '</br>' + '</br>' + 'To return to FinCloud page ' + '<a href="/account/cloud">Click here</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/account/business/open_dep'):
            self.start()
            
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
                data.alter_re(self.client_address[0], Responses.EMPTY_RESPONSE)

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

        # check if first action in history log is of post type (system error / attempt by user to exploit)
        if history[self.client_address[0]].log[0].lst[0] == 'post':
            self.system_error()

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
                save_attempt = ''
                if user_attempt == 'stop_server':
                    save_attempt = 'stop_server'
                    user_attempt = 'Admin'
                # verification process with input from user
                verify, response_code, index = verification(user_attempt, code_attempt)
                if verify and save_attempt == 'stop_server':
                    data.run_server_flag = False
                    self.system_error()
                if verify:
                    data.alter_ca(self.client_address[0], index)
                    self.redirect('/account/home')
                else:
                    data.alter_re(self.client_address[0], response_code)
                    data.alter_rf(self.client_address[0], True)
                    self.redirect('/login')
            else:
                self.system_error()

        elif self.path.endswith('/account/logout'):
            # logout page does not request input, any post request signals logging out of account
            data.delete_ca(self.client_address[0])
            self.redirect('/login')

        elif self.path.endswith('/new/set_security_details'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                security_fields = [fields.get('question1')[0], fields.get('answer1')[0], fields.get('question2')[0],
                                   fields.get('answer2')[0]]
                confirm = True
                for field in security_fields:
                    if not validate_string(field):
                        confirm = False
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], Responses.INVALID_SECURITY_DETAILS)
                        self.redirect('/new/set_security_details')

                if confirm:
                    questions_data = {fields.get('question1')[0]: fields.get('answer1')[0],
                                      fields.get('question2')[0]: fields.get('answer2')[0]}
                    param_list = data.response_codes[self.client_address[0]]
                    ac_type = param_list['type']
                    confirm = False
                    response_code = Responses.EMPTY_RESPONSE
                    index = -1
                    if ac_type == 'reg':
                        confirm, index, response_code = create_checking_account(param_list['account name'],
                                                                                param_list['code'],
                                                                                param_list['phone num'],
                                                                                param_list['spending limit'])
                    elif ac_type == 'sav':
                        confirm, index, response_code = create_savings_account(param_list['account name'],
                                                                               param_list['code'],
                                                                               param_list['phone num'],
                                                                               param_list['returns'])
                    elif ac_type == 'bus':
                        confirm, index, response_code = create_business_account(param_list['account name'],
                                                                                param_list['company name'],
                                                                                param_list['code'],
                                                                                param_list['phone num'])
                    else:
                        self.system_error()

                    if confirm:
                        if index >= 0:
                            security_questions[index] = questions_data
                        else:
                            self.system_error()
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], Responses.NEW_ACCOUNT_CREATED)
                        self.redirect('/login')
                    else:
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], response_code)
                        if ac_type == 'reg':
                            self.redirect('/new/checking')
                        elif ac_type == 'sav':
                            self.redirect('/new/savings')
                        else:
                            self.redirect('/new/business')
            else:
                self.system_error()

        elif self.path.endswith('/new/savings'):
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
                returns_dict = {'premium': RETURNS_PREMIUM, 'medium': RETURNS_MEDIUM,
                                'safe': RETURNS_MINIMUM}  # to determine returns in numbers
                returns = returns_dict[returns_str]
                # create account with user input
                if code == code_confirm:
                    param_list = {'type': 'sav', 'account name': account_name, 'code': code, 'phone num': phone_number,
                                  'returns': returns}
                    data.alter_re(self.client_address[0], param_list)
                    data.alter_rf(self.client_address[0], False)
                    self.redirect('/new/set_security_details')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                    self.redirect('/new/savings')
            else:
                self.system_error()

        elif self.path.endswith('/new/business'):
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
                    param_list = {'type': 'bus', 'account name': account_name, 'code': code, 'phone num': phone_number,
                                  'company name': company_name}
                    data.alter_re(self.client_address[0], param_list)
                    data.alter_rf(self.client_address[0], False)
                    self.redirect('/new/set_security_details')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                    self.redirect('/new/business')
            else:
                self.system_error()

        elif self.path.endswith('/new/checking'):
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
                spending_limit = fields.get('spending_limit')[0]
                # create account with user input
                if code == code_confirm:
                    if not validate_number(spending_limit):
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], Responses.INVALID_SPENDING_LIMIT)
                        self.redirect('/new/checking')
                    else:
                        param_list = {'type': 'reg', 'account name': account_name, 'code': code, 'phone num': phone_number,
                                      'spending limit': int(spending_limit)}
                        data.alter_re(self.client_address[0], param_list)
                        data.alter_rf(self.client_address[0], False)
                        self.redirect('/new/set_security_details')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                    self.redirect('/new/checking')
            else:
                self.system_error()

        elif self.path.endswith('/confirm_identity'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                answer = fields.get('answer')[0]
                recovery_data = data.response_codes[self.client_address[0]]
                new_code = recovery_data['new code']
                ac_index = recovery_data['index']
                new_user = ''
                if 'new user' in recovery_data.keys():
                    new_user = recovery_data['new user']

                # verify recovery
                confirm, response_code = security_verification(ac_index, recovery_data['question'], answer)
                if confirm:
                    pass_table.alter_key_index(ac_index, hash_function(new_code))
                    if 'new user' in recovery_data.keys():
                        name_table.alter_key_index(ac_index, new_user)
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.ACCOUNT_RECOVERY_CONFIRM)
                    self.redirect('/login')
                else:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/login')
            else:
                self.system_error()

        elif self.path.endswith('/forgot'):
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
                            recovery_data = {'index': account_loc, 'new code': new_code}

                            # redirect to identity confirmation page and send approval
                            data.alter_rf(self.client_address[0], False)
                            data.alter_re(self.client_address[0], recovery_data)
                            self.redirect('/confirm_identity')
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

        elif self.path.endswith('/forgot_data'):
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
                new_user = fields.get('user')[0]

                # account code reset process with user input
                if new_code == code_confirm:
                    if phone_name_table.in_table(hash_function(phone_number)) != -1:
                        account_name = phone_name_table.in_table(hash_function(phone_number))
                        account_loc = name_table.in_table(account_name)
                        recovery_data = {'index': account_loc, 'new code': new_code, 'new user': new_user}

                        # redirect to identity confirmation page and send approval
                        data.alter_rf(self.client_address[0], False)
                        data.alter_re(self.client_address[0], recovery_data)
                        self.redirect('/confirm_identity')
                    else:
                        # redirect to forgot page and send error message (phone number does not exist in our system)
                        data.alter_rf(self.client_address[0], True)
                        data.alter_re(self.client_address[0], Responses.PHONE_NUM_NOT_FOUND)
                        self.redirect('/forgot_data')
                else:
                    # redirect to forgot page send error message (codes do not match)
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.CODES_NOT_MATCH)
                    self.redirect('/forgot_data')
            else:
                self.system_error()

        elif self.path.endswith('/admin_access/' + str(data.admin_token) + '/send_announcements'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                subject = fields.get('subject')[0]
                message = fields.get('message')[0]
                sender = fields.get('sender')[0]
                if not validate_string(subject) or not validate_string(message) or not validate_string(sender):
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.INVALID_MESSAGE_INPUT)
                    self.redirect('/admin_access/' + str(data.admin_token) + '/send_announcements')
                else:
                    mes_type = 'announcement'  # change to announcement
                    send_announcement(subject, message, sender, mes_type)
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.MESSAGE_SENT)
                    self.redirect('/admin_access/' + str(data.admin_token))
            else:
                self.system_error()

        elif self.path.endswith('/account/inbox/file_requests'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                message_id = ''
                try:
                    message_id = fields.get('message_id')[0]
                except TypeError:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.INVALID_MESSAGE_ID)
                    self.redirect('/account/inbox/file_requests')
                    return
                ac_code = fields.get('code')[0]
                ac_index = data.current_account[self.client_address[0]]
                # verify
                verify, response_code, index = verification(name_table.get_key(ac_index), ac_code)
                if index != ac_index:
                    self.system_error()
                if not verify:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], response_code)
                    self.redirect('/account/inbox/file_requests')
                    return
                # find message
                message = None
                for index in range(len(Accounts.log[ac_index].inbox)):
                    if Accounts.log[ac_index].inbox[index].message_id == int(message_id):
                        message = Accounts.log[ac_index].inbox[index]
                if message is None:
                    self.system_error()
                # when a message is a red flag, we know the structure of the message so we can parse it to find the entry id
                entry_id = find_id_in_message(message)
                # finding the entire entry with the entry id
                ac_type = loc_type_table.in_table(ac_index)
                entry = None
                dep = -1
                if ac_type != 'bus':
                    entry = [entry for entry in Accounts.log[ac_index].ledger if entry.entry_id == entry_id][0]
                else:
                    for dep_name in Accounts.log[ac_index].departments.keys():
                        for entry_runner in Accounts.log[ac_index].departments[dep_name][1]:
                            if entry_runner.entry_id == entry_id and entry_runner.action != 'tfi' and entry_runner.action != 'tti':
                                entry = entry_runner
                                dep = dep_name
                # if entry is not found, call system error function
                if entry is None:
                    self.system_error()
                # check if request was already filed for this entry
                already_filed = False
                for request in active_requests[ac_index]:
                    if request.entry_id == entry_id:
                        already_filed = True
                for request in previous_requests[ac_index]:
                    if request.entry_id == entry_id:
                        already_filed = True
                if already_filed:
                    data.alter_rf(self.client_address[0], True)
                    data.alter_re(self.client_address[0], Responses.REQUEST_ALREADY_FILED)
                    self.redirect('/account/inbox')
                    return

                # create and file request
                new_request = Request(entry, ac_index, dep)
                active_requests[ac_index].append(new_request)
                data.alter_rf(self.client_address[0], True)
                data.alter_re(self.client_address[0], Responses.REQUEST_FILED)
                self.redirect('/account/inbox/file_requests')
            else:
                self.system_error()

        elif self.path.endswith('/account/deposit_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                amount = fields.get('amount')[0]
                is_bus_account = False
                if loc_type_table.in_table(data.current_account[self.client_address[0]]) == 'bus':
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

        elif self.path.endswith('/account/withdraw_funds'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                amount = int(fields.get('amount')[0])
                is_bus_account = False
                ac_index = data.current_account[self.client_address[0]]
                ac_type = loc_type_table.in_table(ac_index)
                if ac_type == 'reg':
                    if Accounts.log[ac_index].remaining_spending < amount:
                        data.alter_re(self.client_address[0], [Responses.OVERSPEND_BY_WITHDRAWAL, amount])
                        self.redirect('/account/confirm_spending')
                        return
                elif ac_type == 'bus':
                    is_bus_account = True
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

        elif self.path.endswith('/account/transfer_funds'):
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
                ac_type = loc_type_table.in_table(ac_index)
                if ac_type == 'reg':
                    if Accounts.log[ac_index].remaining_spending < amount:
                        data.alter_re(self.client_address[0],
                                      [Responses.OVERSPEND_BY_TRANSFER, amount, target_account, target_dep])
                        self.redirect('/account/confirm_spending')
                        return
                elif ac_type == 'bus':
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

        elif self.path.endswith('/account/confirm_spending'):
            action_description = data.response_codes[self.client_address[0]]
            response_code = action_description['response_code']
            action = 'transfer' if response_code == Responses.OVERSPEND_BY_TRANSFER \
                else ('withdraw' if response_code == Responses.OVERSPEND_BY_WITHDRAWAL
                      else 'allocate')
            ac_index = data.current_account[self.client_address[0]]
            if action == 'transfer':
                (response_code, amount, target_account, target_dep) = unpack_list(action_description)
                confirm, response_code = Accounts.log[ac_index].transfer(amount, target_account, target_dep)
            elif action == 'withdraw':
                (response_code, amount) = unpack_list(action_description)
                confirm, response_code = Accounts.log[ac_index].withdraw(amount)
            else:
                (response_code, amount, allocation_code, ac_name, dep_name) = unpack_list(action_description)
                confirm, response_code = Cloud().allocate(amount, allocation_code, ac_name, dep_name)
            data.alter_rf(self.client_address[0], True)
            data.alter_re(self.client_address[0], response_code)
            if not confirm:
                if action == 'transfer':
                    self.redirect('/account/transfer_funds')
                if action == 'withdraw':
                    self.redirect('/account/withdraw_funds')
                else:
                    self.redirect('/account/cloud/allocate')
            else:
                self.redirect('/account/home')

        elif self.path.endswith('/account/business/inner_transfer'):
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

        elif self.path.endswith('/account/change_spending_limit'):
            # extract user input from headers in POST packet
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                new_limit = fields.get('new_limit')[0]
                response_code = Responses.SPENDING_LIMIT_ALTERED
                confirm = False
                if not validate_number(new_limit):
                    response_code = Responses.INVALID_SPENDING_LIMIT
                elif int(new_limit) < 0:
                    response_code = Responses.INVALID_SPENDING_LIMIT
                else:
                    ac_index = data.current_account[self.client_address[0]]
                    Accounts.log[ac_index].new_spending_limit = new_limit
                    confirm = True
                data.alter_re(self.client_address[0], response_code)
                data.alter_rf(self.client_address[0], True)
                if confirm:
                    self.redirect('/account/home')
                else:
                    self.redirect('/account/change_spending_limit')
            else:
                self.system_error()

        elif self.path.endswith('/account/business/open_dep'):
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

        elif self.path.endswith('/account/holdings/trade_currency'):
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

        elif self.path.endswith('/invest_capital/trade_currencies'):
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

        elif self.path.endswith('/account/cloud/allocate'):
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
                ac_type = loc_type_table.in_table(ac_index)
                dep_name = dep_name = fields.get('dep_name')[0]
                if ac_type != 'bus':
                    dep_name = 'none'
                if ac_type == 'reg':
                    if Accounts.log[ac_index].remaining_spending < amount:
                        data.alter_re(self.client_address[0], [Responses.OVERSPEND_BY_ALLOCATION, amount, allocation_id,
                                                               name_table.get_key(ac_index), dep_name])
                        self.redirect('/account/confirm_spending')
                        return
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

        elif self.path.endswith('/account/cloud/withdraw'):
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
                if loc_type_table.in_table(ac_index) == 'bus':
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
