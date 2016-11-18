import socket
import pickle
import threading
import queue
import time
import sys

UDP_PORT = 5005
SERVER_ADDRESS = socket.gethostbyname(socket.gethostname())
message = {}
inbox = []
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('', UDP_PORT))

def check_inbox( inbox ):
    
def forward_mail( dest, inbox ):
    for message in inbox:
        if(message['destination'] == dest):
            sock.sendto(pickle.dumps(message).encode('utf-8'),(dest,UDP_PORT))
            wait_for_ack()
            del inbox[message]

def wait_for_ack():
    while True:
        

def listen():
    data, addr = sock.recvfrom(1024)
    message = pickle.loads(data.decode('utf-8'))

    if(message['type'] == 'get'):
        forward_mail(message['source'])
    if(message['type'] == 'send'):
        inbox.append(message)
    if(message['type'] == "ack"):
        '''something else'''
    
'''main'''      
while True:
    listen()
