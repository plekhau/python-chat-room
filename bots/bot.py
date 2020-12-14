import logging
import requests

logger = logging.getLogger('chat_logger')


class Bot:
    """
    Implements work with bots using API
    """

    def __init__(self, url):
        self.url = url

    def name(self):
        """
        Use URL as bot name
        Should be unique for different bots
        """
        return self.url

    def get_messages(self):
        """
        Get new messages from bot
        """
        messages = []
        try:
            response = requests.get(self.url)
            assert response.status_code == 200
            messages = response.json()["messages"]
        except OSError:
            pass    # do nothing, maybe bot is not run (logging will break tests)
        except Exception as ex:
            logger.error("Messages were not received:(\n{}".format(ex))
        return messages

    def send_message(self, msg):
        """
        Send message to bot
        """
        try:
            response = requests.post(self.url, data=msg)
            assert response.status_code == 200
        except OSError:
            pass    # do nothing, maybe bot is not run (logging will break tests)
        except Exception as ex:
            logger.error("Message was not sent:(\n{}".format(ex))
