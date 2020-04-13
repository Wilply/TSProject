import threading

from Node.ClientMgmt import Client
from Node.ClientNetworking import ThrClientManagementServer, ThrClientManagementRequestHandler
from Node.CryptoHandler import CryptoHandler
from Node.Utils import Singleton

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

    while True:
        user_input = input("")
        if user_input == "kill":
            client: Client = Client.get_client("44f032b414a9b939a83e1d4fe955b588ca5ab1f7")
            client.close("node killed")
        elif user_input == "list":
            Client.list_clients()
