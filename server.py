import socket
import pickle
import threading
from multiprocessing import Queue, Process
import time
import sys

UDP_PORT = 5005
UDP_ACK_PORT = 5006
SERVER_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
SERVER_ID = 'Server Host'
message_queue = Queue() # declare the message queue
message_list = { 'client_ip' : [] } #THIS IS ACTUALLY A MESSAGE DICTIONARY
client_dict = {'client_ip': ""} # this the list of connected clients
message_queue.put(message_list) # now we have an empty dictionary in the queue

def receive_message(message_queue):
    data, address = sock.recvfrom(1024)  # listen on socket for messages
    print("Attempting to decode the death star plans...")
    message = pickle.loads(data)  # load received data into message
    print("MESSAGE RAW: ", str(message))  # show the contents of the message for now
    # if the message is of type 'send', output flag, call store_message
    if (message['type'] == 'send'):
        print("Message recieved, storing...")
        store_message(message['destination'], message, message_queue)
    if (message['type'] == 'get'):
        print("Deliver messages...")
        deliver_messages(message['source'], message, address, message_queue)
    if (message['type'] == 'ack'):
        handle_acknowledgement(message['payload'], message['source'], message_queue)
    if (message ['type'] == 'handshake'):
        print ("Trying to handshake...\n")
        handshake(sock, message['source'])

    # iterate over the list of stored messages for a particular client.
    # Send each message individually.
def deliver_messages(dest, msg, address, message_queue):
    message_dict = message_queue.get()
    if dest not in message_dict:
        print("Not in the message dictionary yet...")
        # send a no message response. Inbox is empty
        hot_mess = []
        sock.sendto(pickle.dumps(hot_mess), (dest, address[1]))
    else:
        # We are going to either want to fix client to listen properly, or make the server send all client dicts in a array or something.
        client_msgs = message_dict[dest]
        print("client msgs to deliver" + str(client_msgs))
        sock.sendto(pickle.dumps(client_msgs), (dest, address[1]))
    message_queue.put(message_dict)
        # wait for some amount of time in order to get all the acks from client for messages in sent list.
        # Waiting for ACKS needs to happen right here. An ACK function should be used. The message queue will not
        # be used by the ACK handler
        # Will be waiting to clear the message list for the client.

    # store the message for destination in the list.
def store_message(dest, msg, message_queue):
    message_dict = message_queue.get()  # get the dictionary from the queue
    if dest in message_dict:
        print("dest already in list, adding msg to it")
        message_dict[dest].append(msg)  # put the entry in the dictionary of lists of dictionaries
        message_queue.put(message_dict)  # put the dictionary in the queue

    else:
        print("dest not in list, creating new list")
        newList = []
        newList.append(msg)
        message_dict[dest] = newList
        message_queue.put(message_dict)

def handle_acknowledgement(seq_list, client, message_queue):
    print("Acknowledging Messagees...")
    message_dict = message_queue.get()
    list_of_messages = message_dict[client]
    for idx in list_of_messages[:]:
        if idx['seq'] in seq_list:
            list_of_messages.remove(idx)
            print("Removed message: ", str(idx['seq']))
    message_dict[client] = list_of_messages
    message_queue.put(message_dict)

def handshake(sock, source):
    global client_dict
    global message_list
    print ("Recieved handshake.\n")
    #sock.sendto(pickle.dumps(client_dict), (source, address[1])) #send this to the person handshaking
    client_dict[source] = source #add a new entry in the dictionary for the connected client
    message_list[source] = [] #Create a mailbox for the client on this server.
    # this connection shit is fine
try:
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
except socket.error:
    print ("Failed to create sockets.")
    sys.exit()

#server will listen to any IP using it's ports.
sock.bind(('', UDP_PORT))
sock2.bind(('', UDP_ACK_PORT))

print ("server started on port: " + str(UDP_PORT))

#data structure for messages per client. { client ip : [list of messages] }


if __name__ == '__main__':
    while True:
        receive_message(message_queue)
        #should do some sort of time_elapsed - run_time > something check so that we do this every once in a while.
        #Flood clients with handshakes in order to ensure that they are still connected
        #Probably flood other servers here too.
        #Adding a comment
