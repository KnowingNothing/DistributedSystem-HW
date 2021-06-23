import os
import json
import heapq
import time
import random
import socket
import threading
import struct
from .log import make_log_from_str, verify_log_format, LogItem, SEND, RECEIVE, COMPUTE
from .request import make_request_from_str, verify_request_format, RequestItem
from .message import MessageItem, make_message_from_str, REQUEST, REFUSE, RELEASE, GRAND


MAX_WORK_TIME = 1000  # seconds


class WorkerContext(object):
    def __init__(self, addr_info, idx):
        self.log = []
        self.total_addr_info = addr_info
        self.self_id = idx
        self.queue = []
        self.requesting_critical_section = False
        self.in_critical_section = False
        self.compete_trials = 0
        self.max_compete_trials = 4
        self.lamport_timestamp = 0
        self.acks = []
        if self.self_id is None:
            self.fout = open(os.devnull, "w")
            # self.fout = open("tmp.log", "a")
        else:
            os.makedirs(".debug", exist_ok=True)
            self.fout = open(f".debug/debug_{self.self_id}.log", "w")
        
        if self.self_id is None:
            self.log_out = open(os.devnull, "w")
        else:
            os.makedirs(".display", exist_ok=True)
            self.log_out = open(f".display/process_{self.self_id}.log", "w")

    def __del__(self):
        self.fout.close()
        self.log_out.close()

    def to_dict(self):
        return {
            "log": [str(x) for x in self.log],
            "total_addr_info": self.total_addr_info,
            "self_id": self.self_id,
            "queue": [str(x) for x in self.queue],
            "requesting_critical_section": self.requesting_critical_section,
            "in_critical_section": self.in_critical_section,
            "compete_trials": self.compete_trials,
            "max_compete_trials": self.max_compete_trials,
            "lamport_timestamp": self.lamport_timestamp,
            "acks": self.acks
        }

    def from_dict(self, d):
        self.log = [make_log_from_str(s) for s in d["log"]]
        self.total_addr_info = [tuple(x) for x in d["total_addr_info"]]
        self.self_id = d["self_id"]
        self.queue = [make_request_from_str(s) for s in d["queue"]]
        self.requesting_critical_section = d["requesting_critical_section"]
        self.in_critical_section = d["in_critical_section"]
        self.compete_trials = d["compete_trials"]
        self.max_compete_trials = d["max_compete_trials"]
        self.lamport_timestamp = d["lamport_timestamp"]
        self.acks = d["acks"]

        if self.self_id is None:
            self.fout = open(os.devnull, "w")
            # self.fout = open("tmp.log", "a")
        else:
            os.makedirs(".debug", exist_ok=True)
            self.fout = open(f".debug/debug_{self.self_id}.log", "w")
        
        if self.self_id is None:
            self.log_out = open(os.devnull, "w")
        else:
            os.makedirs(".display", exist_ok=True)
            self.log_out = open(f".display/process_{self.self_id}.log", "w")

    def to_jsons(self):
        return json.dumps(self.to_dict())

    def from_jsons(self, string):
        self.from_dict(json.loads(string))

    def write_log(self, log):
        verify_log_format(log)
        print(str(log), file=self.log_out, flush=True)
        self.log.append(log)

    def enque_request(self, request):
        verify_request_format(request)
        heapq.heappush(self.queue, request)
        print([str(x) for x in self.queue], flush=True, file=self.fout)

    def deque_top_request(self):
        heapq.heappop(self.queue)

    def current_request(self):
        if self.queue:
            return self.queue[0]
        else:
            return None
    
    def add_ack(self, vpid):
        self.acks.append(vpid)

    def clear_acks(self):
        self.acks.clear()
    
    def can_enter_critical_section(self):
        # except itself
        return (self.requesting_critical_section 
                and self.current_request().vpid == self.self_id
                and (len(set(self.acks)) == len(self.total_addr_info) - 1))

    def enter_critical_section(self):
        self.in_critical_section = True

    def exit_critical_section(self):
        self.in_critical_section = False

    def inc_timestamp(self):
        self.lamport_timestamp += 1

    def update_timestamp(self, comming):
        self.lamport_timestamp = max(self.lamport_timestamp + 1, comming + 1)


