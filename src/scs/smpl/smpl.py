import math
import random

import sys

from scs.smpl.rand import stream

# Constants
nl = 256  # element pool length
ns = 256  # namespace length
pl = 58  # printer page length (lines used)
sl = 23  # screen page length by 'smpl'
ff = 12  # form feed

# File pointers (stdout equivalent)
display = sys.stdout  # screen display file
opf = sys.stdout  # current output destination

# Static integers
event = 0  # current simulation event
token = 0  # last token dispatched
blk = 0  # next available block index
avl = 0  # available element list header
evl = 0  # event list header
fchn = 0  # facility descriptor chain header
avn = 0  # next available namespace position
tr = 0  # event trace flag
mr = 0  # monitor activation flag
lft = sl  # lines left on current page/screen

# Static real values
clock = 0.0  # current simulation time
start = 0.0  # simulation interval start time
tl = 0.0  # last trace message issue time

# Static lists
l1 = [0] * nl  # facility descriptor
l2 = [0] * nl  # queue
l3 = [0] * nl  # event list
l4 = [0.0] * nl  # element pool
l5 = [0.0] * nl  # additional pool

# Static char list (model and facility name space)
name = [" "] * ns


# Initialization functions
def smpl(m: int, s: str):
    """
    -------------- INITIALIZE SIMULATION SUBSYSTEM ----------------
    """
    global blk, avl, avn, evl, fchn, clock, start, t1, event, tr, mr
    i = 0
    rns = 1
    blk = 1
    avl = -1
    avn = 0  # element pool & namespace headers
    evl = fchn = 0  # event list & descriptor chain headers
    clock = start = t1 = 0.0  # sim., interval start, last trace times
    event = tr = 0  # current event no. & trace flags

    for i in range(nl):
        l1[i] = l2[i] = l3[i] = 0
        l4[i] = l5[i] = 0.0

    i = save_name(s, 50)  # model name -> namespace
    rns = stream(rns)
    rns = 1 if (rns := rns + 1) > 15 else rns  # set random no. stream
    mr = 1 if m > 0 else 0  # set monitor flag
    # if mr: opf = display; init_mtr(1)


def reset():
    """-------------- RESET MEASUREMENTS ----------------"""
    global start
    resetf()
    start = clock


# Namespace and element pool allocation
def save_name(s: str, m: int) -> int:
    """-------------- SAVE NAME ----------------"""
    global avn, name
    n = min(len(s), m)
    if avn + n > ns:
        error(2, 0)  # namespace exhausted
    i = avn
    avn += n + 1
    name[i : i + n] = s[:n]
    if n == m:
        name[avn] = "\0"
    return i


def mname() -> str:
    """-------------- GET MODEL NAME ----------------"""
    return name


def fname(f: int) -> str:
    """-------------- GET FACILITY NAME ----------------"""
    return name[l3[f + 1] :]


def get_blk(n: int) -> int:
    """-------------- GET BLOCK ----------------"""
    global blk
    if blk == 0:
        error(3, 0)  # block request after schedule
    i = blk
    blk += n
    if blk >= nl:
        error(1, 0)  # element pool exhausted
    return i


def get_elm() -> int:
    """-------------- GET ELEMENT ----------------"""
    global avl, blk
    if avl <= 0:
        if avl == 0:
            error(1, 0)  # empty element list
        # if mr and not tr: init_mtr(2)
        # build the free element list from the block of elements
        # remaining after all facilities have been defined
        for i in range(blk, nl - 1):
            l1[i] = i + 1
        avl = blk
        blk = 0
    i = avl
    avl = l1[i]
    return i


def put_elm(i: int):
    """-------------- RETURN ELEMENT ----------------"""
    global avl
    l1[i] = avl
    avl = i


# Event scheduling
def schedule(ev: int, te: float, tkn: int):
    """-------------- SCHEDULE EVENT ----------------"""
    if te < 0.0:
        error(4, 0)  # negative event time
    i = get_elm()
    l2[i] = tkn
    l3[i] = ev
    l4[i] = 0.0
    l5[i] = clock + te
    enlist(evl, i)
    if tr:
        msg(1, tkn, "", ev, 0)


def cause(ev: int, tkn: int):
    """-------------- CAUSE EVENT ----------------"""
    global evl, token, event, clock
    if evl == 0:
        error(5, 0)  # empty event list
    i = evl
    tkn = token = l2[i]
    ev = event = l3[i]
    clock = l5[i]
    evl = l1[i]
    put_elm(i)  # delink element & return to pool
    if tr:
        msg(2, tkn, "", event, 0)
    # if mr and tr != 3: mtr(tr, 0)


