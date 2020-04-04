import socketserver
import threading
import Node.ClientMgmt
from socket import socket


class ThrClientManagementRequestHandler(socketserver.BaseRequestHandler):
    request: socket

    def __init__(self, request, client_address, node_server):
        self.client = None
        self.is_listening = True
        super().__init__(request, client_address, node_server)

    # Point d'entrée de chaque connexion client établie
    def handle(self):
        # Un nouveau client est connecté :
        self.client = Node.ClientMgmt.Client(self)
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " connected.")
        while self.is_listening:
            try:
                data: str = self.request.recv(1024).decode("utf-8")
                print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " -> " + data)
                # On process les données reçues par le client
                if data:
                    self.client.process_request(data)
                else:
                    self.close()
                    self.is_listening = False
            except OSError:
                pass
        return

    def send(self, data: str, is_error: bool = False):
        code = "OK" if not is_error else "ERR"
        sending_data = code + " " + data
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " <- " + sending_data)
        self.request.send(sending_data.encode())

    def close(self):
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " closed connection to node.")
        self.request.close()
        del self.client
        self.is_listening = False


class ThrClientManagementServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
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
