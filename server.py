import socket
import pickle
import threading
import queue
import time
import sys

UDP_PORT = 5005
UDP_ACK_PORT = 5006
SERVER_ADDRESS = socket.gethostbyname(socket.gethostname())
SERVER_ID = 'Server Host'
 msg = { 'seq' : , 'type' : '' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : , 'payload' : ''}

try:
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create sockets.'
    sys.exit()

sock.bind(('', UDP_PORT))
sock2.bind(('', UDP_ACK_PORT))

print "server started on port: ", UDP_PORT

#data structure for messages per client. { client ip : [list of messages] }
message_list = { client_ip : [] }
client_list = {}

message_queue = queue.Queue(maxsize = 0)
ack_queue = queue.Queue(maxsize = 0)

#iterate over the list of stored messages for a particular client.
#Send each message individually.
def deliver_messages(dest, msg):
    if not message_list[dest]:
        mess = { 'seq' : , 'type' : '' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : dest, 'payload' : 'No messages.'}
        sock.sendto(pickle.dump(mess).encode('utf-8'),(dest,UDP_PORT))
    else:
        for client_ip in message_list:
            if(dest == client_ip):
                for message in client_ip:
                    sock.sendto(pickle.dump(message).encode('utf-8'),(dest,UDP_PORT))

#store the message for destination in the list. 
def store_message(dest, msg):
    message_list[dest].append(msg)

def receive_message(data, address):
    message = pickle.loads(data.decode('utf-8'))#This may change

    if(message['type'] == 'send'):
        store_message(message['destination'], message)
    if(message['type'] == 'get'):
        deliver_messages(message['destination'],  message)
    
def listen_mode():
    while True:
        data, address = sock.recvfrom(1024)
        data2, addr = sock2.recvfrom(1024)

        t = threading.Thread(target = receive_message, args=[data, address])
        t2 = threading.Thread(target = '''Ack_reception function''', args = [data2, addr])

        t.start()
        t2.start()

'''
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
while True:
    listen()
'''
