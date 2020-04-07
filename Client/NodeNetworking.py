import socket
import threading
import time
from base64 import b64encode

from Crypto.PublicKey.RSA import RsaKey

from Client.CryptoHandler import CryptoHandler
from Client.DbManager import ServerModel
from Client.Singleton import Singleton


class NodeClient():
    def __init__(self, ip, port):
        self.node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.server_key = None
        self.server_key_str = None

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
                # On stocke la clé publique du serveur sous forme de RsaKey mais aussi sous forme de String base64
                self.server_key_str: str = data.split()[2]
                self.server_key: RsaKey = ch.to_rsa(self.server_key_str)
            if data.split()[1] == "SERVER-AUTH":
                server_authenticator = data.split()[2]
                break

        if ch.check_authenticator(self.server_key, server_authenticator):
            print("Node public key matches authentication challenge")
        else:
            print("FATAL ERROR : NODE HIJACKING DETECTED. EXITING NOW...")
            raise SystemExit

        # Vérif. adresse du serveur au cas où on le connaisse déjà
        check_server: ServerModel = ServerModel.get_or_none(ServerModel.address == self.ip)
        # Si le serveur est inconnu
        if not check_server:
            # On sauvegarde son identité dans la Db
            print("Server " + self.ip + " unknown. Saving server identity...")
            ServerModel.create(address=self.ip, public_key=self.server_key_str)
        # Si le serveur est connu et que sa clé enregistrée ne correspond PAS à la clé qu'il envoie
        elif check_server.public_key != self.server_key_str:
            print(
                "WARNING ! NODE IDENTITY HAS CHANGED ! This may be due to a man-in-the-middle attack. Proceed with "
                "care. Contact server owner if needed.")
            # On demande à l'utilisateur si il veut sauvegarder la nouvelle identité du serveur
            if input("Save new identity and connect ? [y/N] ") == "y":
                check_server.public_key = self.server_key_str
                check_server.save()
                print("Saving node identity")
            else:
                print("Exiting...")
                raise SystemExit
        # Si le serveur enregistré correspond au serveur auquel on se connecte actuellement
        else:
            print("Node " + self.ip + " authenticated, sending client identity...")

        # Authenticating client
        self.send("CLIENT-KEY " + ch.str_public_key)

        # Envoi de l'authenticator
        self.send("CLIENT-AUTH " + ch.get_authenticator())

        print("")

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
