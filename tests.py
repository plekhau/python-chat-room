import os
from queue import Queue
import pytest
import subprocess
import threading

server_process = None
client_process = None
client1_process = None
client2_process = None
client3_process = None


# https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


def run_process(filename: str) -> (subprocess, Queue):
    process = subprocess.Popen("python {}".format(filename), shell=False,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None)
    process_stdout_queue = Queue()
    t = threading.Thread(target=enqueue_output, args=(process.stdout, process_stdout_queue))
    t.daemon = True  # thread dies with the program
    t.start()
    return process, process_stdout_queue


def wait_line_from_stdout(q, timeout=10):
    while timeout > 0:
        try:
            line = q.get(timeout=1)
        except:
            pass
        else:  # got line
            return line.decode().strip()
        timeout -= 1


def start_server() -> (subprocess, Queue):
    global server_process
    process, process_stdout_queue = run_process("server.py")
    server_process = process
    assert wait_line_from_stdout(process_stdout_queue) == "Try to run server on localhost"
    assert wait_line_from_stdout(process_stdout_queue) == "Server started successfully"
    return process, process_stdout_queue


def start_client(username: str, correct_login=True) -> (subprocess, Queue):
    global client_process
    process, process_stdout_queue = run_process("client.py")
    client_process = process
    assert wait_line_from_stdout(process_stdout_queue) == "Socket Connected to localhost on ip 127.0.0.1"
    assert wait_line_from_stdout(process_stdout_queue) == "Hi! You are trying to connect to char room."
    assert wait_line_from_stdout(process_stdout_queue) == "What is your name?"
    write_stdin(process, username)
    if correct_login:
        assert wait_line_from_stdout(process_stdout_queue) == "Hi, {}! Welcome to chat room!".format(username)
    return process, process_stdout_queue


# def read_stdout(process):
#     return process.stdout.readline().decode().strip()


def write_stdin(process, data):
    process.stdin.write("{}\n".format(data).encode())
    process.stdin.flush()


def setup():
    print(os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0])  # test name
    pass


def teardown():
    for process in [server_process, client_process, client1_process, client2_process, client3_process]:
        if process:
            process.kill()


def test_simple_login():
    global server_process
    global client1_process
    username = "Test User"
    user_msg = "User message"

    server_process, server_stdout_queue = start_server()
    client1_process, client1_stdout_queue = start_client(username)

    write_stdin(client1_process, user_msg)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] {}".format(username, user_msg)


def test_simple_login_with_russian_symbols():
    global server_process
    global client1_process
    username = "Новый юзер"
    user_msg = "Привет, мир!"

    server_process, server_stdout_queue = start_server()
    client1_process, client1_stdout_queue = start_client(username)

    write_stdin(client1_process, user_msg)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] {}".format(username, user_msg)


def test_login_with_wrong_name():
    global server_process
    global client1_process
    global client2_process
    username1 = "Test User"
    username2 = "Test User2"
    wrong_name1 = "server"
    wrong_name2 = "  server"
    wrong_name3 = ""
    wrong_name4 = "  "

    server_process, server_stdout_queue = start_server()
    client1_process, client1_stdout_queue = start_client(wrong_name1, False)
    assert wait_line_from_stdout(client1_stdout_queue) == "Name '{}' is not available, please try another one.".format(
        wrong_name1)
    assert wait_line_from_stdout(client1_stdout_queue) == "What is your name?"

    write_stdin(client1_process, wrong_name2)
    assert wait_line_from_stdout(client1_stdout_queue) == "Name '{}' is not available, please try another one.".format(
        wrong_name2.strip())
    assert wait_line_from_stdout(client1_stdout_queue) == "What is your name?"

    write_stdin(client1_process, wrong_name3)
    assert wait_line_from_stdout(client1_stdout_queue, 1) is None

    write_stdin(client1_process, wrong_name4)
    assert wait_line_from_stdout(client1_stdout_queue, 1) is None

    write_stdin(client1_process, username1)
    assert wait_line_from_stdout(client1_stdout_queue) == "Hi, {}! Welcome to chat room!".format(username1)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)

    client2_process, client2_stdout_queue = start_client(username1, False)
    assert wait_line_from_stdout(client2_stdout_queue) == "Name '{}' is not available, please try another one.".format(
        username1)
    assert wait_line_from_stdout(client2_stdout_queue) == "What is your name?"

    write_stdin(client2_process, username2)
    assert wait_line_from_stdout(client2_stdout_queue) == "Hi, {}! Welcome to chat room!".format(username2)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)


def test_public_messages():
    global server_process
    global client1_process
    global client2_process
    global client3_process
    username1 = "Test User1"
    username2 = "Test User2"
    username3 = "Test User3"
    message1 = "test_msg1"
    message2 = "test_msg2"

    server_process, server_stdout_queue = start_server()
    client1_process, client1_stdout_queue = start_client(username1)
    client2_process, client2_stdout_queue = start_client(username2)
    client3_process, client3_stdout_queue = start_client(username3)

    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)

    assert wait_line_from_stdout(client1_stdout_queue, 1) is None
    write_stdin(client1_process, "")
    assert "Accepted new connection from" in wait_line_from_stdout(client1_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(client1_stdout_queue)
    assert wait_line_from_stdout(client1_stdout_queue) == ""  # TODO: extra empty line

    write_stdin(client2_process, message1)
    assert "Accepted new connection from" in wait_line_from_stdout(client2_stdout_queue)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] {}".format(username2, message1)

    write_stdin(client3_process, message2)
    assert wait_line_from_stdout(client3_stdout_queue) == "[{}] {}".format(username2, message1)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] {}".format(username3, message2)

    assert wait_line_from_stdout(client1_stdout_queue, 1) is None
    write_stdin(client1_process, "")
    assert wait_line_from_stdout(client1_stdout_queue) == "[{}] {}".format(username2, message1)
    assert wait_line_from_stdout(client1_stdout_queue) == "[{}] {}".format(username3, message2)


