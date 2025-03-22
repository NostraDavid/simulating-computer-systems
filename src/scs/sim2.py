from scs.smpl import expntl
from structlog.stdlib import get_logger

logger = get_logger(__name__)


def main() -> None:
    Ta: float = 200.0
    Ts: float = 100.0
    te: float = 200000.0

    n: int = 0  # number of customers in the system
    t1: float = 0.0  # next arrival time
    t2: float = te  # next completion time
    time: float = 0.0

    # Counters and accumulators
    B: float = 0.0  # total busy time
    s: float = 0.0  # last event time
    C: float = 0.0  # accumulated waiting in queue
    tb: float = 0.0  # time-integrated number of customers in the system
    tn: float = 0.0  # last update time

    while time < te:
        if t1 < t2:  # event 1: arrival
            time = t1
            s += n * (time - tn)
            n += 1
            tn = time
            t1 = time + expntl(Ta)
            if n == 1:
                tb = time
                t2 = time + expntl(Ts)
        else:  # event 2: completion
            time = t2
            s += n * (time - tn)
            n -= 1
            tn = time
            C += 1
            if n > 0:
                t2 = time + expntl(Ts)
            else:
                t2 = te
                B += time - tb

    X: float = C / time  # "throughput" as in the figure
    U: float = B / time  # utilization
    L: float = s / time  # average number in system
    W: float = L / X  # mean wait in queue

    logger.info("throughput", X=X)
    logger.info("utilization", U=U)
    logger.info("mean no. in system", L=L)
    logger.info("mean residence time", W=W)


if __name__ == "__main__":
    main()
