import random
from scs.smpl import (
    smpl,
    schedule,
    time,
    cause,
    report,
    request,
    release,
    facility,
    expntl,
)


# Constants
queued = 1
p = 0.250  # Local memory miss rate
N = 8  # Number of processors
M = 4  # Number of memories
nB = 2  # Number of buses
module = [None] * 17  # Facility descriptors for modules
bus = None  # Facility descriptor for buses
req = [0] * 17  # Currently-requested memory module


def main():
    global bus
    x = 1.0 / p - 1.0
    smpl(0, "Bandwidth Model")
    bus = facility("bus", nB)
    for i in range(1, M + 1):
        module[i] = facility("module", 1)
    for n in range(1, N + 1):
        req[n] = random.randint(1, M)
        schedule(1, expntl(x), n)
    while time() < 10000.0:
        event, n = 0, 0
        cause(event, n)
        if request(module[req[n]], n, 0) != queued:
            schedule(2, 0.0, n)
        elif event == 2:
            if request(bus, n, 0) != queued:
                schedule(3, 1.0, n)
        elif event == 3:
            release(bus, n)
            release(module[req[n]], n)
            req[n] = random.randint(1, M)
            schedule(1, expntl(x), n)
    report()


if __name__ == "__main__":
    main()
