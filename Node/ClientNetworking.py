import socketserver
import threading
from socket import socket


class ThrClientManagementRequestHandler(socketserver.BaseRequestHandler):
    request: socket

    def __init__(self, request, client_address, node_server):
        self.client = None
        super().__init__(request, client_address, node_server)

    # Point d'entrée de chaque connexion client établie
    def handle(self):
        # Un nouveau client est connecté :
        from Node.ClientMgmt import Client, ClientDisconnected
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " connected.")

        # Boucle de gestion du client
        try:
            self.client = Client(self)
        except ClientDisconnected:
            pass

        # Fin de la boucle : le client a donc quitté
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " closed connection to node.")
        self.request.close()
        del self.client
        return

    def receive(self) -> str:
        data: str = self.request.recv(512).decode("utf-8")
        if data != "":
            print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " -> " + data)
        return data

    def send(self, data: str, is_error: bool = False):
        code = "OK" if not is_error else "ERR"
        sending_data = code + " " + data
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " <- " + sending_data)
        self.request.send(sending_data.encode())


class ThrClientManagementServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
