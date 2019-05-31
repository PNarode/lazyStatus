import json
import abc
from copy import deepcopy
from .config import slack_attachment

from eng_join import join


class SlackMessageHandler():
    """Abstract base class from which all Slack message handlers derive"""
    __metaclass__= abc.ABCMeta
    message_dictionary = dict()
    message_dictionary['NONE'] = ''
    message_dictionary['RESOLVED'] = "Here's what I found {} :) Let me know"\
                                     " if there is anything else I can do."
    message_dictionary['RESULTS'] = "Okay, here's what I found {}:"
    message_dictionary['CLARIFY'] = "Which one did you mean?"
    message_dictionary['NO_RESULTS'] = "Ugh, I couldn't find anything {}:("

    def __init__(self):

        self.messages = []
        self.attachment_data = {'title': None, 'title_link': None,
                                'fields': [], 'text': None}

    def get_message(self):
        """Returns formatted message to caller."""

        self._prepare_message()
        return self._make_reply()

    def _make_reply(self):
        """Package messages as list of dicts and return packaged reply

        Each message dict item contains two key, value pairs
        'text': a string containing the message
        'attachments': None if no attachment else a dict of attachment fields
        """

        attachment = self._format_attachment(deepcopy(slack_attachment))

        reply = [{'text': self.messages.pop(0),
                  'attachments': attachment}]

        while self.messages:

            next_reply = {'text': self.messages.pop(0),
                          'attachments': None}

            reply.append(next_reply)

        return reply

    def _prepare_message(self):
        """Format message and return reply and attachments."""

        if self.error:
            self._set_error_msg()

        elif self.pending:
            self._set_unresolved_query_msg()

        else:
            self._set_resolved_query_msg()

    def _create_attachment_fields(self, proposed_fields):
        """Set proposed_fields to the Slack attachment fields format"""
        fields = []

        for title, value in proposed_fields:
            if value:
                fields.append(dict([('title', title),
                                   ('value', value),
                                   ('short', True)]))
        return fields

    def _format_attachment(self, attachment):
        """Set attachment fields and return Slack attachment as JSON"""
        for key, value in self.attachment_data.items():
            if key in attachment.keys():
                if key == 'text' and type(value) == list:
                    value = self._make_list_string(value)
                attachment[key] = value

        return json.dumps([attachment])

    def _make_list_string(self, item_list):
        """Turn a list of items into an enumerated string"""

        string_list = '\n'.join(['{}. {}'.format(i+1, item)
                                for i, item in enumerate(item_list)])

        return string_list

    def _format_msg(self, base, joiner='', string=''):
        """Format message strings"""

        try:
            _int = int(string)
            format_string = ''
        except:
            _int = False
            format_string = ' '.join([joiner, string])

        return base.format(format_string).strip()

    @abc.abstractmethod
    def _set_error_msg(self):
        """Create error message."""
        pass

    @abc.abstractmethod
    def _set_unresolved_query_msg(self):
        """Create message requesting further query of interim results."""

        pass

    @abc.abstractmethod
    def _set_resolved_query_msg(self):
        """Create message for resolved query."""
        pass


class ContactQueryMessageHandler(SlackMessageHandler):

    def __init__(self, query, pending, error,
                 summary=None, data=None, results=None):

        super().__init__()

        self.msg_dict = SlackMessageHandler.message_dictionary
        self.query = query
        self.pending = pending
        self.error = error
        self.member_summary = summary
        self.member_data = data
        self.search_results = results

    def _set_error_msg(self):
        """Set error message and append to messages."""

        error_message = self._format_msg(base=self.msg_dict[self.error],
                                         joiner='for',
                                         string=self.query)

        self.messages.append(error_message)

    def _set_unresolved_query_msg(self):
        """Set unresolved query msg and append msg and attachment to messages"""

        primary_reply = self._format_msg(base=self.msg_dict['RESULTS'],
                                         joiner='for',
                                         string=self.query)

        secondary_reply = self.msg_dict['CLARIFY']

        self.attachment_data['text'] = [res[0] for res in self.search_results]

        self.messages.extend([primary_reply, secondary_reply])

    def _set_resolved_query_msg(self):
        """Set resolved query msg and append msg and attachment to messages"""

        twitter_handle = self.member_data.get('twitter_id')

        if twitter_handle:
            twitter_url = 'twitter.com/{}'.format(twitter_handle)
        else:
            twitter_url = None

        # prepare
        phone_number = self.member_data.get('phone')
        office_locale = self.member_data.get('office')
        contact_form = self.member_data.get('contact_form')

        _fields = [('Twitter', twitter_url),
                   ('Phone', phone_number),
                   ('Office', office_locale),
                   ('Contact Form', contact_form)]

        self.attachment_data['fields'] = self._create_attachment_fields(_fields)

        self.attachment_data['title'] = self.member_summary
        self.attachment_data['title_link'] = self.member_data['website']

        primary_reply = self._format_msg(base=self.msg_dict['RESOLVED'],
                                         joiner='for',
                                         string=self.query)

        secondary_reply = self.msg_dict['NONE']

        self.messages.extend([primary_reply, secondary_reply])


