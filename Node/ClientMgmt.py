import threading
from base64 import b64encode

from Node.ClientNetworking import ThrClientManagementRequestHandler
from Node.CryptoHandler import Singleton, CryptoHandler


class ClientDisconnected(Exception):
    pass


class Client:
    crypto_handler: CryptoHandler = Singleton.Instance(CryptoHandler)

    def __init__(self, comm_handler: ThrClientManagementRequestHandler):
        self.comm_handler: ThrClientManagementRequestHandler = comm_handler
        self.address = comm_handler.client_address
        self.identity: str = ""

        # Envoi de la bannière de bienvenue
        self.comm_handler.send("WELCOME TSProject node, listening")

        # Envoi de la clé publique du serveur
        self.comm_handler.send("SERVER-KEY "+Client.crypto_handler.str_public_key)

        # Lancement de la phase d'authentification client-serveur
        self.auth()

        # Démarrage boucle d'écoute une fois le client authentifié
        while True:
            data = self.listen_wait()

            # On redirige vers la fonction correspondant à la commande
            main_command = data.split()[0]
            function_call = self.function_switcher.get(main_command)
            if function_call:
                function_call(self, data)
            else:
                self.do_unkown_command(data)

    def auth(self):
        # On attend que le client demande de s'authentifier "auth"
        while self.listen_wait().split()[0] != "auth":
            self.comm_handler.send("AUTH-NEEDED Please authenticate", True)
        self.comm_handler.send("AUTH-OK Successfully authenticated, welcome")
        self.print_debug("authenticated")
        pass

    def listen_wait(self) -> str:
        try:
            # On attend que le client envoie quelque chose et on renvoie cette valeur
            data: str = self.comm_handler.receive()
            if not data or data == "":
                raise ClientDisconnected()
            return data
        except OSError:
            pass

    def print_debug(self, msg: str):
        print(str(self) + " : " + msg)

    def do_hello(self, data):
        self.comm_handler.send("Hello user ! You said " + data)

    def do_unkown_command(self, data):
        self.comm_handler.send("Unknown command", True)

    def do_quit(self, data):
        pass

    def __str__(self):
        return "Client " + str(threading.currentThread().getName()) + " " + str(self.address) + self.identity

    function_switcher = {
        "hello": do_hello,
        "quit": do_quit
    }