def test_private_messages():
    global server_process
    global client1_process
    global client2_process
    global client3_process
    username1 = "Test User1"
    username2 = "Test User2"
    username3 = "Test User3"
    username4 = "Test User4"  # does not exist
    message1 = "[{}] test_msg1".format(username2)
    message2 = "[{}] test_msg2".format(username1)
    message3 = "[{}] test_msg2".format(username4)
    message4 = "[server] test_msg3"

    server_process, server_stdout_queue = start_server()
    client1_process, client1_stdout_queue = start_client(username1)
    client2_process, client2_stdout_queue = start_client(username2)
    client3_process, client3_stdout_queue = start_client(username3)

    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)

    write_stdin(client1_process, message1)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] -> {}".format(username1, message1)
    assert "Accepted new connection from" in wait_line_from_stdout(client1_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(client1_stdout_queue)
    assert wait_line_from_stdout(client1_stdout_queue) == ""  # TODO: extra empty line

    write_stdin(client2_process, message2)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] -> {}".format(username2, message2)
    assert "Accepted new connection from" in wait_line_from_stdout(client2_stdout_queue)
    assert wait_line_from_stdout(client2_stdout_queue) == "[{}] -> {}".format(username1, message1)

    write_stdin(client3_process, "")
    assert wait_line_from_stdout(client3_stdout_queue, 1) is None

    assert wait_line_from_stdout(client1_stdout_queue, 1) is None
    write_stdin(client1_process, "")
    assert wait_line_from_stdout(client1_stdout_queue) == "[{}] -> {}".format(username2, message2)

    write_stdin(client1_process, message3)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] -> {}".format(username1, message3)
    assert wait_line_from_stdout(client1_stdout_queue) == "Unknown recipient. Please try again."

    write_stdin(client1_process, message4)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] -> {}".format(username1, message4)
    assert wait_line_from_stdout(client1_stdout_queue) == "[server] -> [{}] Unknown command".format(username1)

    write_stdin(client2_process, "")
    assert wait_line_from_stdout(client2_stdout_queue, 1) is None


def test_server_commands_help():
    # [server] help
    global server_process
    global client1_process
    username1 = "Test User1"
    message1 = "[server] help"
    help_message = ["To send a public message: just send any text.",
                    "To send private message: [<username>] <your message>",
                    "To send message to server: [server] command",
                    "Server supports the following commands:",
                    "[server] help - info about chat",
                    "[server] participants - return list of chat participants",
                    "[server] participants-count - return count of chat participants",
                    "[server] rock-paper-scissors - play rock-paper-scissors game with server",
                    "[server] 21 - play 21 game with server",
                    "[server] quiz - quiz game for all participants"]

    server_process, server_stdout_queue = start_server()
    client1_process, client1_stdout_queue = start_client(username1)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)

    write_stdin(client1_process, message1)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] -> {}".format(username1, message1)
    for help_msg in help_message:
        assert help_msg in wait_line_from_stdout(server_stdout_queue)
    for help_msg in help_message:
        assert help_msg in wait_line_from_stdout(client1_stdout_queue)


def test_server_commands_participants():
    # [server] participants
    # [server] participants-count
    global server_process
    global client1_process
    global client2_process
    global client3_process
    username1 = "Test User1"
    username2 = "Test User2"
    username3 = "Test User3"
    message1 = "[server] participants"
    message2 = "[server] participants-count"

    server_process, server_stdout_queue = start_server()
    client1_process, client1_stdout_queue = start_client(username1)
    client2_process, client2_stdout_queue = start_client(username2)
    client3_process, client3_stdout_queue = start_client(username3)

    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(server_stdout_queue)

    # [server] participants
    write_stdin(client1_process, message1)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] -> {}".format(username1, message1)
    assert "Accepted new connection from" in wait_line_from_stdout(client1_stdout_queue)
    assert "Accepted new connection from" in wait_line_from_stdout(client1_stdout_queue)
    response = "[server] -> [{}] List of participants: {}".format(username1, ", ".join([username1, username2, username3]))
    assert wait_line_from_stdout(server_stdout_queue) == response
    assert wait_line_from_stdout(client1_stdout_queue) == response

    # [server] participants-count
    write_stdin(client1_process, message2)
    assert wait_line_from_stdout(server_stdout_queue) == "[{}] -> {}".format(username1, message2)
    response = "[server] -> [{}] Participants count: 3".format(username1)
    assert wait_line_from_stdout(server_stdout_queue) == response
    assert wait_line_from_stdout(client1_stdout_queue) == response

    write_stdin(client3_process, "")
    assert wait_line_from_stdout(client3_stdout_queue, 1) is None
