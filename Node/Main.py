#!/usr/local/bin/python3

import threading
import time
from datetime import datetime

from ClientMgmt import Client
from ClientNetworking import ThrClientManagementServer, ThrClientManagementRequestHandler
from CryptoHandler import CryptoHandler
from DbManager import ClientModel
from Utils import Singleton

if __name__ == '__main__':
    # Starting CryptoHandler (key generation)
    # noinspection PyCallByClass,PyCallByClass
    Singleton.Instance(CryptoHandler)

    # Starting Client Management server
    # address = ('::1', 37405)
    address = ('localhost', 37405)
    server = ThrClientManagementServer(address, ThrClientManagementRequestHandler)
    print("Server launched : " + str(server.server_address))
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.setDaemon(True)
    serverThread.start()
    print("Server running in " + serverThread.getName())

    try:
        while True:
            user_input = input("")
            if user_input == "kill":
                client: Client = Client.get_client("44f032b414a9b939a83e1d4fe955b588ca5ab1f7")
                client.close("node killed")
            elif user_input == "list":
                Client.list_clients()
            elif user_input == "listall":
                print("List of known clients :")
                for client in ClientModel.select():
                    if Client.get_client(client.identity):
                        print("- " + client.identity + " - Online")
                    else:
                        print(
                            "- " + client.identity + " - last seen : " + str(datetime.fromtimestamp(client.last_seen)))
            elif user_input == "killall":
                print("Terminating all client connections")
                Client.kill_all_clients()
    except KeyboardInterrupt:
        print("")
        print("")
        print("Terminating all client connections and exiting...")
        Client.kill_all_clients()
        while True:
            if Client.clients_count() == 0:
                break
            time.sleep(0.5)
