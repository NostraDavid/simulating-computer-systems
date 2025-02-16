from dataclasses import dataclass
import math
import random
from scs.smpl import smpl, schedule, cause, time, cancel, expntl
from scs.sim6 import init_bm, obs, civals

# Constants
busy = 1
idle = 0
Na = 200  # max. no. of active stations
Tp = 0.0225  # propagation delay (ms)
Tif = 0.0096  # interframe delay (ms)
Tslot = 0.0512  # slot time (ms)
Tjam = 0.0032  # jam time (ms)


@dataclass
class Request:
    attempt = 0  # no. retransmission attempts
    bkf = 0  # current backoff count
    lnk = 0  # avai/defer wait list link
    tin = 0.0  # request initiation time
    txf = 0.0  # request's transmission time


desc = [Request() for _ in range(Na + 1)]

# Network parameters
N = 200  # no. of stations in network
chnl = idle  # channel status (busy/idle)
avl = 1  # avail. descriptor list head
dfr = 0  # defer wait list head
end = 0  # run termination flag

a = 0.05  # propagation/transfer time ratio
G = 0.50  # offered load: G=N*Tf(Ti+Tf)
Tf = 0.0  # mean frame transmission time
Ti = 0.0  # mean inter-request time/station
tbs = 0.0  # channel busy start times
tis = 0.0  # channel idle start times
tfsum = 0.0  # frame transmission time sum


def main():
    global Tf, Ti
    Td, hw, nb = 0.0, 0.0, 0
    event, stn = 0, 0
    Tf = Tp / a
    Ti = Tf * (N / G - 1.0)
    smpl(0, "Ethernet Local Area Network")
    for stn in range(1, Na + 1):
        desc[stn].lnk = stn + 1
    desc[Na].lnk = 0
    init_bm(2000, 2000)
    schedule(1, Tp, 0)
    while not end:
        cause(event, stn)
        match event:
            case 1:
                TransmitFrame()
                break
            case 2:
                Defer(stn)
                break
            case 3:
                StartTransmit(stn)
                break
            case 4:
                EndTransmit(stn)
                break
            case 5:
                InitBackoff(stn)
                break
            case 6:
                Deassert()
                break

    civals(Td, hw, nb)
    print(f"S = {tfsum / time():.3f}")
    print(f"D = {Td / Tf:.3f} +/- {hw / Tf:.3f}")


def dly() -> float:
    return Tp * (1.0 - math.sqrt(random.random()))


def maxm(x: float, y: float) -> float:
    return max(x, y)


def TransmitFrame():
    global N, avl
    if avl:  # allocate & build request descriptor
        stn = avl
        p = desc[stn]
        avl = p.lnk
        p.attempt = p.bkf = 0
        p.tin = time()
        p.txf = Tf
        schedule(2, 0.0, stn)
        N -= 1
    if N:
        schedule(1, expntl(Ti / N), 0)


def Defer(stn: int):
    global dfr
    dt = dly()
    p = desc[stn]
    if chnl == busy and time() > (tbs + dt + Tif):
        p.lnk = dfr
        dfr = stn
    else:
        schedule(3, maxm(tis + dt + Tif - time(), 0.0), stn)


def StartTransmit(stn: int):
    global chnl, tbs
    t = time()
    p = desc[stn]
    if chnl == idle:  # reserve channel & schedule EndTransmit
        chnl = busy
        tbs = t
        ncls = 0
        schedule(4, p.txf, stn)
    else:  # collision will occur in tc ms
        dt = dly()
        tc = maxm(tbs + dt - t, 0.0)
        ncls += 1
        if ncls == 1:  # cancel EndTransmit event
            schedule(5, Tjam + dt, cancel(4))
            schedule(6, maxm(Tjam + dt, tbs + Tp - t), 0)
        schedule(5, Tjam + tc, stn)


def EndTransmit(stn: int):
    """end successful frame transmission"""
    global tfsum
    p = desc[stn]
    tfsum += p.txf
    EndRequest(stn)
    schedule(6, 0.0, 0)


def InitBackoff(stn: int):
    global dfr
    p = desc[stn]
    p.attempt += 1
    if p.attempt > 16:
        EndRequest(stn)  # Abandon request
    else:  # compute and schedule backoff delay
        if p.attempt == 1:
            p.bkf = 2
        elif p.bkf < 1024:
            p.bkf *= 2
        k = random.randint(0, p.bkf - 1)
        if k == 0:
            p.lnk = dfr
            dfr = stn
        else:
            schedule(2, Tslot * k, stn)


def Deassert():
    global chnl, tis, dfr
    chnl = idle
    tis = time()
    while dfr:  # activate requests on defer wait list
        schedule(3, dly() + Tif, dfr)
        dfr = desc[dfr].lnk


def EndRequest(stn: int):
    """deallocate descdriptor, reschedule next arrival"""
    global avl, N, end
    p = desc[stn]
    end = obs(time() - p.tin)
    p.lnk = avl
    avl = stn
    N += 1
    cancel(1)
    schedule(1, expntl(Ti / N), 0)


if __name__ == "__main__":
    main()
