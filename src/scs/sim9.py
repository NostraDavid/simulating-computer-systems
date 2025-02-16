from scs.smpl.smpl import request, schedule, time, release
from scs.sim8 import next_access


# Constants
N = 8  # Number of processors
M = 4  # Number of memories
nbs = 0  # Number of busy buses in current cycle
module = [None] * 17  # Memory facility descriptors
bus = None  # Bus facility descriptor
req = [0] * 17  # Currently-requested memory module
tn = 1.0e6  # Earliest-occurring request time


def req_module(n: int):
    if request(module[req[n]], n, 0) == 0:
        schedule(3, 0.0, n)


def req_bus(n: int):
    global nbs
    if request(bus, n) == 0:
        nbs += 1
        schedule(4, 1.0, n)


def end_cycle(n: int):
    global nbs
    req[n] = -req[n]
    nbs -= 1
    if nbs == 0:
        for n in range(1, N + 1):
            if req[n] < 0:
                release(bus, n)
                release(module[-req[n]], n)
                req[n] = 0
                next_access(n)
        schedule(1, tn - time(), 0)