def make_worker_ctx_from_str(s):
    ctx = WorkerContext(None, None)
    ctx.from_jsons(s)
    return ctx


def random_rest():
    randsec = random.randint(0, 5)
    time.sleep(randsec)


def lamport_worker(ctx_str):
    ctx = make_worker_ctx_from_str(ctx_str)
    print("Starting worker...", flush=True, file=ctx.fout)
    # setup server
    soc = socket.socket()
    soc.bind(ctx.total_addr_info[ctx.self_id])
    soc.listen(len(ctx.total_addr_info) * 10)
    clis = [
        socket.socket() if i != ctx.self_id else None for i in range(
            len(ctx.total_addr_info))]
    for i, (addr, port) in enumerate(ctx.total_addr_info):
        if i == ctx.self_id:
            continue
        clis[i].connect((addr, port))
        msg = struct.pack("i", ctx.self_id)
        length = len(msg)
        header = struct.pack("i", length)
        print("Send", ctx.self_id, flush=True, file=ctx.fout)
        clis[i].send(header)
        clis[i].send(msg)

    others = {}
    to_release = set()
    
    print("Establish sockets", flush=True, file=ctx.fout)
    # listen to others
    print("Try to accept...", flush=True, file=ctx.fout)
    while len(others) < len(ctx.total_addr_info) - 1:
        cl, addr = soc.accept()
        print("Accept", addr, flush=True, file=ctx.fout)
        header = cl.recv(4)
        length = struct.unpack("i", header)[0]
        msg_str = cl.recv(length)
        vpid = struct.unpack("i", msg_str)[0]
        print("Handshake value", header, msg_str, vpid, flush=True, file=ctx.fout)
        cl.setblocking(False)
        others[vpid] = cl

        for i in range(len(ctx.total_addr_info)):
            if i != ctx.self_id:
                if i not in others:
                    print("Waiting for connections from", i, "...", flush=True, file=ctx.fout)

    random_rest()

    beg = time.time()
    while time.time() - beg < MAX_WORK_TIME:
        # self need
        print("Try to send request", flush=True, file=ctx.fout)
        want_critical_section = random.random()
        if (
            want_critical_section > 0.7
            and not ctx.requesting_critical_section
            and not ctx.in_critical_section
            and ctx.compete_trials < ctx.max_compete_trials
           ):
            ctx.requesting_critical_section = True
            need_critical_section = True
            ctx.compete_trials += 1
        else:
            need_critical_section = False
        
        print("Whether to send request:", need_critical_section, flush=True, file=ctx.fout)
        if need_critical_section:
            request_timestamp = ctx.lamport_timestamp
            ctx.enque_request(RequestItem(ctx.lamport_timestamp, ctx.self_id))
            ctx.clear_acks()

            # send to others
            """for i, (addr, port) in enumerate(ctx.total_addr_info):
                print(i, addr, port, flush=True, file=ctx.fout)
                if i == ctx.self_id:
                    continue
                ctx.inc_timestamp()
                print(ctx.self_id, addr, port, type(addr), type(port), flush=True, file=ctx.fout)
                # clis[i].connect((addr, port))
                print("OK", flush=True, file=ctx.fout)
                msg = str(MessageItem(ctx.lamport_timestamp, ctx.self_id, REQUEST, str(request_timestamp))).encode()
                length = len(msg)
                header = struct.pack("i", length)
                clis[i].send(header)
                clis[i].send(msg)
                # cli.close()
                ctx.write_log(LogItem(ctx.self_id, ctx.lamport_timestamp, SEND, i, REQUEST, str(request_timestamp)))""" 
            ctx.inc_timestamp()
            for i, (addr, port) in enumerate(ctx.total_addr_info):
                print(i, addr, port, flush=True, file=ctx.fout)
                if i == ctx.self.id:
                    continue
                print(ctx.self_id, addr, port, type(addr), type(port), flush=True, file=ctx.fout)
                print("OK", flush=True, file=ctx.fout)
                msg = str(MessageItem(ctx.lamport_timestamp, ctx.self_id, REQUEST, str(request_timestamp))).encode()
                length = len(msg)
                header = struct.pack("i", length)
                clis[i].send(header)
                clis[i].send(msg)
            ctx.write_log(LogItem(ctx.self_id, ctx.lamport_timestamp, SEND, i, REQUEST, str(request_timestamp)))

        random_rest()

        for i, cl in others.items():
            try:
                header = cl.recv(4)
                length = struct.unpack("i", header)[0]
                cl.setblocking(True)
                msg_str = cl.recv(length)
                cl.setblocking(False)
            except Exception as e:
                msg_str = ""
                print("No message from", addr, flush=True, file=ctx.fout)
            if msg_str:
                msg_str = msg_str.decode()
                print("Get ", msg_str, flush=True, file=ctx.fout)
                msg = make_message_from_str(msg_str)
                ctx.update_timestamp(msg.timestamp)
                ctx.write_log(LogItem(ctx.self_id, ctx.lamport_timestamp, RECEIVE, msg.vpid, msg.info, msg.other))

                # handle the msg
                # send to others if necessary
                cli = clis[msg.vpid]
                print(cli.getsockname(), cli.getpeername(), flush=True, file=ctx.fout)
                print("Sending to", msg.vpid, flush=True, file=ctx.fout)
                if msg.info == REQUEST:
                    request_timestamp = int(msg.other)
                    ctx.enque_request(RequestItem(request_timestamp, msg.vpid))
                    ctx.inc_timestamp()
                    vmsg = str(MessageItem(ctx.lamport_timestamp, ctx.self_id, GRAND)).encode()
                    length = len(vmsg)
                    header = struct.pack("i", length)
                    clis[msg.vpid].send(header)
                    clis[msg.vpid].send(vmsg)
                    ctx.write_log(LogItem(ctx.self_id, ctx.lamport_timestamp, SEND, msg.vpid, GRAND, str(request_timestamp)))
                elif msg.info == GRAND:
                    ctx.add_ack(msg.vpid)
                elif msg.info == REFUSE:
                    raise RuntimeError("There shouldn't be REFUSE in lamport mutual exclusion")
                elif msg.info == RELEASE:
                    # assert msg.vpid == ctx.current_request().vpid
                    to_release.add(msg.vpid)
                    for vpid in to_release:
                        if ctx.current_request() is not None and ctx.current_request().vpid == vpid:
                            ctx.deque_top_request()

            print("Current top", ctx.current_request(), flush=True, file=ctx.fout)
            if ctx.can_enter_critical_section():
                ctx.requesting_critical_section = False
                ctx.enter_critical_section()

                random_rest()

                ctx.exit_critical_section()

                for i, (addr, port) in enumerate(ctx.total_addr_info):
                    if i == ctx.self_id:
                        continue
                    ctx.inc_timestamp()
                    # cli.connect((addr, port))
                    vmsg = str(MessageItem(ctx.lamport_timestamp, ctx.self_id, RELEASE, str(ctx.current_request().timestamp))).encode()
                    length = len(vmsg)
                    header = struct.pack("i", length)
                    clis[i].send(header)
                    clis[i].send(vmsg)
                    # cli.close()
                    ctx.write_log(LogItem(ctx.self_id, ctx.lamport_timestamp, SEND, i, RELEASE, str(ctx.current_request().timestamp)))
                
                ctx.deque_top_request()
                ctx.clear_acks()

        random_rest()

    for cli in clis:
        if cli is not None:
            cli.close()
    soc.close()
        
        
