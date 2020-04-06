import socket
import threading
import time
from base64 import b64encode

from Crypto.PublicKey.RSA import RsaKey

from Client.CryptoHandler import Singleton, CryptoHandler


class NodeClient():
    def __init__(self, ip, port):
        self.node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.server_key = None

    def initiate(self):
        self.node_socket.connect((self.ip, self.port))
        print("Connected to Node.")

    def interactive(self):

        # Starting auth loop
        while True:
            data = self.receive()
            if data.split()[1] == "WELCOME":
                print("Node banner : " + " ".join(data.split()[2:]))
            if data.split()[1] == "SERVER-KEY":
                self.server_key: RsaKey = ch.to_rsa(data.split()[2])
            if data.split()[1] == "SERVER-AUTH":
                server_authenticator = data.split()[2]
                break

        if ch.check_authenticator(self.server_key, server_authenticator):
            print("Node identity check : pass")
        else:
            print("FATAL ERROR : NODE HIJACKING DETECTED. EXITING NOW...")
            raise SystemExit

        # Starting normal communication
        receive_thread = threading.Thread(target=self.listen)
        receive_thread.setDaemon(True)
        receive_thread.start()

        time.sleep(0.5)

        # Starting input infinite loop
        while True:
            user_input = input("Client : ")
            if user_input == "quit":
                print("Exiting")
                self.node_socket.close()
                raise SystemExit
            self.send(user_input)
            time.sleep(0.2)

    def send(self, data):
        if type(data) == str:
            data = data.encode()

        lenght = len(data)
        # On préfixe les données avec leur indication de taille
        full_data = str(lenght).encode() + b":" + data
        self.node_socket.send(full_data)

    def listen(self):
        while True:
            try:
                data: str = self.receive()
                print("Node : " + data)
                # On process les données reçues par le node
                if not data:
                    self.node_socket.close()
                    print("Node closed connection. Exiting...")
                    raise SystemExit
            except OSError:
                pass

    # noinspection DuplicatedCode
    def receive(self) -> str:
        length = None
        buffer = data = message = b""
        receiving = True
        # Tant que on a pas tout reçu :
        while receiving:
            # On reçoit de nouvelle données
            data += self.node_socket.recv(2048)
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

        return full_message


if __name__ == '__main__':
    # Init CryptoHandler
    ch: CryptoHandler = Singleton.Instance(CryptoHandler)
    print("Identity : " + ch.identity)
    print("Simple TCP client starting...")
    ip = input("IP address of server [127.0.0.1] : ")
    port = input("TCP port of server [37405] : ")
    if not ip:
        ip = "127.0.0.1"
    if not port:
        port = 37405

    node = NodeClient(ip, port)
    try:
        node.initiate()
        node.interactive()
    except ConnectionRefusedError:
        print("Cannot connect to server. Exiting.")
        raise SystemExit
