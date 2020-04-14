import hashlib
import socket
import threading
import time
import weakref
from base64 import b64decode, b64encode
from datetime import datetime

from Crypto.PublicKey.RSA import RsaKey
from func_timeout import func_set_timeout, FunctionTimedOut

from ClientNetworking import ThrClientManagementRequestHandler
from CryptoHandler import CryptoHandler
from DbManager import ClientModel
from Utils import Singleton


class ClientDisconnected(Exception):
    pass


class Client:
    client_identity: str
    # noinspection PyCallByClass,PyCallByClass
    crypto_handler: CryptoHandler = Singleton.Instance(CryptoHandler)
    __instances = {}

    @staticmethod
    def get_client(client_identity: str):
        try:
            return Client.__instances[client_identity]
        except KeyError:
            return None

    @staticmethod
    def get_client_key(client_identity: str):
        try:
            client: ClientModel = ClientModel.get_or_none(ClientModel.identity == client_identity)
            return client.public_key
        except KeyError:
            return None

    @staticmethod
    def del_client(client_identity: str):
        if client_identity in Client.__instances:
            Client.__instances.pop(client_identity)

    @staticmethod
    def list_clients():
        print("Authenticated clients list :")
        for client in Client.__instances:
            print("- " + client)

    @staticmethod
    def kill_all_clients():
        for client in Client.__instances:
            Client.get_client(client).close("server terminated all connections")

    @staticmethod
    def clients_count():
        return len(Client.__instances)

    def __init__(self, comm_handler: ThrClientManagementRequestHandler):
        self.comm_handler: ThrClientManagementRequestHandler = comm_handler
        self.client_address = comm_handler.client_address
        self.client_identity = ""
        self.client_key_str = None
        self.client_key = None
        self.session_key = None
        self.__inbox_queue = []
        self.thread = threading.current_thread()

        # Envoi de la bannière de bienvenue
        self.send("WELCOME TSProject node, listening", is_encrypted=False)

        # Envoi de la clé publique du serveur
        self.send("SERVER-KEY " + Client.crypto_handler.str_public_key, is_encrypted=False)

        # Envoi de l'authenticator
        self.send("SERVER-AUTH " + self.crypto_handler.get_authenticator(), is_encrypted=False)

        # Lancement de la phase de négociation de clé de session. Timeout de 5 sec
        try:
            self.client_crypto_exchange()
        except (Exception, FunctionTimedOut):
            self.close("error during session encryption key exchange")

        # A partir de ce point, tous les échanges sont chiffrés avec la clé de session

        # Lancement de la phase d'authentification du client. Timeout de 5 sec
        try:
            self.client_auth()
        # except (Exception, FunctionTimedOut):
        except FunctionTimedOut:
            self.close("client authentication timed out")

        # Lancement de la boucle d'écoute des commandes client
        thr_main = threading.Thread(target=self.main_loop)
        thr_main.setDaemon(True)
        thr_main.start()

        # Lancement de la boucle d'écoute des commandes internes
        self.inbox_listener()

    # Inbox listener récupère les commandes envoyées par d'autres thread puis les fait éxecuter par le thread
    # du client. Cela permet d'être thread-safe ainsi que de raise les exceptions au bon endroit.
    def inbox_listener(self):
        while True:
            for event in self.__inbox_queue:
                self.print_debug("processing inbox : " + str(event))
                if event[0] == "close":
                    self.__inbox_queue.remove(event)
                    self.close(event[1])
            time.sleep(0.2)

    @func_set_timeout(5)
    def client_crypto_exchange(self):
        while True:
            data = self.listen_wait(False).decode()
            if data.split()[0] == "SESSION-KEY":
                break
            else:
                self.send("SESSION-NEEDED Please send session key", True, False)
        self.session_key = self.crypto_handler.decrypt_rsa(b64decode(data.split()[1]))
        print("Session key : " + str(b64encode(self.session_key)))
        self.send("SESSION-OK Session key exchange successful", is_encrypted=False)

    @func_set_timeout(7)
    def client_auth(self):
        # On attend que le client envoie ses infos d'authentification
        while True:
            data = self.listen_wait().decode()
            if data.split()[0] == "CLIENT-KEY":
                break
            else:
                self.send("KEY-NEEDED Please send public key", True)

        self.client_key_str = data.split()[1]
        self.client_key: RsaKey = self.crypto_handler.to_rsa(self.client_key_str)

        while True:
            data = self.listen_wait().decode()
            if data.split()[0] == "CLIENT-AUTH":
                break
            else:
                self.send("AUTH-NEEDED Please auth", True)

        client_authenticator = data.split()[1]

        # Si le client est bien qui il prétend être
        if self.crypto_handler.check_authenticator(self.client_key, client_authenticator):
            self.client_identity: str = hashlib.sha1(self.client_key.export_key(format="DER")).hexdigest()
            self.comm_handler.client_identity = self.client_identity
            self.send("AUTH-OK Successfully authenticated, welcome " + self.client_identity)
            # On vérifie que le client n'est pas déjà connecté
            existing_client: Client = Client.get_client(self.client_identity)
            # Si le client est déjà connecté, on ferme la connexion de l'ancien
            if existing_client:
                existing_client.close("connected from another place")
                self.send("ALREADY-CONNECTED You are logged in from another place. Killing old connection...")
                # Attente de la déconnexion de l'ancien client
                while True:
                    if self.client_identity not in self.__instances:
                        self.print_debug("old connection killed")
                        break
                    time.sleep(0.5)
            # Ajout du client à la liste des clients
            self.print_debug("authenticated")
            self.__instances[self.client_identity] = weakref.proxy(self)
            # Ajout du client à la base de données si il n'existe pas
            existing_db_client: ClientModel = ClientModel.get_or_none(ClientModel.identity == self.client_identity)
            if not existing_db_client:
                ClientModel.create(identity=self.client_identity, public_key=self.client_key_str,
                                   last_seen=datetime.timestamp(datetime.now()))
                self.print_debug("creating new client identity in database")
                self.send("NEW-CLIENT You are new on this node. Welcome.")
            else:
                existing_db_client.last_seen = datetime.timestamp(datetime.now())
                existing_db_client.save()
        else:
            self.send("AUTH-ERROR Authentication error, wrong identity. Closing.")
            raise Exception

    def do_hello(self, data):
        self.send("Hello user ! You said " + data)

    def do_whoami(self, data):
        self.send("You are " + self.client_identity)

    def do_quit(self, data):
        pass

    def do_get_key(self, data):
        client_key = Client.get_client_key(data.split()[1])
        if not client_key:
            self.send("CLIENT-UNKNOWN Client is not known from this node", is_error=True)
        else:
            self.send("GET-CLIENT-KEY " + data.split()[1] + " " + client_key)

    def do_get_status(self, data):
        client_identity_lookup = data.split()[1]
        client: Client = Client.get_client(client_identity_lookup)
        # Si le client est trouvé dans la liste des connectés actuels sur ce node :
        if client:
            self.send("GET-CLIENT-STATUS " + client_identity_lookup + " ONLINE")
        # Si le client n'est pas dans la liste des connectés, on regarde dans la db :
        else:
            client_db: ClientModel = ClientModel.get_or_none(ClientModel.identity == client_identity_lookup)
            # Si le client existe dans la db :
            if client_db:
                self.send("GET-CLIENT-STATUS " + client_identity_lookup + " OFFLINE " + str(client_db.last_seen))
            # Si le client n'existe pas dans la db :
            else:
                self.send("CLIENT-UNKNOWN Client is not known from this node", is_error=True)
        pass

    def do_unknown_command(self):
        self.send("Unknown command", True)

    def main_loop(self):

        function_switcher = {
            "hello": self.do_hello,
            "whoami": self.do_whoami,
            "get-key": self.do_get_key,
            "get-status": self.do_get_status,
            "quit": self.do_quit,
        }
        while True:
            data = self.listen_wait()
            if not data:
                break
            data = data.decode()
            # On redirige vers la fonction correspondant à la commande
            main_command = data.split()[0].lower()
            function_call = function_switcher.get(main_command)
            if function_call:
                function_call(data)
            else:
                self.do_unknown_command()

    def listen_wait(self, is_encrypted: bool = True) -> bytes:
        try:
            while True:
                # On attend que le client envoie quelque chose et on renvoie cette valeur
                data: bytes = self.comm_handler.receive()
                # Si le socket n'envoie plus rien, alors le client est déconnecté
                if not data or data == b'':
                    self.close("client left")
                    time.sleep(2)
                # Si la donnée reçue n'est pas un keepalive, on process (sinon on recommence la boucle)
                if data != b"keepalive":
                    # Si on s'attend à des données chiffrées, alors on les déchiffre avec clé de session et un décode
                    # base64
                    if is_encrypted:
                        data: bytes = self.crypto_handler.decrypt(data, self.session_key)
                        # Si les données chiffrées ne correspondent à rien, alors le client est déconnecté
                        if data == b'':
                            self.close("client left")
                        print(str(self) + " (E) -> " + str(data))
                    else:
                        print(str(self) + " -> " + str(data))
                    break
            return data
        # Si le socket timeout alors on ferme la connexion
        except socket.timeout:
            self.close("timed out")
        except ValueError:
            self.close("encryption error, received cleartext data while expecting encrytion")
        # Si on a une erreur de chiffrement ou de récupération de valeurs, on ferme immédiatement
        except (TypeError, AttributeError):
            pass

    def send(self, data, is_error: bool = False, is_encrypted: bool = True):
        code: bytes = b"OK" if not is_error else b"ERR"
        if type(data) == str:
            data = data.encode()
        prefixed_data: bytes = code + b" " + data

        if is_encrypted:
            print(str(self) + " (E) <- " + str(prefixed_data))
            prefixed_data = (self.crypto_handler.encrypt(prefixed_data, self.session_key))
        else:
            print(str(self) + " <- " + str(prefixed_data))

        self.comm_handler.send(prefixed_data)

    def close(self, message: str = "unknown"):
        # Si l'appel de close est réalisé depuis le thread du client, on raise l'exception et on ferme
        if self.thread == threading.current_thread():
            self.print_debug("connection closed (" + message + ")")
            self.send("DISCONNECTED Node closed connection : " + message, is_error=True)
            # On indique l'heure de dernière connexion du client dans la db
            existing_db_client: ClientModel = ClientModel.get_or_none(ClientModel.identity == self.client_identity)
            if existing_db_client:
                existing_db_client.last_seen = datetime.timestamp(datetime.now())
                existing_db_client.save()
            raise ClientDisconnected
        # Sinon, on ajoute le message dans l'inbox_queue pour que le thread du client le process
        else:
            self.__inbox_queue.append(("close", message))

    def print_debug(self, msg: str):
        print(str(self) + " : " + msg)

    def __str__(self):
        return str(self.client_address) + " " + str(self.client_identity) if self.client_identity else str(
            self.client_address)
