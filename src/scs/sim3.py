from scs.smpl.smpl import (
    smpl,
    schedule,
    time,
    cause,
    report,
    expntl,
    facility,
    request,
    release,
)


def main():
    Ta = 200.0
    Ts = 100.0
    te = 200000.0
    customer = 1
    event = None
    server = None
    smpl(1, "M/M/1 Queue")
    server = facility("server", 1)
    schedule(1, 0.0, customer)
    while time() < te:
        cause(event, customer)

        match event:
            case 1:  # arrival
                schedule(2, 0.0, customer)
                schedule(1, expntl(Ta), customer)
                break
            case 2:  # request server
                if request(server, customer, 0) == 0:
                    schedule(3, expntl(Ts), customer)
                break
            case 3:  # completion
                release(server, customer)
                break
    report()


if __name__ == "__main__":
    main()
