import socket
import threading
import errno
import time
HEADER_LENGTH = 10

# initialising the server socket
IP = "127.0.0.1"
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP, PORT))

server_socket.listen()
server_socket.setblocking(1)
print(f'Listening for connections on {IP}:{PORT}...')

# Creating Groups
Army = ["Army" + str(i) for i in range(1, 51)]
Army.append("ArmyGeneral")
Army.append("ChiefCommander")
Navy = ["Navy" + str(i) for i in range(1, 51)]
Navy.append("NavyMarshal")
Navy.append("ChiefCommander")
AirForce = ["AirForce" + str(i) for i in range(1, 51)]
AirForce.append("AirForceChief")
AirForce.append("ChiefCommander")
Chiefs = ["ArmyGeneral", "AirForceChief", "NavyMarshal", "ChiefCommander"]

clients = {}
clients_list = []

# creating TO_SEND
TO_SEND = {name: [] for name in Army + Navy + AirForce}

# Accepting connections continuously

def accept_connection():
    while True:
        connection, address = server_socket.accept()
        connection.setblocking(0)
        user_header = connection.recv(HEADER_LENGTH)
        if not len(user_header):
            return False
        user_name_len = int(user_header.decode("utf-8").strip())
        user_name = connection.recv(user_name_len).decode("utf-8")
        clients[connection] = user_name
        clients[user_name] = connection
        clients_list.append(connection)
        if TO_SEND[user_name]:
            for massage in TO_SEND[user_name]:
                text = f"{len(massage[0]):<{HEADER_LENGTH}}{massage[0]}{len(massage[1]):<{HEADER_LENGTH}}{massage[1]}"
                connection.send(text.encode())
            TO_SEND[user_name].clear()
        print(f"new connection established with {address[0]}:{address[1]} : username - {user_name}")
        print(f"Total active users: {len(clients_list)}")


accept_connections = threading.Thread(target=accept_connection)
accept_connections.start()


# Handles message receiving and del dead clients

def receive_message(client_socket):
    try:
        user_header = client_socket.recv(HEADER_LENGTH)
        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if user_header == -1:
            return False
        if not len(user_header):
            return "CLIENT NOT AVAILABLE"

        # Convert header to int value
        user_len = int(user_header.decode('utf-8').strip())
        sender = client_socket.recv(user_len).decode("utf-8")
        text_len = int(client_socket.recv(HEADER_LENGTH).decode("utf-8").strip())
        text = client_socket.recv(text_len).decode("utf-8")
        if text == "GET_HISTORY":
            return text
        # Return an object of message header and message data
        massage = [sender, text]
        print(f"message receaved: {massage}")
        return massage

    except IOError as e:
        if e.errno == errno.EAGAIN and e.errno == errno.EWOULDBLOCK:
            return False
        else:
            print('Reading error: {}'.format(str(e)))
            return "CLIENT NOT AVAILABLE"

def get_group(user):
    if "ArmyGeneral" in user:
        return set(Army+Chiefs)
    elif "Army" in user:
        return set(Army)
    elif "NavyMarshal" in user:
        return set(Navy + Chiefs)
    elif "Navy" in user:
        return set(Navy)
    elif "AirForceChief" in user:
        return set(AirForce + Chiefs)
    elif "AirForce" in user:
        return set(AirForce)
    else:
        return set(Chiefs)


def send_history(client):
    file = clients[client] + ".txt"
    massage = []
    massage.append("CHAT_HISTORY")
    massage.append(open(file, 'r').read())
    text = f"{len(massage[0]):<{HEADER_LENGTH}}{massage[0]}{len(massage[1]):<{HEADER_LENGTH}}{massage[1]}"
    client.send(text.encode())


while True:
    for client in clients_list:
        massage = receive_message(client)
        user = clients[client]
        if massage == "CLIENT NOT AVAILABLE":
            clients_list.remove(client)
            del clients[client]
            del clients[user]
        elif massage == "GET_HISTORY":
            send_history(client)
        elif massage:
            with open(f"{clients[client]}.txt", 'a') as file1:
                file1.write(f"\n{time.strftime('%Y-%m-%d-%H.%M.%S', time.localtime())}\t{massage[0]}\t{massage[1]}")
            for member in get_group(user):
                with open(f"{member}.txt", 'a') as file1:
                    file1.write(f"\n{time.strftime('%Y-%m-%d-%H.%M.%S', time.localtime())}\t{massage[0]}\t{massage[1]}")
                if member in clients:
                    if client != clients[member]:
                        text = f"{len(massage[0]):<{HEADER_LENGTH}}{massage[0]}{len(massage[1]):<{HEADER_LENGTH}}{massage[1]}"
                        clients[member].send(text.encode())
                else:
                    # save to TO_SEND
                    TO_SEND[member].append(massage)
                                
