VALID_INFO = [
    "REQUEST",
    "GRAND",
    "REFUSE",
    "RELEASE"    
]


REQUEST = "REQUEST"
GRAND = "GRAND"
REFUSE = "REFUSE"
RELEASE = "RELEASE"


class MessageItem(object):
    def __init__(self, timestamp, vpid, info, other=""):
        assert info in VALID_INFO
        self.timestamp = timestamp
        self.vpid = vpid
        self.info = info
        self.other = other

    def __str__(self):
        return f"{self.timestamp}:{self.vpid}:{self.info}:{self.other}"


def make_message_from_str(s):
    timestamp, vpid, info, other = s.split(":")
    timestamp = int(timestamp)
    vpid = int(vpid)
    return MessageItem(timestamp, vpid, info, other)