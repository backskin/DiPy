

def precise_sleep(delay: float):
    from time import clock
    last_time = clock()
    while clock() - last_time < delay:
        pass