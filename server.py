"""
Create server socket and start endless loop with checking client socket responses

Start:
- for connecting to localhost:     python server.py
- for connecting to remote host:   python server.py ip_address port

Features:
- All users have unique name
- User can get the last chat messages by sending any message or pressing Enter
- Users can send public message just typing any text
- Users can send private message, i.e [recipient] message
- Users can interact with server, i.e. [server] command
- List of server commands:
    [server] help                   - info about chat
    [server] participants           - return list of chat participants
    [server] participants-count     - return count of chat participants
    [server] rock-paper-scissors    - play rock-paper-scissors game with server
    [server] 21                     - play 21 game with server
    [server] quiz                   - quiz game for all participants
"""
import select
import socket
import sys
import random
from threading import Timer

BUFFER_SIZE = 2048
init_game_msg = "init_game"
stop_game_msg = "stop_game"

server_socket = None
sockets_list = {}
one_player_game_list = {}  # contains active one player games with their progresses if needed
all_player_game = {}  # contains active all player game with its progress


def _get_socket_by_name(name: str):
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
        port = 8888
        print("Try to run server on localhost", flush=True)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
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
    try:
        sock.sendall(msg.encode())
    finally:
        pass


def send_to_all(msg: str, ignore_socket: socket):
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


def split_message(msg: str):
    """
    Split message from socket if it has format "[recipient] command"
    Otherwise, return whole message as command

    :param msg: str, message from socket to server
    :return: tuple, (recipient, command)
    """
    if msg[0] == "[" and "]" in msg:
        pos = msg.find("]")
        recipient = msg[1:pos].strip()
        cmd = msg[pos + 1:].strip()
        return recipient, cmd
    else:
        return None, msg


def one_player_game_rock_paper_scissors(sock: socket, msg: str):
    """
    Game: rock-paper-scissors

    :param sock: socket, client socket that is playing game
    :param msg: str, client choice (rock/r, paper/p or scissors/s)
    :return: None
    """
    if msg == init_game_msg:
        private_message(server_socket, sock, "Let's play rock-paper-scissors!\n"
                                             "What is your choice?"
                                             " (need to send: rock or r / paper or p /scissors or s)")
        one_player_game_list[sock] = {"game": one_player_game_rock_paper_scissors}
    else:
        if msg == "rock" or msg == "r" or msg == "paper" or msg == "p" or msg == "scissors" or msg == "s":
            if msg == "r":
                msg = "rock"
            elif msg == "p":
                msg = "paper"
            elif msg == "s":
                msg = "scissors"
            server_choice = random.choice(["rock", "paper", "scissors"])
            if msg == server_choice:
                status = "No winner!"
            elif msg == "rock":
                status = "You won!" if server_choice == "scissors" else "Server won!"
            elif msg == "paper":
                status = "You won!" if server_choice == "rock" else "Server won!"
            elif msg == "scissors":
                status = "You won!" if server_choice == "paper" else "Server won!"
            else:
                raise ValueError("Something impossible was happened")
            private_message(server_socket, sock, "Your choice: {}, server choice: {}. {}"
                            .format(msg, server_choice, status))
            one_player_game_list.pop(sock)
        else:
            private_message(server_socket, sock, "You sent incorrect value. Please try again.\nWhat is your choice?"
                                                 " (need to send: rock or r / paper or p /scissors or s)")


def one_player_game_21(sock: socket, msg: str):
    """
    Game: 21

    :param sock: socket, client socket that is playing game
    :param msg: str, client choice (numbers [0..10] or stop)
    :return: None
    """
    if msg == init_game_msg:
        private_message(server_socket, sock, "Let's play 21!\n"
                                             "You and server will throw numbers from 0 to 10 and calculate them.\n"
                                             "Your goal: score as much as possible, but not more than 21.\n"
                                             "Throwing out for you (need to send: number from 0 to 10 or 'stop')")
        one_player_game_list[sock] = {"game": one_player_game_21,
                                      "status": "throwing_for_player",
                                      "player": 0,
                                      "server": 0}
    else:
        if "stop" in msg and one_player_game_list[sock]["status"] == "throwing_for_player":
            one_player_game_list[sock]["status"] = "throwing_for_server"
            response = "Throwing out for server (need to send: number from 0 to 10)"
        else:
            if msg.isdigit() and int(msg) < 11:
                player_score = one_player_game_list[sock]["player"]
                server_score = one_player_game_list[sock]["server"]
                player = int(msg)
                if one_player_game_list[sock]["status"] == "throwing_for_player":
                    server = random.randint(0, 10) if player_score < 12 else 10
                else:
                    server = random.randint(0, 10)
                if one_player_game_list[sock]["status"] == "throwing_for_player":
                    player_score += player + server
                else:
                    server_score += player + server
                one_player_game_list[sock]["player"] = player_score
                one_player_game_list[sock]["server"] = server_score
                response = "You thrown {}, server thrown {}. Total: you - {}, server - {}\n" \
                    .format(player, server, player_score, server_score)
                if one_player_game_list[sock]["status"] == "throwing_for_player":
                    if player_score == 21:
                        response += "Wow! BlackJack! You won!"
                        one_player_game_list.pop(sock)
                    elif player_score < 21:
                        response += "Throwing out for you (need to send: number from 0 to 10 or 'stop')"
                    else:
                        response += "You took more 21! You lost!"
                        one_player_game_list.pop(sock)
                else:
                    if server_score <= player_score and server_score <= 11:
                        response += "Throwing out for server (need to send: number from 0 to 10)"
                    else:
                        if server_score > 21:
                            response += "Server took more 21! You won!"
                        elif server_score > player_score:
                            response += "Server won!"
                        elif server_score == player_score:
                            response += "No winner!"
                        else:
                            response += "You won!"
                        one_player_game_list.pop(sock)
            else:
                response = "You sent incorrect value. Please try again."
        private_message(server_socket, sock, response)


