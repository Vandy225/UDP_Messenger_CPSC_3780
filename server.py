import socket
import pickle
# from multiprocessing import Queue, Process
try:
    import Queue
except ImportError:
    import queue as Queue
import time
import sys

UDP_PORT = 5005
UDP_ACK_PORT = 5006
SERVER_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
SERVER_ID = 'Server Host'
message_queue = Queue.Queue() # declare the message queue
message_list = { 'client_ip' : [] } #THIS IS ACTUALLY A MESSAGE DICTIONARY
client_list = [] # this the list of connected clients
message_queue.put(message_list) # now we have an empty dictionary in the queue
neighbor1 = "10.76.134.106"
neighbor2 = "10.76.134.106"
lifetime_max = 1

#this data structure is the routing table with keys client_ip and a list with entries:
#list[0] is the ip of the server
#list[1] is the number of hops to reach the client.
routing_table = {}
#===================================================================================================
#ROUTING TABLE UPDATE IMPLEMENTATION NOTES
#We will need to pass these routing tables back and forth between servers at some interval.
#We should update these tables when a new handshake occurs.
#We will have to send THIS servers routing table to each one of our neighbours.
#USing the principal of optimality.
#The neighbour (we) will check to see if we have each of the neighbours clients in our own routing table.
#If we have that client, then whatever do nothing.
#If we dont have that client, then we need to add that client into out own routing table. When this is done _ things must happen:
#1: When adding client into table, change the list[0] value to be the server that gave us the table we are looking at.
#2: add 1 to the list[1] value so that we know the number of hops to the server. This is not being used right now, but may as well keep track of it.
#===================================================================================================
def update_routing_table(my_table, message):
    #iterate over the clients in the received routing table
    your_table = message['payload']
    for client_ip in your_table:
        #if our table does not have an entry for a client, add it
        if client_ip not in my_table:
            my_table[client_ip] = [message['server_source'],your_table[client_ip][1]+1] #add to my table
        else:
            index = your_table[client_ip][1]
            print ("" + str(index))
            if your_table[client_ip][1] + 1 < my_table[client_ip][1]:
                my_table[client_ip] = [message['server_source'], your_table[client_ip][1] + 1]

    message = {'type': 'routing_update', 'server_source': socket.gethostbyname(socket.gethostname()),
               'payload': routing_table, 'life_time': message['life_time'] + 1}
    print ("Sending table to neighbors")
    sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
    sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))

#Given a dest (client) return the server IP that that client is connected to as far as THIS server knows.
def check_table(dest):
    global routing_table
    if(dest in routing_table):
        return routing_table[dest][0]
    else:
        return "0"

def send_get_request(source):
    global neighbor1
    global neighbor2
    global UDP_PORT
    mess = {'type' : "server_get" , 'server_source' : socket.gethostbyname(socket.gethostname()), 'source' : source, 'life_time' : 0}
    sock.sendto(pickle.dumps(mess),(neighbor1,UDP_PORT))
    sock.sendto(pickle.dumps(mess),(neighbor2, UDP_PORT))

#Server_get type meswsage received by server.
#If we have messages for the gets source, send them back.
#Also send the request on, incase other servers have messages.
def handle_server_get(message, message_queue):
    temp_dict = message_queue.get()
    if message['source'] in temp_dict:
        mess = {'type': "server_deliver", 'destination' : message['source'], 'payload' : temp_dict[message['source']]}
        print ("SERVER GET ROUTING TABLE CHECK = " + str(check_table(message['source'])))
        sock.sendto(pickle.dumps(mess),(check_table(message['source']),UDP_PORT))
    message['life_time'] += 1
    if(message['server_source'] == neighbor1):
        message['server_source'] = socket.gethostbyname(socket.gethostname())
        sock.sendto(pickle.dumps(message),(neighbor2,UDP_PORT))
    else:
        message['server_source'] = socket.gethostbyname(socket.gethostname())
        sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
    message_queue.put(temp_dict)

