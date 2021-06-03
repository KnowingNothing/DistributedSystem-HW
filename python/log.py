from .message import MessageItem


VALID_EVENT = [
    "SEND",
    "RECEIVE",
    "COMPUTE"
]

SEND = "SEND"
RECEIVE = "RECEIVE"
COMPUTE = "COMPUTE"


class LogItem(MessageItem):
    def __init__(self, timestamp, event, vpid, info, other=""):
        super(LogItem, self).__init__(timestamp, vpid, info, other)
        assert event in VALID_EVENT
        self.event = event

    def __str__(self):
        return f"{self.timestamp}:{self.event}:{self.vpid}:{self.info}:{self.other}"


def make_log_from_str(s):
    timestamp, event, vpid, info, other = s.split(":")
    timestamp = int(timestamp)
    vpid = int(vpid)
    return LogItem(timestamp, event, vpid, info, other)


def verify_log_format(log):
    return True