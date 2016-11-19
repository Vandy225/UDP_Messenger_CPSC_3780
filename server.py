import socket
import pickle
import threading
import time
import sys

UDP_PORT = 5005
UDP_ACK_PORT = 5006
SERVER_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
SERVER_ID = 'Server Host'

try:
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create sockets.'
    sys.exit()

#server will listen to any IP using it's ports.
sock.bind(('', UDP_PORT))
sock2.bind(('', UDP_ACK_PORT))

print "server started on port: ", UDP_PORT

#data structure for messages per client. { client ip : [list of messages] }
message_list = { 'client_ip' : [] }
client_list = {}


#iterate over the list of stored messages for a particular client.
#Send each message individually.
def deliver_messages(dest, msg, address):
    if dest not in message_list:
        print 'No messages for you...'
        #send a no message response. Inbox is empty
        hot_mess = { 'seq' : '', 'type' : '' , 'source' : SERVER_ADDRESS, 'destination' : dest, 'payload' : 'No messages.' }
        sock.sendto(pickle.dumps(hot_mess).encode('utf-8'), (address[0], address[1]))
    else:
#We are going to either want to fix client to listen properly, or make the server send all client dicts in a array or something.
        client_msgs = message_list[dest]
        print "client msgs to deliver" + str(client_msgs)
        for msg in client_msgs:
            sock.sendto(pickle.dumps(msg).encode('utf-8'),(address[0],address[1]))


#store the message for destination in the list. 
def store_message(dest, msg):
    if dest in message_list:
        print "dest already in list, adding msg to it"
        message_list[dest].append(msg)
    else: 
        print "dest not in list, creating new list"
        newList = []
        newList.append(msg)
        message_list[dest] = newList

def receive_message(data, address):
    print 'Attempting to decode the death star plans...'
    message = pickle.loads(data.decode('utf-8'))#This may change
    print 'MESSAGE RAW: ', str(message)

    if(message['type'] == 'send'):
        print 'Message recieved, storing...'
        store_message(message['destination'], message)
    if(message['type'] == 'get'):
        print 'Deliver messages...'
        deliver_messages(message['source'],  message, address)
    
def listen_mode():
    print 'listen for data....'
    data, address = sock.recvfrom(1024)
    #data2, addr = sock2.recvfrom(1024)
    print 'thread start...'
    t = threading.Thread(target = receive_message, args=[data, address])
    #t2 = threading.Thread(target = '''Ack_reception function''', args = [data2, addr])
    
    t.start()
    #t2.start()
    

while True:
    listen_mode()

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