def time() -> float:
    """-------------- RETURN TIME ----------------"""
    return clock


def cancel(ev: int):
    """-------------------- CANCEL EVENT --------------------"""
    global evl
    pred = 0
    succ = evl
    while succ != 0 and l3[succ] != ev:
        pred = succ
        succ = l1[pred]
    if succ == 0:
        return -1
    tkn = l2[succ]
    if tr:
        msg(3, tkn, "", l3[succ], 0)
    if succ == evl:
        evl = l1[succ]  # Unlink event
    else:
        l1[pred] = l1[succ]  # List entry
    put_elm(succ)  # Deallocate it
    return tkn


def suspend(tkn: int):
    """-------------------- SUSPEND EVENT --------------------"""
    global evl
    pred = 0
    succ = evl
    while succ != 0 and l2[succ] != tkn:
        pred = succ
        succ = l1[pred]
    if succ == 0:
        error(6, 0)  # No event scheduled for token
    if succ == evl:
        evl = l1[succ]  # Unlink event
    else:
        l1[pred] = l1[succ]  # List entry
    if tr:
        msg(6, -1, "", l3[succ], 0)
    return succ


# List processing
def enlist(head: list, elm: int):
    """-------------------- ENTER ELEMENT IN QUEUE OR EVENT LIST --------------------"""
    pred = 0
    succ = head[0]
    arg = l5[elm]
    while True:
        if succ == 0:
            break  # End of list
        v = l5[succ]
        if head[0] == evl:
            # Event list
            if v > arg:
                break
        else:
            # Queue: If entry is for a preempted token
            # (l4, the remaining event time, >0), insert
            # Entry at beginning of its priority class;
            # Otherwise, insert it at the end
            if v < arg or (v == arg and l4[elm] > 0.0):
                break
        pred = succ
        succ = l1[pred]
    l1[elm] = succ
    if succ != head[0]:
        l1[pred] = elm
    else:
        head[0] = elm


# Facility definition, operation, and query
def facility(s: str, n: int) -> int:
    """-------------------- DEFINE FACILITY --------------------"""
    global fchn
    f = get_blk(n + 2)
    l1[f] = n
    l3[f + 1] = save_name(s, 14 if n > 1 else 17)
    if fchn == 0:
        fchn = f
    else:
        i = fchn
        while l2[i + 1]:
            i = l2[i + 1]
        l2[i + 1] = f
    l2[f + 1] = 0
    if tr:
        msg(13, -1, fname(f), f, 0)
    return f


def resetf():
    """-------------------- RESET FACILITY & QUEUE MEASUREMENTS --------------------"""
    global start, clock
    i = fchn
    while i:
        l4[i] = l4[i + 1] = l5[i + 1] = 0.0
        for j in range(i + 2, i + l1[i] + 1):
            l3[j] = 0
            l4[j] = 0.0
        i = l2[i + 1]  # Advance to next facility
    start = clock


def request(f: int, tkn: int, pri: int) -> int:
    """-------------------- REQUEST FACILITY --------------------"""
    global tr
    if l2[f] < l1[f]:
        # Facility nonbusy - reserve 1st-found nonbusy server
        for i in range(f + 2, f + l1[f] + 1):
            if l1[i] == 0:
                break
        l1[i] = tkn
        l2[i] = pri
        l5[i] = clock
        l2[f] += 1
        r = 0
    else:
        # Facility busy - enqueue token marked with event and priority
        enqueue(f, tkn, pri, event, 0.0)
        r = 1
    if tr:
        msg(7, tkn, fname(f), r, l3[f])
    return r


def enqueue(f: int, j: int, pri: int, ev: int, te: float):
    """-------------------- ENQUEUE TOKEN --------------------"""
    global clock
    l5[f + 1] += l3[f] * (clock - l5[f])
    l3[f] += 1
    l5[f] = clock
    i = get_elm()
    l2[i] = j
    l3[i] = ev
    l4[i] = te
    l5[i] = float(pri)
    enlist(l1[f + 1], i)


