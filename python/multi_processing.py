import multiprocessing as multi
import signal
import psutil
import queue


class NoDaemonProcess(multi.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class NoDaemonContext(type(multi.get_context())):
    Process = NoDaemonProcess


class NoDaemonPool(multi.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs["context"] = NoDaemonContext()
        super().__init__(*args, **kwargs)

    def __reduce__(self):
        pass


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid):
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        try:
            process.send_signal(sig)
        except psutil.NoSuchProcess:
            return


def call_with_timeout(timeout, func, args=(), kwargs=None):
    def func_wrapper(que):
        if kwargs:
            que.put(func(*args, **kwargs))
        else:
            que.put(func(*args))
        
    que = multi.Queue(2)
    process = multi.Process(target=func_wrapper, args=(que,))
    process.start()
    process.join(timeout)

    try:
        res = que.get(block=False)
    except queue.Empty:
        res = TimeoutError()

    kill_child_processes(process.pid)
    process.terminate()
    process.join()
    que.close()
    que.join_thread()
    del process
    del que

    return res