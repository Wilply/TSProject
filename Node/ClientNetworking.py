import socketserver
import struct
import sys
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

    # Receive adaptative size
    def receive(self):
        length = None
        buffer = data = message = b""
        receiving = True
        # Tant que on a pas tout reçu :
        while receiving:
            # On reçoit de nouvelle données
            data += self.request.recv(2048)
            if not data:
                break
            buffer += data
            while True:
                if length is None:
                    if b':' not in buffer:
                        break
                    # On récupère la taille du message
                    length_str, ingnored, buffer = buffer.partition(b':')
                    length = int(length_str)
                if len(buffer) == length:
                    receiving = False
                message = buffer[:length]
                buffer = buffer[length:]
                length = None

        full_message = message.decode()

        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " -> " + full_message)
        return full_message

    def send(self, data: str, is_error: bool = False):
        code = "OK" if not is_error else "ERR"
        prefixed_data = code + " " + data
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " <- " + prefixed_data)

        lenght = len(prefixed_data.encode())
        # On préfixe les données avec leur indication de taille
        full_data = str(lenght)+":"+prefixed_data
        self.request.send(full_data.encode())


class ThrClientManagementServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