def all_players_game_quiz(sock: socket, msg: str):
    """
    Game: Quiz (all players game)

    :param sock: socket, client socket that is playing game
    :param msg: str, client answer
    :return: None
    """
    global all_player_game
    if msg == init_game_msg:
        questions = [("How many bytes in one kilobyte?", "1024", "equal"),
                     ("What is the capital of Belarus?", "Minsk", "equal"),
                     ("Who is the creator of the Python?", "Guido", "contains")]
        num = random.randint(0, len(questions) - 1)
        question, answer, comparison = questions[num]
        send_to_all("Let's start Quiz round!\nYou have 30 sec and you can send several answers\n{}"
                    .format(question), None)
        all_player_game = {"game": all_players_game_quiz,
                           "answer": answer,
                           "comparison": comparison,
                           "winner": None,
                           "log": ""}
        Timer(30, all_players_game_quiz, [None, stop_game_msg]).start()
    elif msg == stop_game_msg:
        if len(all_player_game["log"]) > 0:
            response = "Participants' answer(s):\n{}The right answer: {}\n" \
                .format(all_player_game["log"], all_player_game["answer"])
            if all_player_game["winner"] is None:
                response += "No winner!"
            else:
                response += "The winner is {}! Congratulations!".format(all_player_game["winner"])
        else:
            response = "Nobody sent an answer. No winner!"
        send_to_all(response, None)
        all_player_game.clear()
    else:
        all_player_game["log"] += "[{}] {}\n".format(sockets_list[sock], msg)
        if all_player_game["winner"] is None:
            if all_player_game["comparison"] == "equal":
                is_right = all_player_game["answer"].lower() == msg.lower()
            else:  # contains
                is_right = all_player_game["answer"].lower() in msg.lower()
            if is_right:
                all_player_game["winner"] = sockets_list[sock]


def process_message_to_server(sock: socket, cmd: str):
    """
    Process commands like '[server] <command>'

    :param sock: socket
    :param cmd: str, command that can be processed, see help command for details
    :return: None
    """
    if cmd == "help":
        about_chat = """To send a public message: just send any text.
        To send private message: [<username>] <your message>
        To send message to server: [server] command
        Server supports the following commands:
        [server] help - info about chat
        [server] participants - return list of chat participants
        [server] participants-count - return count of chat participants
        [server] rock-paper-scissors - play rock-paper-scissors game with server
        [server] 21 - play 21 game with server
        [server] quiz - quiz game for all participants"""
        private_message(server_socket, sock, about_chat)
    elif cmd == "participants":
        participants = list(sockets_list.values())
        participants.remove(sockets_list[server_socket])
        private_message(server_socket, sock, "List of participants: {}".format(", ".join(participants)))
    elif cmd == "participants-count":
        private_message(server_socket, sock, "Participants count: {}".format(len(sockets_list.values()) - 1))
    elif cmd == "rock-paper-scissors":
        one_player_game_rock_paper_scissors(sock, init_game_msg)
    elif cmd == "21":
        one_player_game_21(sock, init_game_msg)
    elif cmd == "quiz":
        all_players_game_quiz(None, init_game_msg)
    else:
        private_message(server_socket, sock, "Unknown command")


def process_message(sock: socket, msg: str):
    """
    Common function for processing message from socket

    :param sock: socket, socket-sender
    :param msg: str, message from socket
    :return: None
    """
    try:
        if all_player_game:
            all_player_game["game"](sock, msg)
        elif sock in one_player_game_list:
            one_player_game_list[sock]["game"](sock, msg)
        else:
            recipient, cmd = split_message(msg)
            if recipient is None:
                send_to_all("[{}] {}".format(sockets_list[sock], cmd), sock)
            else:
                recipient_socket = _get_socket_by_name(recipient)
                msg = "[{}] -> [{}] {}".format(sockets_list[sock], recipient, cmd)
                print(msg, flush=True)

                if recipient_socket is None:
                    send_to_one(sock, "Unknown recipient. Please try again.")
                elif recipient == sockets_list[server_socket]:
                    process_message_to_server(sock, cmd)
                else:
                    # Private message from client to client
                    send_to_one(recipient_socket, msg)
    except Exception as ex:
        print("Something goes wrong:(\n{}".format(ex), flush=True)


def start_server():
    """
    Create server socket and start endless loop with checking client socket responses
    """
    create_server_socket()

    while True:
        read_sockets, write_socket, error_socket = select.select(sockets_list.keys(), [], [])

        for read_socket in read_sockets:
            if read_socket == server_socket:
                client_socket, addr = read_socket.accept()
                sockets_list[client_socket] = ""
                send_to_one(client_socket, "Hi! You are trying to connect to char room.\nWhat is your name?")
            else:
                try:
                    message = read_socket.recv(BUFFER_SIZE).decode()
                    if not message:
                        raise ConnectionError
                    elif not sockets_list[read_socket]:
                        user_registration(read_socket, message)
                    else:
                        process_message(read_socket, message)
                except ConnectionError:
                    username = sockets_list.pop(read_socket)
                    if username == "":
                        print("Unknown user was disconnected", flush=True)
                    else:
                        send_to_all("User '{}' was disconnected".format(username), read_socket)


if __name__ == "__main__":
    start_server()
