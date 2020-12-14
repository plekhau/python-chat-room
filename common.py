"""
Low-level functionality with sockets + global variables
"""
import socket
import sys
from typing import Dict, Callable
import logging.config
import time

from bots.bot import Bot

BUFFER_SIZE = 2048
DEFAULT_PORT = 8888
INIT_GAME_MSG = "init_game"
STOP_GAME_MSG = "stop_game"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sockets_list: Dict[socket.socket, str] = {}
one_player_game_list: Dict[socket.socket, Dict] = {}  # contains active one player games with their progresses if needed
all_player_game: Dict[str, Callable] = {}  # contains active all player game with its progress

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('chat_logger')

bots = [
    Bot("http://127.0.0.1:5555/messages"),   # slack bot
]


class Timer:
    """
    Context manager for checking code performance
    """
    def __init__(self, name):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000
        logger.debug("{}: {}".format(self.name, duration))


def timer(fun):
    """
    Decorator for checking function performance
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = fun(*args, **kwargs)
        duration = (time.time() - start_time) * 1000
        logger.debug("{}: {}".format(fun.__name__, duration))
        return result
    return wrapper


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
    return None


def create_server_socket():
    """
    Create server socket
    """
    if len(sys.argv) == 3:
        host = str(sys.argv[1])
        port = int(sys.argv[2])
        logger.error("Try to run server using ip {}:{}".format(host, port))
    else:
        host = ""
        port = DEFAULT_PORT
        logger.error("Try to run server on localhost")

    try:
        # fix for tests in Linux: port is not available a few seconds after killing the subprocess
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((host, port))
    except socket.error as msg:
        logger.error("Bind failed. Error: {}".format(msg))
        sys.exit()

    server_socket.listen(100)
    logger.info("Server started successfully")
    sockets_list[server_socket] = "server"


def send_to_one(sock: socket.socket, msg: str):
    """
    Wrapper for socket.sendall

    :param sock: socket
    :param msg: str
    :return: None
    """
    sock.sendall(msg.encode())


def send_to_all(msg: str, ignore_socket: socket.socket = None, ignore_bot: str = None):
    """
    Send {message} to all connected client sockets except {ignore_socket} + print in server log
    """
    logger.info(msg)
    msg += "\n"
    for sock in sockets_list:
        if sock not in [ignore_socket, server_socket] and sockets_list[sock]:
            send_to_one(sock, msg)

    for bot in bots:
        if bot.name() != ignore_bot:
            bot.send_message(msg)


def private_message(sender_sock: socket.socket, recipient_socket: socket.socket, msg: str):
    """
    Private message that only the recipient will see

    :param sender_sock: socket
    :param recipient_socket: socket
    :param msg: str
    :return: None
    """
    msg = "[{}] -> [{}] {}".format(sockets_list[sender_sock], sockets_list[recipient_socket], msg)
    logger.info(msg)
    send_to_one(recipient_socket, msg)


def user_registration(sock: socket.socket, msg: str):
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
