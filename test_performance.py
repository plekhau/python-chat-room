"""
Checking performance
"""
# pylint: disable=C0116     # docstrings
import server
import common


def test_create_server_socket():
    with common.Timer("create_server_socket"):
        common.create_server_socket()


def test_split_message():
    @common.timer
    def split_message(msg):
        return server.split_message(msg)

    assert split_message("[server] rock-paper-scissors") == ("server", "rock-paper-scissors")
