import multiprocessing as multi
from multiprocessing import Pool, TimeoutError


def launch_process(func, num_process, args_lst):
    with Pool(processes=num_process) as pool:
        results = pool.map(func, args_lst)
        print(results)
        return results