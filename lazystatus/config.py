import os
from slackclient import SlackClient


# Billy Bot's Slack ID
BOT_ID = os.environ.get('BOT_ID')

# constants
AT_BOT = '<@{}>'.format(BOT_ID)

# Slack Client Config
SLACK_CLIENT = SlackClient("xoxb-644938651809-639878011538-fBs7uiVBuUJwA7H6DhJhO0Lh")
READ_WEBSOCKET_DELAY = 1

# What counts an an 'old' thread
MAX_THREAD_AGE = 90  # seconds
OLD_THREAD_LIMIT = 10

slack_attachment = {
    "fallback": None,  # "Required plain-text summary of the attachment."
    "color": '#56A0D3',  # color hex value
    "pretext": None,  # "Optional text that appears above the attachment block"
    "author_name": None,
    "author_link": None,
    "title": None,
    "title_link": None,
    "fields": [],
    "text": None,  # "Optional text that appears within the attachment",
    "footer": None,
    "ts": None
}
