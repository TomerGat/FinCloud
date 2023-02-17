# import system objects/functions
from Fincloud_general_systems import *
from Fincloud_request_handler import FinCloudHTTPRequestHandler
from Fincloud_background_functions import session_timing, accounts_update, rates_update, refresh_admin_credentials, anomaly_detection


# main - driver function
def main():
    # admin account and credentials setup
    print('Setting up credentials')
    Admin_code = str(hash_function(generate_code()))
    dir_path = str(os.path.dirname(os.path.abspath(__file__))) + '\\credentials'
    file_path = dir_path + '\\Admin_credentials.txt'
    try:
        os.mkdir(dir_path)
    except FileExistsError:
        pass
    with open(file_path, 'w') as file:
        file.write(Admin_code)

    print('Creating Admin account')
    create_checking_account('Admin', Admin_code, 1234567890, 1)
    loc_type_table.body[0] = 'admin'

    # thread management
    print('Starting background threads:')

    # create separate thread for session timings
    session_thread = threading.Thread(target=session_timing)
    # run the thread
    session_thread.start()
    session_thread_ID = session_thread.ident
    print('* Session timing thread started at thread id = "' + str(session_thread_ID) + '"')

    # create separate thread for account updates
    accounts_update_thread = threading.Thread(target=accounts_update)
    # run the thread
    accounts_update_thread.start()
    accounts_update_thread_ID = accounts_update_thread.ident
    print('* Account updating thread started at thread ID = "' + str(accounts_update_thread_ID) + '"')

    # create separate thread for currency rates updates
    rates_update_thread = threading.Thread(target=rates_update)
    # run the thread
    rates_update_thread.start()
    rates_update_thread_ID = rates_update_thread.ident
    print('* Currency rates updating thread started at thread ID = "' + str(rates_update_thread_ID) + '"')

    # create separate thread for admin credentials updates
    credentials_update_thread = threading.Thread(target=refresh_admin_credentials)
    # run the thread
    credentials_update_thread.start()
    credentials_update_thread_ID = credentials_update_thread.ident
    print('* Admin credentials updating thread started at thread ID = "' + str(credentials_update_thread_ID) + '"')

    # create separate thread for anomaly detection and handling
    anomaly_detection_thread = threading.Thread(target=anomaly_detection)
    # run the thread
    anomaly_detection_thread.start()
    anomaly_detection_thread_ID = anomaly_detection_thread.ident
    print('* Anomaly detection thread started at thread ID = "' + str(anomaly_detection_thread_ID) + '"\n')

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
