def list_to_str(lst):
    return str(lst)

def str_to_list(s):
    lst = s[1:-1].split(", ")
    lst = [int(x) for x in lst]
    return lst


class RequestItem(object):
    def __init__(self, timestamp, vpid):
        self.timestamp = timestamp
        self.vpid = vpid

    def __str__(self):
        return f"{self.timestamp}:{self.vpid}"

    def __lt__(self, other):
        assert isinstance(other, RequestItem)
        if self.timestamp == other.timestamp:
            return self.vpid < other.vpid
        return self.timestamp < other.timestamp


def make_request_from_str(s):
    timestamp, vpid = s.split(":")
    timestamp = int(timestamp)
    vpid = int(vpid)
    req = RequestItem(timestamp, vpid)
    return req


def verify_request_format(req):
    return True