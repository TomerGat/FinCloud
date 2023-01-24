# import system objects/functions
from Fincloud_general_systems import *
from Fincloud_request_handler import FinCloudHTTPRequestHandler
from Fincloud_background_functions import session_timing, savings_update, rates_update, refresh_admin_credentials


# main - driver function
def main():
    # admin account and credentials setup
    Admin_code = str(hash_function(generate_code()))
    dir_path = str(os.path.dirname(os.path.abspath(__file__))) + '\\credentials'
    file_path = dir_path + '\\Admin_credentials.txt'
    try:
        os.mkdir(dir_path)
    except FileExistsError:
        pass
    with open(file_path, 'w') as file:
        file.write(Admin_code)
    create_checking_account('Admin', Admin_code, 1234567890)
    loc_type_table.body[0] = 'admin'

    # thread management
    print('Starting background threads:')

    # create separate thread for session timings
    session_thread = threading.Thread(target=session_timing)
    # run the process
    session_thread.start()
    session_thread_ID = session_thread.ident
    print('* Session timing thread started at thread id = "' + str(session_thread_ID) + '"')

    # create separate thread for savings updates
    savings_update_thread = threading.Thread(target=savings_update)
    # run the process
    savings_update_thread.start()
    savings_update_thread_ID = savings_update_thread.ident
    print('* Savings account updating thread started at thread ID = "' + str(savings_update_thread_ID) + '"')

    # create separate thread for currency rates updates
    rates_update_thread = threading.Thread(target=rates_update)
    # run the process
    rates_update_thread.start()
    rates_update_thread_ID = rates_update_thread.ident
    print('* Currency rates updating thread started at thread ID = "' + str(rates_update_thread_ID) + '"')

    # create separate thread for admin credentials updates
    credentials_update_thread = threading.Thread(target=refresh_admin_credentials)
    # run the process
    credentials_update_thread.start()
    credentials_update_thread_ID = credentials_update_thread.ident
    print('* Admin credentials updating thread started at thread ID = "' + str(credentials_update_thread_ID) + '"\n')

    # create HTTP server with custom request handler
    print('Running main thread at thread ID = "' + str(threading.get_ident()) + '"')
    PORT = 8080
    IP = socket.gethostbyname(socket.gethostname())
    server_address = (IP, PORT)
    server = http.server.HTTPServer(server_address, FinCloudHTTPRequestHandler)
    print('Server running at http://{}:{}'.format(IP, PORT))
    server.serve_forever()

    # delete admin credentials
    with open(file_path, 'w') as file:
        file.write('')


# run main driver function
if __name__ == '__main__':
    main()
