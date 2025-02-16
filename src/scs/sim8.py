import math
import random
from structlog.stdlib import get_logger
from scs.smpl import (
    smpl,
    facility,
    schedule,
    cause,
    time,
    request,
    release,
    U,
    status,
)

logger = get_logger(__name__)

# Constants
busy = 1
p = 0.250  # Local memory miss rate
treq = [0.0] * 17  # Next request time for processor
tn = 1.0e6  # Earliest-occurring request time
N = 8  # Number of processors
M = 4  # Number of memories
nB = 2  # Number of buses
module = [None] * 17  # Memory & bus facility descriptors
bus = None  # Bus facility descriptor
nbs = 0  # Number of busy buses in current cycle
req = [0] * 17  # Currently-requested memory module
next = 1  # Arbitration scan starting point


def main():
    """MEMORY-BUS BANDWIDTH MODEL"""
    global bus
    event, n = 0, 0
    smpl(0, "Bandwidth Model")
    bus = facility("bus", nB)
    for i in range(1, M + 1):
        module[i] = facility("module", 1)
    for n in range(1, N + 1):
        req[n] = 0
        next_access(n)
    schedule(1, tn, 0)
    while time() < 10000.0:
        cause(event, n)
        match event:
            case 1:
                begin_cycle()
            case 2:
                req_module(n)
            case 3:
                end_cycle(n)
    print(f"BW = {U(bus):.3f}")


def next_access(n: int):
    """COMPUTE NEXT MEMORY ACCESS TIME"""
    global tn
    t = math.floor(math.log(random.random()) / math.log(1.0 - p)) + time()
    treq[n] = t
    if t < tn:
        tn = t


def begin_cycle():
    """EVENT 1: BEGIN CYCLE"""
    global next, tn
    n = next
    tmin = 1.0e6
    for i in range(N):
        if req[n] == 0:
            # in this version, req[n] is always 0 here
            if (t := treq[n]) == tn:
                req[n] = random.randint(1, M)
                schedule(2, 0.0, n)
            elif t < tmin:
                tmin = t
        n = (n % N) + 1
    next = (next % N) + 1
    tn = tmin


def req_module(n: int):
    """EVENT 2: REQUEST MEMORY AND BUS"""
    global nbs, tn
    if status(module[req[n]]) != busy and status(bus) != busy:
        request(module[req[n]], n, 0)
        request(bus, n, 0)
        nbs += 1
        schedule(3, 1.0, n)
    else:
        req[n] = 0
        treq[n] += 1
        if treq[n] < tn:
            tn = treq[n]


def end_cycle(n: int):
    """EVENT 3: END CYCLE"""
    global nbs
    release(bus, n)
    release(module[req[n]], n)
    req[n] = 0
    next_access(n)
    nbs -= 1
    if nbs == 0:
        schedule(1, tn - time(), 0)


if __name__ == "__main__":
    main()
