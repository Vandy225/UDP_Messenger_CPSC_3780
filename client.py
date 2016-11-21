import socket
import pickle
import threading
import time
import sys


'''Servers IP address'''
SERVER_IP = "10.76.134.106"
UDP_PORT = 5007
UDP_ACK_PORT = 5009
SERVER_PORT = 5005
SERVER_ACK_PORT = 5006
seq_num = 0
message = { 'seq' : seq_num, 'type' : '' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : '10.76.134.106', 'payload' : ''}
try:
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
except socket.error:
    print ("Failed to create sockets.")
    sys.exit()

#Setting up the LISTENING udp portion
sock.bind((socket.gethostbyname(socket.gethostname()),UDP_PORT))
#sock2.bind((SERVER_IP,UDP_ACK_PORT))

def user_listen():
    global SERVER_IP
    global SERVER_PORT
    msg = { 'seq' : seq_num, 'type' : 'get' , 'source' : socket.gethostbyname(socket.gethostname()), 'payload' : ''}
    print ("trying to send get")
    sock.sendto(pickle.dumps(msg),(SERVER_IP,SERVER_PORT))
    print ("waiting for server response")
    data, address = sock.recvfrom(1024)
    msg = pickle.loads(data)
    print ("Received Message: " + str(msg)) #this may change... JOSH
    #we need to be able to get the message dump, right now we are only
    #getting one messgage at a time
    #may use a loop to iterate through the messages --> need to implements ACKS
    #or use the seq number to stop iterating through the for loop
    if(msg['payload'] == 'No messages'):
        pass
        

def send_mode():
    while True:
        thing = input("Message: ")
        if(thing == ''):
            pass
        else:
            global SERVER_IP 
            global SERVER_PORT
            global seq_num
            message['seq'] = seq_num
            print ("sending message with seq_num =" + message['seq'])
            message['payload'] = thing
            message['type'] = 'send'
            sock.sendto(pickle.dumps(message),(SERVER_IP,SERVER_PORT))
            seq_num += 1
            user_listen()

#while True:
print ("starting thread 2")
t2 = threading.Thread(target =user_listen(), args=[])
t2.start()     
    
print ("starting thread 1")
t = threading.Thread(target = send_mode(), args=[])
t.start()
print ("thread 1 has started")


    
