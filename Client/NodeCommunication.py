import socket
import threading
import time


class NodeClient():
    def __init__(self, ip, port):
        self.node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port

    def initiate(self):
        self.node_socket.connect((self.ip, self.port))
        print("Connected to Node.")

    def interactive(self):
        # Starting receiving data
        receive_thread = threading.Thread(target=self.listen)
        receive_thread.setDaemon(True)
        receive_thread.start()

        # Starting input infinite loop
        while True:
            user_input = input("Client : ")
            if user_input == "quit":
                print("Exiting")
                self.node_socket.close()
                raise SystemExit
            if user_input == "lorem":
                user_input = "Morbinecnibhsitametnullamaximusdapibus.Duisnullaturpis,dapibussitametornaresitamet,elementumutnunc.Utatcursusnulla.Phasellusurnami,maximusegetjustoquis,vestibuluminterdumenim.Nullamvelquamsedexelementumconvallisutvitaedui.Morbieumolestiedolor.Integermaximusurnavelsemvehicula,acfacilisisfelisbibendum.Pellentesquerutrum,nibhaegestasporttitor,purusjustofermentumex,fermentumornareexauguevelante.Curabiturneclectusmaximus,tinciduntsemac,gravidaenim.Pellentesqueinauguevelliberorhoncusvestibulum.Craspharetralaoreettortorapretium.Vestibulumfinibussemacrisusdignissim,necfacilisisarcuplacerat.Duistempor,sapieninaliquamaliquam,magnaleopretiumneque,facilisisdictumnulladuiiderat.Morbinecnibhsitametnullamaximusdapibus.Duisnullaturpis,dapibussitametornaresitamet,elementumutnunc.Utatcursusnulla.Phasellusurnami,maximusegetjustoquis,vestibuluminterdumenim.Nullamvelquamsedexelementumconvallisutvitaedui.Morbieumolestiedolor.Integermaximusurnavelsemvehicula,acfacilisisfelisbibendum.Pellentesquerutrum,nibhaegestasporttitor,purusjustofermentumex,fermentumornareexauguevelante.Curabiturneclectusmaximus,tinciduntsemac,gravidaenim.Pellentesqueinauguevelliberorhoncusvestibulum.Craspharetralaoreettortorapretium.Vestibulumfinibussemacrisusdignissim,necfacilisisarcuplacerat.Duistempor,sapieninaliquamaliquam,magnaleopretiumneque,facilisisdictumnulladuiiderat.Morbinecnibhsitametnullamaximusdapibus.Duisnullaturpis,dapibussitametornaresitamet,elementumutnunc.Utatcursusnulla.Phasellusurnami,maximusegetjustoquis,vestibuluminterdumenim.Nullamvelquamsedexelementumconvallisutvitaedui.Morbieumolestiedolor.Integermaximusurnavelsemvehicula,acfacilisisfelisbibendum.Pellentesquerutrum,nibhaegestasporttitor,purusjustofermentumex,fermentumornareexauguevelante.Curabiturneclectusmaximus,tinciduntsemac,gravidaenim.Pellentesqueinauguevelliberorhoncusvestibulum.Craspharetralaoreettortorapretium.Vestibulumfinibussemacrisusdignissim,necfacilisisarcuplacerat.Duistempor,sapieninaliquamaliquam,magnaleopretiumneque,facilisisdictumnulladuiiderat.Morbinecnibhsitametnullamaximusdapibus.Duisnullaturpis,dapibussitametornaresitamet,elementumutnunc.Utatcursusnulla.Phasellusurnami,maximusegetjustoquis,vestibuluminterdumenim.Nullamvelquamsedexelementumconvallisutvitaedui.Morbieumolestiedolor.Integermaximusurnavelsemvehicula,acfacilisisfelisbibendum.Pellentesquerutrum,nibhaegestasporttitor,purusjustofermentumex,fermentumornareexauguevelante.Curabiturneclectusmaximus,tinciduntsemac,gravidaenim.Pellentesqueinauguevelliberorhoncusvestibulum.Craspharetralaoreettortorapretium.Vestibulumfinibussemacrisusdignissim,necfacilisisarcuplacerat.Duistempor,sapieninaliquamaliquam,magnaleopretiumneque,facilisisdictumnulladuiiderat.Morbinecnibhsitametnullamaximusdapibus.Duisnullaturpis,dapibussitametornaresitamet,elementumutnunc.Utatcursusnulla.Phasellusurnami,maximusegetjustoquis,vestibuluminterdumenim.Nullamvelquamsedexelementumconvallisutvitaedui.Morbieumolestiedolor.Integermaximusurnavelsemvehicula,acfacilisisfelisbibendum.Pellentesquerutrum,nibhaegestasporttitor,purusjustofermentumex,fermentumornareexauguevelante.Curabiturneclectusmaximus,tinciduntsemac,gravidaenim.Pellentesqueinauguevelliberorhoncusvestibulum.Craspharetralaoreettortorapretium.Vestibulumfinibussemacrisusdignissim,necfacilisisarcuplacerat.Duistempor,sapieninaliquamaliquam,magnaleopretiumneque,facilisisdictumnulladuiiderat.2"
            self.send(user_input)
            time.sleep(0.2)

    def send(self, msg: str):
        lenght = len(msg.encode())
        # On préfixe les données avec leur indication de taille
        data = str(lenght) + ":" + msg
        self.node_socket.send(data.encode())

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
    def receive(self):
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
