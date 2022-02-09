import datetime
import socket,struct,pickle,threading,select,datetime


def communication():
    try:
        while True:
            sockets, _, _ = select.select([self_tcp_socket, self_udp_socket], [], [])
            if self_tcp_socket in sockets:
                operation = self_tcp_socket.recv(1)
                if operation == b'/':
                    print("You have been disconnected")
                    return
                new_client = pickle.loads(self_tcp_socket.recv(1024))
                if operation == b'N':
                    print(new_client[0], 'has connected to the chat')
                    other_clients.add(new_client)
                elif operation == b'L':
                    print(new_client[0], 'has left the chat')
                    other_clients.discard(new_client)
                else:
                    print('Unknown operation received')

            if self_udp_socket in sockets:
                message = pickle.loads(self_udp_socket.recv(256))
                print('[',str(datetime.datetime.now().strftime('%X')),']',message[0],': ',message[1])
    except OSError as o:
        self_tcp_socket.close()
        self_udp_socket.close()
        print("Error")
        return


if __name__ == "__main__":

    self_tcp_socket = socket.socket()
    self_tcp_socket.connect(('127.0.0.1', 10000))


    name = input("Enter your name: ")

    number_of_clients = struct.unpack("!I", self_tcp_socket.recv(4))[0]
    other_clients = set()
    for _ in range(number_of_clients):
        clientrecv = self_tcp_socket.recv(4094)
        client = pickle.loads(clientrecv)
        other_clients.add(client)
        self_tcp_socket.send(b'S')
    self_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    self_udp_socket.sendto(b'random', ('8.8.8.8', 2355))

    _, self_udp_port = self_udp_socket.getsockname()
    print("My UDP port is:", str(self_udp_port))

    me = (name,'',self_udp_port)
    new_me = pickle.dumps(me)
    self_tcp_socket.sendall(new_me)

    threading.Thread(target=communication, daemon=True).start()

    while True:

        user_input = input()
        if user_input == "Q":
            self_tcp_socket.send(b'L')
            print("Leaving the chat room and shutting down...")
            self_tcp_socket.close()
            self_udp_socket.close()
            exit(0)
        for other_client in other_clients:
            package = (name,user_input)
            package_send = pickle.dumps(package)
            self_udp_socket.sendto(package_send, (other_client[1],other_client[2]))