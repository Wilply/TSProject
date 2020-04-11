import hashlib
import threading
from base64 import b64decode, b64encode

from Crypto.PublicKey.RSA import RsaKey
from func_timeout import func_set_timeout, FunctionTimedOut

from Node.ClientNetworking import ThrClientManagementRequestHandler
from Node.CryptoHandler import CryptoHandler
from Node.Utils import Singleton


class ClientDisconnected(Exception):
    pass


class ClientAuthError(Exception):
    pass


class ClientSessionExchangeError(Exception):
    pass


class Client:
    client_identity: str
    # noinspection PyCallByClass,PyCallByClass
    crypto_handler: CryptoHandler = Singleton.Instance(CryptoHandler)

    def __init__(self, comm_handler: ThrClientManagementRequestHandler):
        self.comm_handler: ThrClientManagementRequestHandler = comm_handler
        self.client_address = comm_handler.client_address
        self.client_identity = ""
        self.client_key_str = None
        self.client_key = None
        self.session_key = None

        # Envoi de la bannière de bienvenue
        self.comm_handler.send("WELCOME TSProject node, listening")

        # Envoi de la clé publique du serveur
        self.comm_handler.send("SERVER-KEY " + Client.crypto_handler.str_public_key)

        # Envoi de l'authenticator
        self.comm_handler.send("SERVER-AUTH " + self.crypto_handler.get_authenticator())

        # Lancement de la phase de négociation de clé de session. Timeout de 5 sec
        try:
            self.client_crypto_exchange()
        except (Exception, FunctionTimedOut):
            raise ClientSessionExchangeError

        # Lancement de la phase d'authentification du client. Timeout de 5 sec
        try:
            self.client_auth()
        except (Exception, FunctionTimedOut):
            raise ClientAuthError

        # Lancement de la boucle d'écoute des commandes client
        self.main_loop()

    @func_set_timeout(5)
    def client_crypto_exchange(self):
        while True:
            data = self.listen_wait(False).decode()
            if data.split()[0] == "SESSION-KEY":
                break
            else:
                self.comm_handler.send("SESSION-NEEDED Please send session key", True)
        self.session_key = self.crypto_handler.decrypt_rsa(b64decode(data.split()[1]))
        print("Session key : " + str(b64encode(self.session_key)))
        self.comm_handler.send("SESSION-OK Session key exchange successful")

    @func_set_timeout(5)
    def client_auth(self):
        # On attend que le client envoie ses infos d'authentification
        while True:
            data = self.listen_wait(False).decode()
            if data.split()[0] == "CLIENT-KEY":
                break
            else:
                self.comm_handler.send("KEY-NEEDED Please send public key", True)

        self.client_key_str = data.split()[1]
        self.client_key: RsaKey = self.crypto_handler.to_rsa(self.client_key_str)

        while True:
            data = self.listen_wait(False).decode()
            if data.split()[0] == "CLIENT-AUTH":
                break
            else:
                self.comm_handler.send("AUTH-NEEDED Please auth", True)

        client_authenticator = data.split()[1]

        # Si le client est bien qui il prétend être
        if self.crypto_handler.check_authenticator(self.client_key, client_authenticator):
            self.client_identity: str = hashlib.sha1(self.client_key.export_key(format="DER")).hexdigest()
            self.comm_handler.send("AUTH-OK Successfully authenticated, welcome " + self.client_identity)
            self.print_debug("authenticated")
        else:
            self.comm_handler.send("AUTH-ERROR Authentication error, wrong identity. Closing.")
            raise Exception

    def do_hello(self, data):
        self.comm_handler.send("Hello user ! You said " + data)

    def do_whoami(self, data):
        self.comm_handler.send("You are " + self.client_identity)

    def do_quit(self, data):
        pass

    def do_unknown_command(self):
        self.comm_handler.send("Unknown command", True)

    def main_loop(self):

        function_switcher = {
            "hello": self.do_hello,
            "whoami": self.do_whoami,
            "quit": self.do_quit,
        }
        while True:
            data = self.listen_wait().decode()
            # On redirige vers la fonction correspondant à la commande
            main_command = data.split()[0]
            function_call = function_switcher.get(main_command)
            if main_command == "hello":
                function_call(data)
            else:
                self.do_unknown_command()

    # TODO : afficher dans les logs le texte déchiffré au lieu de chiffré
    # TODO : chiffrer le sens Node => Client
    # TODO : créer une méthode send qui chiffre avant d'envoyer à ClientNetworking
    def listen_wait(self, is_encrypted: bool = True) -> bytes:
        try:
            # On attend que le client envoie quelque chose et on renvoie cette valeur
            data: bytes = self.comm_handler.receive()
            # Si le socket n'envoie plus rien, alors le client est déconnecté
            if not data or data == "":
                raise ClientDisconnected()
            # Si on s'attend à des données chiffrées, alors on les déchiffre avec clé de session et un décode base64
            if is_encrypted:
                data: bytes = self.crypto_handler.decrypt(data, self.session_key)
            return data
        except OSError:
            pass

    def print_debug(self, msg: str):
        print(str(self) + " : " + msg)

    def __str__(self):
        return "Client " + str(threading.currentThread().getName()) + " " + str(
            self.client_address) + " " + self.client_identity