def receive_message(message_queue):
    global client_list
    global routing_table
    data, address = sock.recvfrom(1024)  # listen on socket for messages
    print("Attempting to decode the death star plans...")
    message = pickle.loads(data)  # load received data into message
    print("MESSAGE RAW: ", str(message))  # show the contents of the message for now
    # if the message is of type 'send', output flag, call store_message
    #SEND SEND SEND SEND SEND SEND SEND SEND SEND SEND SEND SEND SEND SEND SEND SEND
    if (message['type'] == 'send'):
        print("Message recieved, deciding what to do...")
        if(message['destination'] in client_list):
            store_message(message['destination'], message, message_queue)
        elif(message['destination'] not in client_list):
            #check the routing table for a route.
            destination = check_table(message['destination'])
            if(destination != "0"):
                #destination is correct, send message along.
                sock.sendto(pickle.dumps(message),(destination,UDP_PORT))
            else:
                #Destination was not in routing table. Stor it
                store_message(message['destination'],message,message_queue)
    #GET GET GET GET GET GET GET GET GET GET GET GET GET GET GET GET GET GET GET GET
    if (message['type'] == 'get'):
        print("Deliver messages...")
        if (message['source'] in client_list):
            deliver_messages(message['source'], address, message_queue)
            send_get_request(message['source'])
            #deliver_messages(message['source'], message, address, message_queue)
    #SERVER_GET SERVER_GET SERVER_GET SERVER_GET SERVER_GET SERVER_GET SERVER_GET SERVER_GET SERVER_GET
    if(message['type'] == 'server_get'):
        if(message['life_time'] < lifetime_max):
            handle_server_get(message, message_queue)
        #If the life time is three or greater, we just drop it.
    #SERVER_DELIVERY SERVER_DELIVERY SERVER_DELIVERY SERVER_DELIVERY SERVER_DELIVERY SERVER_DELIVERY
    if(message['type'] == "server_deliver"):
        if(message['destination'] in client_list):
            temp_dict = message_queue.get()
            temp_dict[message['destination']].append(message['payload'])
            message_queue.put(temp_dict)
    if (message['type'] == 'ack'):
        handle_acknowledgement(message['payload'], message['source'], message_queue)
    if (message ['type'] == 'handshake'):
        print ("Trying to handshake...\n")
        handshake(sock, message['source'])
    if (message['type'] == 'routing_update'):
        print("Received table from " + message['server_source'])
        if (message['life_time'] < lifetime_max):
            update_routing_table(routing_table, message)
        '''message = {'type': 'routing_update', 'server_source': socket.gethostbyname(socket.gethostname()), 'payload': routing_table, 'life_time': }
        sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
        sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))'''
    if(message['type'] == 'exit' and message['life_time'] < lifetime_max + 1):
        print ("client " + message['source'] + " is disconnecting")
        #call function to delete user from routing table and client_list
        user_disconnect(message, routing_table, client_list, message_queue)


def user_disconnect(message, routing_table, client_list, message_queue):
    global UDP_PORT
    global neighbor1
    global neighbor2
    if (message['source'] in routing_table):
        del routing_table[message['source']] #delete the client from the routing tbale
    #this may need work
    for idx in client_list[:]:
        if (message['source'] == idx):
            print("deleting client " + message['source'] + " from client_list...")
            client_list.remove(idx)
    #delete messages destined for exiting client.
    '''
    temp_dict = message_queue.get()
    if(message['source'] in temp_dict):
        print("deleting messages for client: " + message['source'] + " from message inbox...")
        del temp_dict[message['source']]
    message_queue.put(temp_dict)
    '''
    #now we must tell other servers to do the same.
    print("Forwarding exit to neighbours...")
    message['life_time'] += 1
    sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
    sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))

    # iterate over the list of stored messages for a particular client.
    # Send each message individually.
def deliver_messages(dest, address, message_queue):
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
        print("Dest already in list, adding msg to it")
        message_dict[dest].append(msg)  # put the entry in the dictionary of lists of dictionaries
        message_queue.put(message_dict)  # put the dictionary in the queue

    else:
        print("Dest not in list, creating new list")
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
    global client_list
    global message_list
    global routing_table
    print ("Recieved handshake.\n")
    #sock.sendto(pickle.dumps(client_dict), (source, address[1])) #send this to the person handshaking
    client_list.append(source) #add a new entry in the dictionary for the connected client
    if (source not in message_list):
        message_list[source] = [] #Create a mailbox for the client on this server.
    routing_table[source] = [source, 0] #add the client to routing table.
    message = {'type': 'routing_update', 'server_source': socket.gethostbyname(socket.gethostname()), 'payload': routing_table, 'life_time': 0}
    print("Sending table to neighbors")
    sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
    sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))
    # this connection shit is fine
    initial_server_get_message = {'type': 'server_get', 'source': source,'server_source': socket.gethostbyname(socket.gethostname()), 'life_time': 0}
    sock.sendto(pickle.dumps(initial_server_get_message), (neighbor1, UDP_PORT))
    sock.sendto(pickle.dumps(initial_server_get_message), (neighbor2, UDP_PORT))
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
