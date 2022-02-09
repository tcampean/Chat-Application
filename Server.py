

import socket, threading, select,pickle,struct


def server():
    listening_sock = socket.create_server(('', 10000))
    listening_sock.listen()
    clients = {}
    select_sockets_list = [listening_sock]

    while True:

        slist, _, _  = select.select(select_sockets_list, [], [])
        for sock in slist:
            if sock == listening_sock:
                client_socket, (client_ip,_) = listening_sock.accept()
                client_socket.sendall(struct.pack("!I", len(clients)))
                for client in clients:
                    client_data = clients[client]
                    client_sending = pickle.dumps(client_data)
                    client_socket.sendall(client_sending)
                    if client_socket.recv(1) == b'S':
                        print("Client received!")
                    else:
                        print("Sending Error")


                new_client = pickle.loads(client_socket.recv(1024))
                print("New client connected",new_client[0],client_ip)

                for other_client_socket in clients:
                    other_client_socket.send(b'N')
                    client_send = (new_client[0],client_ip,new_client[2])
                    client_sending = pickle.dumps(client_send)
                    other_client_socket.sendall(client_sending)

                good_client = (new_client[0], client_ip, new_client[2])
                clients[client_socket] = good_client
                select_sockets_list.append(client_socket)

            else:
                operation = sock.recv(1)
                if operation == b'L':
                    print("Client is leaving...")
                    sock.close()
                    deleted_client = clients[sock]
                    del clients[sock]
                    select_sockets_list.remove(sock)

                    for other_client_socket in clients:
                        other_client_socket.send(b'L')
                        other_client_socket.send(deleted_client[0])
                        other_client_socket.send(struct.pack("!H", deleted_client[1]))




if __name__ == "__main__":
    threading.Thread(target=server, daemon=True).start()

    while True:
        user_input = input()
        if user_input == "Q":
            print("Shutting down...")
            exit(0)