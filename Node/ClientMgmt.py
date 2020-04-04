from Node.ClientMgmtServer import ThrClientManagementRequestHandler


class Client:
    def __init__(self, comm_handler: ThrClientManagementRequestHandler):
        self.comm_handler = comm_handler
        self.address = comm_handler.client_address

    def get_request(self):
        self.comm_handler.request.recv(1024)