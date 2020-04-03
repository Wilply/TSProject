import socket


class NodeClient():
    def __init__(self, ip, port):
        self.node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port

    def initiate(self):
        self.node_socket.connect((self.ip, self.port))
        print("Connected to Node.")

    def interactive(self):
        while True:
            user_input = input("Client : ")
            self.node_socket.send(user_input.encode())
            print("Node : " + self.node_socket.recv(1024).decode("utf-8"))
            if user_input == "quit":
                print("Exiting")
                self.node_socket.close()
                raise SystemExit


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
