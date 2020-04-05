import threading

from Node.ClientNetworking import ThrClientManagementServer, ThrClientManagementRequestHandler
from Node.CryptoHandler import CryptoHandler, Singleton

if __name__ == '__main__':
    # Starting CryptoHandler (key generation)
    Singleton.Instance(CryptoHandler)

    # Starting Client Management server
    address = ('localhost', 37405)
    server = ThrClientManagementServer(address, ThrClientManagementRequestHandler)
    print("Server launched : " + str(server.server_address))
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.setDaemon(True)
    serverThread.start()
    print("Server running in " + serverThread.getName())

    while True:
        input("")
