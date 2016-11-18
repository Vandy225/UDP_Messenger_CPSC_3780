import socket
import pickle
import threading
import queue
import time
import sys


'''Servers IP address'''
UDP_IP = "142.66.140.23"
UDP_PORT = 5005
UDP_ACK_PORT = 5006
seq_num = 0
message = { 'seq' : seq_num, 'type' : '' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : '142.66.140.24', 'payload' : ''}
try:
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create sockets.'
    sys.exit()

sock.bind((UDP_IP,UDP_PORT))
sock2.bind((UDP_IP,UDP_ACK_PORT))

def user_listen():
    msg = { 'seq' : seq_num, 'type' : 'get' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : UDP_IP, 'payload' : ''}
    sock.sendto(pickle.dumps(msg).encode('utf-8'),(UDP_IP,UDP_PORT))
    while data, address = sock.recvfrom(1024):
        message = pickle.loads(data.decode('utf-8'))
        print "Message: ", message['payload'] #this may change... JOSH

def send_mode():
    message['payload'] = raw_input("Message: ")
    message['type'] = 'send'
    sock.sendto(pickle.dumps(message).encode('utf-8'),(UDP_IP,UDP_PORT))
    seq_num = seq_num + 1
    
while True:
    
    t = threading.Thread(target = send_mode(), args=[])
    t2 = threading.Thread(target = user_listen(), args=[])
    t.start()
    t2.start()
