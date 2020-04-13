import socket
import socketserver
import threading


class ThrClientManagementRequestHandler(socketserver.BaseRequestHandler):
    request: socket

    def __init__(self, request, client_address, node_server):
        self.client = None
        self.client_identity = None
        self.client_thread: threading.Thread = threading.current_thread()
        super().__init__(request, client_address, node_server)

    # Point d'entrée de chaque connexion client établie
    def handle(self):
        # Si le client n'envoie rien pendant 12 secondes on considère qu'il a timeout (et Client raise ClientTimeout)
        self.request.settimeout(12)
        # Un nouveau client est connecté :
        from Node.ClientMgmt import Client, ClientDisconnected
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " connected.")

        # Boucle de gestion du client (ne s'arrête que lorsque le client se déconnecte)
        try:
            self.client = Client(self)
        except ClientDisconnected:
            pass
        # On retourne lorsque le client a terminé
        return

    def finish(self):
        print(str(threading.currentThread().getName()) + " " + str(self.client_identity) + " " + str(
            self.client_address) + " is now offline.")
        del self.client
        # Suppression du client dans la liste :
        from Node.ClientMgmt import Client
        Client.del_client(self.client_identity)
        super().finish()

    # On reçoit les données en prenant en compte leur taille
    def receive(self):
        length = None
        buffer = data = message = b""
        receiving = True
        # Tant que on a pas tout reçu :
        while receiving:
            # On reçoit de nouvelle données
            data += self.request.recv(2048)
            if not data:
                return None
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

        full_message = message

        # print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " -> " + str(message))
        return full_message

    def send(self, data: bytes):
        full_data = str(len(data)).encode() + b":" + data
        self.request.send(full_data)


class ThrClientManagementServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # address_family = socket.AF_INET6

    def handle_error(self, request, client_address):
        super().handle_error(request, client_address)

    socketserver.ThreadingMixIn.daemon_threads = True