def preempt(f: int, tkn: int, pri: int) -> int:
    """-------------------- PREEMPT FACILITY --------------------"""
    global tr
    if l2[f] < l1[f]:
        # Facility nonbusy - locate 1st-found nonbusy server
        k = f + 2
        while l1[k] != 0:
            k += 1
        r = 0
        if tr:
            msg(8, tkn, fname(f), 0, 0)
    else:
        # Facility busy - find server with lowest-priority user
        k = f + 2
        j = l1[f] + f + 1
        for i in range(f + 2, j + 1):
            if l2[i] < l2[k]:
                k = i
        if pri <= l2[k]:
            # Requesting token's priority is not higher than any user
            enqueue(f, tkn, pri, event, 0.0)
            r = 1
            if tr:
                msg(7, tkn, fname(f), r, l3[f])
        else:
            # Preempt user of server k, suspend event, save event number and remaining time
            j = l1[k]
            i = suspend(j)
            ev = l3[i]
            te = l5[i] - clock
            if te == 0.0:
                te = 1.0e-99
            put_elm(i)
            enqueue(f, j, l2[k], ev, te)
            if tr:
                msg(10, -1, "", j, l3[f])
                msg(12, -1, fname(f), tkn, 0)
            l3[k] += 1
            l4[k] += clock - l5[k]
            l2[f] -= 1
            l4[f + 1] += 1
            r = 0
    if r == 0:
        # Reserve server k of facility
        l1[k] = tkn
        l2[k] = pri
        l5[k] = clock
        l2[f] += 1
    return r


def release(f: int, tkn: int):
    """-------------------- RELEASE FACILITY --------------------"""
    global tr
    j = 0
    k = f + 1 + l1[f]  # Index of last server element
    for i in range(f + 2, k + 1):
        if l1[i] == tkn:
            j = i
            break
    if j == 0:
        error(7, 0)  # No server reserved
    l1[j] = 0
    l3[j] += 1
    l4[j] += clock - l5[j]
    l2[f] -= 1
    if tr:
        msg(9, tkn, fname(f), 0, 0)
    if l3[f] > 0:
        # Queue not empty: dequeue request and update queue measures
        k = l1[f + 1]
        l1[f + 1] = l1[k]
        te = l4[k]
        l5[f + 1] += l3[f] * (clock - l5[f])
        l3[f] -= 1
        if tr:
            msg(11, -1, "", l2[k], l3[f])
        if te == 0.0:
            # Blocked request: place request at head of event list
            # so its facility request can be re-initiated before other requests
            l5[k] = clock
            l1[k] = evl
            evl = k
            m = 4
        else:
            # Return after preemption: reserve facility for dequeued request
            # and reschedule remaining event time
            l1[j] = l2[k]
            l2[j] = int(l5[k])
            l5[j] = clock
            l2[f] += 1
            if tr:
                msg(12, -1, fname(f), l2[k], 0)
            l5[k] = clock + te
            enlist(evl, k)
            m = 5
    if tr:
        msg(m, -1, "", l3[k], 0)


def status(f: int) -> int:
    """-------------------- GET FACILITY STATUS --------------------"""
    return 1 if l1[f] == l2[f] else 0


def inq(f: int) -> int:
    """-------------------- GET CURRENT QUEUE LENGTH --------------------"""
    return l3[f]


def U(f: int) -> float:
    """-------------------- GET FACILITY UTILIZATION --------------------"""
    b = 0.0
    t = clock - start
    if t > 0.0:
        for i in range(f + 2, f + l1[f] + 2):
            b += l4[i]
        return b / t
    return 0.0


def B(f: int) -> float:
    """-------------------- GET MEAN BUSY PERIOD --------------------"""
    b = 0.0
    n = 0
    for i in range(f + 2, f + l1[f] + 2):
        b += l4[i]
        n += l3[i]
    return (b / n) if n > 0 else b


def Lq(f: int) -> float:
    """-------------------- GET AVERAGE QUEUE LENGTH --------------------"""
    t = clock - start
    return (l5[f + 1] / t) if t > 0.0 else 0.0


# Debugging and reporting
def trace(n: int):
    """-------------------- TURN TRACE ON/OFF --------------------"""
    global tr, tl
    match n:
        case 0:
            tr = 0
        case 1:
            pass
        case 2:
            pass
        case 3:
            tr = n
            tl = -1.0
            newpage()
        case 4:
            end_line()
        case _:
            pass


def msg(n: int, i: int, s: str, q1: int, q2: int):
    """-------------------- GENERATE TRACE MESSAGE --------------------"""
    global clock, t1
    m = [
        "",
        "SCHEDULE",
        "CAUSE",
        "CANCEL",
        "RESCHEDULE",
        "RESUME",
        "SUSPEND",
        "REQUEST",
        "PREEMPT",
        "RELEASE",
        "QUEUE",
        "DEQUEUE",
        "RESERVE",
        "FACILITY",
    ]

    if clock > t1:  # Print time stamp if time has advanced
        t1 = clock
        print(f" time {clock:12.3f}", end="")
    else:
        print(f"{'':21}", end="")

    if i >= 0:  # Print token number if specified
        print(f"-- token {i:4d}", end="")
    else:
        print("--", end="")

    print(f"{m[n]} {s}", end="")  # Print basic message

    match n:
        case 6:
            print(f" EVENT {q1}", end="")
        case 8:
            match q1:
                case 0:
                    print(" RESERVED", end="")
                case 1:
                    print(f": QUEUED (inq = {q2})", end="")
                case 2:
                    print(": INTERRUPT", end="")
        case 11:
            print(f" token {q1} (inq = {q2})", end="")
        case 12:
            print(f" for token {q1}", end="")
        case 13:
            print(f": f = {q1}", end="")

    print()
    end_line()


