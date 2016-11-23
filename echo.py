import multiprocessing as mp
from multiprocessing import Process
import sys
import os

def echo_input(fileno):
    sys.stdin = os.fdopen(fileno)
    while True:
        thing = input("echo: ")
        print(thing)


if(__name__ == "__main__"):
    mp.set_start_method('spawn')

    fn = sys.stdin.fileno()
    p = Process(target=echo_input, args=(fn,))
    p.start()