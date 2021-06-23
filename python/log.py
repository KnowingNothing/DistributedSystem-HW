from .message import *


VALID_EVENT = [
    "SEND",
    "RECEIVE",
    "COMPUTE"
]

SEND = "SEND"
RECEIVE = "RECEIVE"
COMPUTE = "COMPUTE"



def beautify_log(log):
    if log.event == SEND:
        if log.info == GRAND:
            s = f"{log.timestamp} reply {log.self_id} to <{log.other}, {log.vpid}>"
        elif log.info == REQUEST:
            #s = f"{log.timestamp} request <{log.other}, {log.self_id}> from {log.vpid}"
            s = f"{log.timestamp} request <{log.timestamp}, {log.self_id}>"
        elif log.info == RELEASE:
            s = f"{log.timestamp} release <{log.other}, {log.self_id}> in {log.vpid}"
        elif log.info == REFUSE:
            raise NotImplementedError()
        else:
            raise ValueError()
    elif log.event == RECEIVE:
        if log.info == GRAND:
            s = f"{log.timestamp} recv reply {log.vpid}"
        elif log.info == REQUEST:
            s = f"{log.timestamp} recv <{log.other}, {log.vpid}>"
        elif log.info == RELEASE:
            s = f"{log.timestamp} recv release {log.vpid}"
        elif log.info == REFUSE:
            raise NotImplementedError()
        else:
            raise ValueError()
    elif log.event == COMPUTE:
        raise NotImplementedError()
    else:
        raise ValueError()
    return s


class LogItem(MessageItem):
    def __init__(self, self_id, timestamp, event, vpid, info, other=""):
        super(LogItem, self).__init__(timestamp, vpid, info, other)
        assert event in VALID_EVENT
        self.self_id = self_id
        self.event = event

    def __repr__(self):
        return f"{self.self_id}:{self.timestamp}:{self.event}:{self.vpid}:{self.info}:{self.other}"

    def __str__(self):
        return beautify_log(self)


def make_log_from_str(s):
    self_id, timestamp, event, vpid, info, other = s.split(":")
    timestamp = int(timestamp)
    vpid = int(vpid)
    return LogItem(self_id, timestamp, event, vpid, info, other)


def verify_log_format(log):
    return True
