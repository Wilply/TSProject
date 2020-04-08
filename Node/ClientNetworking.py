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
        from Node.ClientMgmt import Client, ClientDisconnected, ClientAuthError, ClientAuthTimeout
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " connected.")

        # Boucle de gestion du client
        try:
            self.client = Client(self)
        except ClientAuthError:
            print(str(threading.currentThread().getName()) + " " + str(
                self.client_address) + " did not pass authentication checks. Stopping connection...")
        except ClientAuthTimeout:
            print(str(threading.currentThread().getName()) + " " + str(
                self.client_address) + " timed out during authentication. Stopping connection...")
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

        full_str = message.decode()

        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " -> " + str(message))
        return full_str

    def send(self, data, is_error: bool = False):
        code: bytes = b"OK" if not is_error else b"ERR"
        if type(data) == str:
            data = data.encode()
        prefixed_data: bytes = code + b" " + data
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " <- " + str(prefixed_data))

        lenght = len(prefixed_data)
        # On préfixe les données avec leur indication de taille
        full_data = str(lenght).encode() + b":" + prefixed_data
        self.request.send(full_data)


class ThrClientManagementServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    socketserver.ThreadingMixIn.daemon_threads = True
    pass
