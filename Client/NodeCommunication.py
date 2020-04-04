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
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.setDaemon(True)
        receive_thread.start()

        # Starting input infinite loop
        while True:
            user_input = input("Client : ")
            self.node_socket.send(user_input.encode())
            if user_input == "quit":
                print("Exiting")
                self.node_socket.close()
                raise SystemExit
            time.sleep(0.2)

    def receive(self):
        while True:
            try:
                data: str = self.node_socket.recv(1024).decode("utf-8")
                print("Node : " + data)
                # On process les données reçues par le client
                if not data:
                    self.node_socket.close()
                    print("Node closed connection. Exiting...")
                    raise SystemExit
            except OSError:
                pass


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
