import random
from scs.smpl import (
    erlang,
)
from scs.smpl.smpl import (
    expntl,
    facility,
    smpl,
    preempt,
    cause,
    release,
    request,
    schedule,
    time,
)

from dataclasses import dataclass
from structlog.stdlib import get_logger

logger = get_logger(__name__)


def main():
    n0 = 6  # no. class 0 tasks
    n1 = 3  # no. class 1 tasks
    nt = n0 + n1  # total no. of tasks
    nd = 4  # no. of disk units
    qd = 1  # queued req. return

    @dataclass
    class Token:
        cls: int = 0  # task's class (& priority)
        un: int = 0  # unit for current IO req.
        ts: float = 0.0  # tour start time stamp

    task: list[Token] = [Token() for _ in range(nt + 1)]
    disk = [None] * (nd + 1)
    cpu = None
    nts = 10000  # no. of tours to simulate
    tc = [10.0, 5.0]  # class 0,1 mean cpu times
    td, sd = 30.0, 7.5  # disk time mean, std. dev.

    n = [0, 0]
    s = [0.0, 0.0]

    for i in range(1, nt + 1):
        task[i].cls = 1 if i > n0 else 0

    smpl(0, "central server model")
    cpu = facility("CPU", 1)
    for i in range(1, nd + 1):
        disk[i] = facility("disk", 1)
    for i in range(1, nt + 1):
        schedule(1, 0.0, i)

    while nts:
        event = None
        i = None
        cause(event, i)
        p: Token = task[i]

        match event:
            case 1:  # begin tour
                p.ts = time()
                schedule(2, 0.0, i)
                break
            case 2:  # request cpu
                j = p.cls
                if preempt(cpu, i, j) != qd:
                    schedule(3, expntl(tc[j]), i)
                break
            case 3:  # release cpu, select disk
                release(cpu, i)
                p.un = random.randint(1, nd)
                schedule(4, 0.0, i)
                break
            case 4:  # request disk
                if request(disk[p.un], i, 0) != qd:
                    schedule(5, erlang(td, sd), i)
                break
            case 5:  # release disk, end tour
                release(disk[p.un], i)
                j = p.cls
                t = time()
                s[j] += t - p.ts
                p.ts = t
                n[j] += 1
                schedule(1, 0.0, i)
                nts -= 1
                break

    logger.info("class 0 tour time", tour_time=f"{s[0] / n[0]:.2f}")
    logger.info("class 1 tour time", tour_time=f"{s[1] / n[1]:.2f}")


if __name__ == "__main__":
    main()
