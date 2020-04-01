import socket
import threading

class EntryServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.socket.bind((self.host, self.port))

    def start(self):
        thread = threading.Thread(target=self.listen)
        thread.daemon = True
        thread.start()

    def listen(self):
        self.socket.listen(5)
        while True:
            client, address = self.socket.accept()
            client.settimeout(5)
            threading.Thread(target=ClientThread, args=(client, address)).start()


class ClientThread(object):
    clientsList = []

    def __init__(self, client, address):
        self.client = client
        self.address = address
        self.clientsList.append(self)
        print("Client connected ! " + str(address))

    def __str__(self):
        return str(self.address)

    def handle_client(self):
        size = 1024
        while True:
            try:
                data = self.client.recv(size)
                if data:
                    if data.decode("utf-8") == "quit":
                        self.client.close()
                    print(str(self.address) + " says : " + data.decode("utf-8"))
                    response = data
                    self.client.send(response)
                else:
                    print("Client disconnected : " + self.client)
                    self.clientsList.remove(self)
            except:
                self.client.close()
                self.clientsList.remove(self)
                return False