def end_line():
    """-------------------- TRACE LINE END --------------------"""
    global lft, tr
    lft -= 1
    if lft == 0:
        match tr:
            case 1:
                if opf == display:
                    lft = sl
                else:
                    endpage()
            case 2:
                if mr:
                    print("\n")
                    lft = sl
                    pause()
                else:
                    endpage()
            case 3:
                lft = sl
    if tr == 3:
        pause()


def pause():
    """-------------------- PAUSE --------------------"""
    input()  # Simulates getchar() in C


def error(n: int, s: str):
    """-------------------- DISPLAY ERROR MESSAGE & EXIT --------------------"""
    global clock, opf, display
    messages = [
        "Simulation Error at Time ",
        "Empty Element Pool",
        "Empty Name Space",
        "Facility Defined After Queue/Schedule",
        "Negative Event Time",
        "Empty Event List",
        "Preempted Token Not in Event List",
        "Release of Idle/Unowned Facility",
    ]

    dest = opf
    while True:
        print(f"\n**** {messages[0]}{clock:.3f}", file=dest)
        if n:
            print(f"{messages[n]}", file=dest)
        if s:
            print(f"{s}", file=dest)
        if dest == display:
            break
        else:
            dest = display

    if opf != display:
        report()
    exit(0)


def report():
    """-------------------- GENERATE REPORT --------------------"""
    newpage()
    reportf()
    endpage()


def reportf():
    """-------------------- GENERATE FACILITY REPORT --------------------"""
    global fchn
    if fchn == 0:
        print("\nno facilities defined: report abandoned\n")
    else:
        # f = 0 at end of facility chain
        f = fchn
        while f:
            f = rept_page(f)
            if f > 0:
                endpage()


def rept_page(fnxt: int) -> int:
    """-------------------- GENERATE REPORT PAGE --------------------"""
    f = fnxt
    headers = [
        "SMPL SIMULATION REPORT",
        "MODEL: ",
        "TIME: ",
        "INTERVAL: ",
        "MEAN BUSY",
        "MEAN QUEUE",
        "OPERATION COUNTS",
        "FACILITY UTIL.",
        "PERIOD LENGTH",
        "RELEASE",
        "PREEMPT",
        "QUEUE",
    ]

    print(f"\n{headers[0]:>51}\n\n\n")
    print(f"{' '*4}{headers[1]}{mname()} {headers[2]}{clock:11.3f}")
    print(f"{' '*68}{headers[3]}{clock-start:11.3f}\n\n")
    print(f"{' '*75}{headers[4]}")
    print(f"{headers[5]} {headers[6]}")

    global lft
    lft -= 8
    while f and lft > 0:
        n = sum(l3[i] for i in range(f + 2, f + l1[f] + 2))
        fname_str = fname(f) if l1[f] == 0 else f"{fname(f)}[{l1[f]}]"
        print(
            f"{fname_str:<17} {U(f):6.4f} {B(f):10.3f} {Lq(f):13.3f} {n:11d} {int(l4[f+1]):9d} {int(l4[f]):7d}"
        )
        f = l2[f + 1]
    return f


def lns(i: int) -> int:
    """-------------------- COUNT LINES --------------------"""
    global lft
    lft -= i
    if lft <= 0:
        endpage()
    return lft


def endpage():
    """-------------------- END PAGE --------------------"""
    global lft, opf, display
    if opf == display:
        # Screen output: push to top of screen & pause
        while lft > 0:
            print("\n", end="")
            lft -= 1
        print("\n(ENTER) to continue:", end="")
        input()
        print("\n\n")
    else:
        if lft < pl:
            print("\f", end="")
    newpage()


def newpage():
    """-------------------- NEW PAGE --------------------"""
    global lft, opf, display, sl, pl
    # Set line count to top of page/screen after page change/screen
    # Clear by 'smpl', another SMPL module, or simulation program
    lft = sl if opf == display else pl


def sendto(dest):
    """-------------------- REDIRECT OUTPUT --------------------"""
    global opf
    if dest:
        opf = dest
    return opf
