import os
import time
import re
from slackclient import SlackClient

SLACK_BOT_TOKEN = "xoxb-644938651809-639878011538-vyKxtdSSJdYZHYWQWk4ymxLT"

# instantiate Slack client
slack_client = SlackClient(SLACK_BOT_TOKEN)

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
INIT_COMMAND = "init"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            parse_direct_mention(event["text"])
            return event["text"], event["channel"]
    return None, None


def init(command, channel):
    response = "Hey Wellcome to *LazyStatus*. \nLets get started with *Configuration*. \nEnter the `Project Name`"
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

    while True:
        command, channel = parse_bot_commands(slack_client.rtm_read())
        if command:
            break
        time.sleep(RTM_READ_DELAY)
    
    project_name = command

    response = "Great! Lets get started with Project=`" + project_name +"`"

    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """

    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(INIT_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(INIT_COMMAND):
        init(command, channel)
        return

    # response = "Will get started with lazystatus configuration !!! \n Please Enter you Github Id:"

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")

        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
    
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")