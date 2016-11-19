import socket
import pickle
import threading
import time
import sys


'''Servers IP address'''
SERVER_IP = "142.66.140.23"
UDP_PORT = 5007
UDP_ACK_PORT = 5009
SERVER_PORT = 5005
SERVER_ACK_PORT = 5006
seq_num = 0
message = { 'seq' : seq_num, 'type' : '' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : '142.66.140.24', 'payload' : ''}
try:
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create sockets.'
    sys.exit()

#Setting up the LISTENING udp portion
sock.bind((socket.gethostbyname(socket.gethostname()),UDP_PORT))
#sock2.bind((SERVER_IP,UDP_ACK_PORT))

def user_listen():
    global SERVER_IP
    global SERVER_PORT
    msg = { 'seq' : seq_num, 'type' : 'get' , 'source' : socket.gethostbyname(socket.gethostname()), 'payload' : ''}
    sock.sendto(pickle.dumps(msg).encode('utf-8'),(SERVER_IP,SERVER_PORT))
    data, address = sock.recvfrom(1024)
    while data:
        message = pickle.loads(data.decode('utf-8'))
        print "Received Message: ", message['payload'] #this may change... JOSH
        if(message['payload'] == 'No messages'):
            break
        

def send_mode():
    while True:
        thing = raw_input("Message: ")
        if(thing == ''):
            pass
        else:
            global SERVER_IP 
            global SERVER_PORT
            message['payload'] = thing
            message['type'] = 'send'
            sock.sendto(pickle.dumps(message).encode('utf-8'),(SERVER_IP,SERVER_PORT))
            global seq_num 
            seq_num += 1
        
    

t = threading.Thread(target = send_mode(), args=[])
t.start()

while True:
    
    t2 = threading.Thread(target =user_listen(), args=[])
    t2.start()
    
