import random
import socket
import common
from threading import Timer

questions = [("How many bytes in one kilobyte?", "1024", "equal"),
             ("What is the capital of Belarus?", "Minsk", "equal"),
             ("Who is the creator of the Python?", "Guido", "contains")]
_answer = None          # right answer on the current question
_comparison = None      # how to compare user answer and right one (equal, contains)
_winner = None          # quiz winner
_log = None             # log of user answers


def init_new_game():
    """
    Initialization game parameters, send question to users and start timer
    """
    global _answer, _comparison, _winner, _log
    question, _answer, _comparison = random.choice(questions)
    _winner = None
    _log = ""
    common.send_to_all(f"Let's start Quiz round!\nYou have 30 sec and you can send several answers\n{question}")
    common.all_player_game["game"] = all_players_game_quiz
    Timer(30, all_players_game_quiz, [None, common.stop_game_msg]).start()


def is_right_answer(answer: str):
    """
    Check if user answer is correct.
    _comparison can have values:
        - equal - the answer must strictly correspond to the correct one
        - contains - the answer must contain the correct one
                     (i.e. "Guido", "Guido van Rossum" are both correct if right answer is "Guido")
    :param answer: str, user answer
    :return: None
    """
    if _comparison == "equal":
        return _answer.lower() == answer.lower()
    else:  # contains
        return _answer.lower() in answer.lower()


def finish_game():
    if len(_log) > 0:
        response = "Participants' answer(s):\n{}The right answer: {}\n".format(_log, _answer)
        if _winner is None:
            response += "No winner!"
        else:
            response += "The winner is {}! Congratulations!".format(_winner)
    else:
        response = "Nobody sent an answer. No winner!"
    common.send_to_all(response)
    common.all_player_game.clear()


def all_players_game_quiz(sock: socket, msg: str):
    """
    Game: Quiz (all players game)

    :param sock: socket, client socket that is playing game
    :param msg: str, client answer
    :return: None
    """
    global _winner, _log
    if msg == common.init_game_msg:
        init_new_game()
    elif msg == common.stop_game_msg:
        finish_game()
    else:
        _log += "[{}] {}\n".format(common.sockets_list[sock], msg)
        if _winner is None and is_right_answer(msg):
            _winner = common.sockets_list[sock]
