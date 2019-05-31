import sys
import time
import threading
import datetime
import redis
from .message_handler import ContactQueryMessageHandler
# from .query_handler import MemberQuery
from .config import (BOT_ID, AT_BOT, READ_WEBSOCKET_DELAY, SLACK_CLIENT,
    MAX_THREAD_AGE, OLD_THREAD_LIMIT)

client = redis.StrictRedis(host='localhost', port=6379, db=0)

class LazyStatus(object):

    def connect(self):
        """Connect to Slack RTM and start accepting incoming messages."""

        if SLACK_CLIENT.rtm_connect():
            print('LazyStatus Bot is running!')
            pubs = client.pubsub()

            while True:

                # too_many = self._monitor_old_threads()
                # if too_many:
                #     return

                stream = SLACK_CLIENT.rtm_read()
                user_id, username, command, channel = self.parse_stream(stream)

                if command and channel:
                    if command.startswith("init"):
                        thread = MessageTriage(user_id, username, command, channel)
                        thread.daemon = True # daemons will die if MainThread exits
                        thread.start()
                    else:
                        pubs.execute_command('PUBLISH', user_id, command)

                time.sleep(READ_WEBSOCKET_DELAY)

        else:
            print('Connection failed :(')

    def parse_stream(self, stream_output):

        output_list = stream_output
        if output_list:

            for message in output_list:

                AT_BOT_REPLY = False
                DIRECT_MESSAGE = False

                channel = message.get('channel')
                text = message.get('text')
                user_id = message.get('user')

                if not user_id:
                    break

                if message['type'] != "message":
                    break
                    
                if (channel and text):

                    username = "<@{}>".format(user_id)

                    return user_id, username, text, channel

        return None, None, None, None

    def _monitor_old_threads(self):
        """Check how many active and old threads are alive."""

        active_threads = [thread.time_alive for thread in threading.enumerate()[1:]]

        old_threads = [item >= MAX_THREAD_AGE for item in active_threads]

        # If we have too many old threads, it means that Thread instances
        # 'run' methods are taking a long time to return (if they are to
        # return at all). This is an indication that there is some problem
        # in our code and we exit.
        if len(old_threads) > OLD_THREAD_LIMIT:

            # print data on old threads to aid debugging
            print('Old Threads: ')
            for thread in old_threads:
                print('{}: {} via {}'.format(thread.username,
                                             thread.message,
                                             thread.active_query))
            return True

        return False


class MessageTriage(threading.Thread):
    """MessageTriage instances run in their own thread and process queries."""

    # We maintain a class variable dictionary with user_id as key and the
    # current query_handler object as the value. This allows us to access
    # the state of a query that required additional user input to resolve.
    ACTIVE_QUERIES = dict()

    def __init__(self, user_id, username, command, channel):

        threading.Thread.__init__(self)
        # self._thread_initiated = datetime.datetime.now().timestamp()
        self.name = user_id  # name of the current thread

        self.user_id = user_id
        self.username = username
        self.channel = channel
        self.message = command

        self.active_query = MessageTriage.ACTIVE_QUERIES.get(self.user_id)

    @property
    def time_alive(self):
        """Return number of seconds the thread instance has been alive."""

        current_time = datetime.datetime.now().timestamp()
        return current_time - self._thread_initiated

    def run(self):
        """Triage message and prepare reply to send.

        This method overrides the default Thread.run() implementation.
        """
        response = "Hey Wellcome to *LazyStatus*. \nLets get started with *Configuration*. \nEnter the `Project Name`"
        self.send_message(self.username, response, None, self.channel)

        subs = client.pubsub()

        subs.subscribe(self.user_id)

        while True:
            message = subs.get_message()
            if message and message['type'] == 'message':
                project_name = message['data']
                response = "You entered project name `"+ message['data'] +"`\nNow Please Enter Your Project `Channel Name`:"
                self.send_message(self.username, response, None, self.channel)
                break
            time.sleep(READ_WEBSOCKET_DELAY)

        while True:
            message = subs.get_message()
            if message and message['type'] == 'message':
                channel_name = message['data']
                response = "You entered channel name `"+ message['data'] +"`\nNow Please configure GitHub App from here"
                self.send_message(self.username, response, None, self.channel)
                break
            time.sleep(READ_WEBSOCKET_DELAY)


    def send_message(self, username, text, attachments, channel):
        """Send message back to user via slack api call."""

        SLACK_CLIENT.api_call("chat.postMessage",
                              channel=channel,
                              text=text,
                              as_user=True,
                              unfurl_media=False,
                              unfurl_links=False,
                              attachments=attachments)

