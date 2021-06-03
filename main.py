from python.worker import WorkerContext, lamport_worker
from python.launch_process import launch_process


def lamport_work(num_process=4):
    port_begin = 12345
    port_stride = 1
    ports = [port_begin + x * port_stride for x in range(num_process)]
    addrs = [
        ("127.0.0.1", x) for x in ports
    ]
    ctx_lst = [
        WorkerContext(addrs, i) for i, addr in enumerate(addrs)
    ]

    ctx_str_lst = [x.to_jsons() for x in ctx_lst]
    
    print("Begin lamport...", flush=True)
    launch_process(lamport_worker, num_process, ctx_str_lst)
    print("Done", flush=True)


if __name__ == "__main__":
    lamport_work()