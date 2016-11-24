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
client_dict = {'name': ""} # this the list of connected clients
message_queue.put(message_list) # now we have an empty dictionary in the queue

def receive_message(message_queue):
    data, address = sock.recvfrom(1024)  # listen on socket for messages
    print("Attempting to decode the death star plans...")
    message = pickle.loads(data)  # load received data into message
    print("MESSAGE RAW: ", str(message))  # show the contents of the message for now
    # if the message is of type 'send', output flag, call store_message
    if (message['type'] == 'send'):
        print("Message recieved, storing...")
        '''ps = Process(target = store_message, args=(message['destination'], message, message_queue,))
        ps.start()
        ps.join()
        ps.terminate()'''
        store_message(message['destination'], message, message_queue)
    if (message['type'] == 'get'):
        print("Deliver messages...")
        '''pdm = Process(target =deliver_messages, args=(message['source'], message, address, message_queue,))
        pdm.start()
        pdm.join()
        pdm.terminate()'''
        deliver_messages(message['source'], message, address, message_queue)
    if (message['type'] == 'ack'):
        '''pha = Process(target=handle_acknowledgement,args=(message['payload'], message['source'], message_queue,))
        pha.start()
        pha.join()
        pha.terminate()'''
        handle_acknowledgement(message['payload'], message['source'], message_queue)
    if (message ['type'] == 'handshake'):
        global client_list
        print ("Trying to handshake...\n")
        handshake(sock, message['source'], message['name'], client_list)

    # iterate over the list of stored messages for a particular client.
    # Send each message individually.
def deliver_messages(dest, msg, address, message_queue):
    message_dict = message_queue.get()
    if dest not in message_dict:
        print("Not in the dictionary yet...")
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

def handshake(sock, source, name, client_dict):
    print ("Sending client list to new client \n")
    sock.sendto(pickle.dumps(client_dict), (source, address[1])) #send this to the person handshaking
    client_dict[name] = source #add a new entry in the dictionary for the connected client
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
    if __name__ == '__main__':
        if __name__ == '__main__':
            if __name__ == '__main__':
                while True:
                    '''p = Process(target=receive_message, args=(message_queue,)) # start process to do listening
                    p.start() #start the listening
                    p.join() # lock access to the queue
                    p.terminate()'''
                    receive_message(message_queue)
                    #should do some sort of time_elapsed - run_time > something check so that we do this every once in a while.
                    #Flood clients with handshakes in order to ensure that they are still connected
                    #Probably flood other servers here too.

'''def listen_mode():
    print ("listen for data....")
    data, address = sock.recvfrom(1024)
    #data2, addr = sock2.recvfrom(1024)
    print ("thread start...")
    t = threading.Thread(target = receive_message, args=[data, address])
    #t2 = threading.Thread(target = '''
''', args = [data2, addr])

    t.start()
    #t2.start()
    '''

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
