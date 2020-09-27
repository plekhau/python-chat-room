"""
Low-level functionality with sockets + global variables
"""
import socket
import sys

BUFFER_SIZE = 2048
DEFAULT_PORT = 8888
init_game_msg = "init_game"
stop_game_msg = "stop_game"

server_socket = None
sockets_list = {}
one_player_game_list = {}  # contains active one player games with their progresses if needed
all_player_game = {}  # contains active all player game with its progress


def get_socket_by_name(name: str):
    """
    Get key by value from {sockets_list} dictionary
    TODO: add dict with (value: key) items if participant count increases

    :param name: str, username that should be unique
    :return: socket or None
    """
    for sock in sockets_list:
        if sockets_list[sock] == name:
            return sock


def create_server_socket():
    """
    Create server socket
    """
    global server_socket
    if len(sys.argv) == 3:
        host = str(sys.argv[1])
        port = int(sys.argv[2])
        print("Try to run server using ip {}:{}".format(host, port), flush=True)
    else:
        host = ""
        port = DEFAULT_PORT
        print("Try to run server on localhost", flush=True)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # fix for tests in Linux: port is not available a few seconds after killing the subprocess
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((host, port))
    except socket.error as msg:
        print("Bind failed. Error: {}".format(msg), flush=True)
        sys.exit()

    server_socket.listen(100)
    print("Server started successfully", flush=True)
    sockets_list[server_socket] = "server"


def send_to_one(sock: socket, msg: str):
    """
    Wrapper for socket.sendall

    :param sock: socket
    :param msg: str
    :return: None
    """
    sock.sendall(msg.encode())


def send_to_all(msg: str, ignore_socket: socket = None):
    """
    Send {message} to all connected client sockets except {ignore_socket} + print in server log
    """
    print(msg, flush=True)
    msg += "\n"
    for sock in sockets_list:
        if sock not in [ignore_socket, server_socket] and sockets_list[sock]:
            send_to_one(sock, msg)


def private_message(sender_sock: socket, recipient_socket: socket, msg: str):
    """
    Private message that only the recipient will see

    :param sender_sock: socket
    :param recipient_socket: socket
    :param msg: str
    :return: None
    """
    msg = "[{}] -> [{}] {}".format(sockets_list[sender_sock], sockets_list[recipient_socket], msg)
    print(msg, flush=True)
    send_to_one(recipient_socket, msg)


def user_registration(sock: socket, msg: str):
    """
    Check that username is unique and register this name.
    Otherwise, asks for another username.

    :param sock: socket,
    :param msg: str, username
    :return: None
    """
    if msg in sockets_list.values():
        send_to_one(sock, "Name '{}' is not available, please try another one.\n"
                          "What is your name?".format(msg))
    else:
        sockets_list[sock] = msg
        host, port = sock.getpeername()
        send_to_all('Accepted new connection from {}:{}, username: {}'.format(host, port, msg), sock)
        send_to_one(sock, "Hi, {}! Welcome to chat room!".format(msg))
