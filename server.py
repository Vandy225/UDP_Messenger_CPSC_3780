import socket
import pickle
import time
import sys

CLIENT_PORT = 5006
SERVER_PORT = 5005
SERVER_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
message_inbox = {} # this will be the replacement for the queue
client_directory = {} #this will be a dict of user_names : ip addresses that this server hosts
neighbor1 = '' #*
# neighbor2 = ''

# the format for pairs in the table is:
# routing_table = {user_name: [server_host_ip, hops, user_name's ip address]}
routing_table = {} #dictionary that tells a client which server to send messages to

lifetime_max = 1 #for now...

#this is the new receive_message
def receive_packet (sock):
    global client_directory
    global routing_table
    global message_inbox
    print "Server is listening"
    data, address = sock.recvfrom(10240)
    print "Received packet, deciding what to do with it"
    message = pickle.loads(data)
    print "Raw message: ", str(message)
    if type(message) is dict:
        #packet types fall into these categories:
        #send: client wants to send messages to another client
        #get: client wants to view their messages
        #server_get: propagates a get message to other servers 
        #server_deliver: delivers a list of messages in the payload
        #ack: signals that the payload contains the dictionary of messages to delete
        #handshake: user enters the network, tries to register user_name, gets initial
        #messages if registration successful
        #routing_update: happens when new user enters, informs servers where they connected
        #exit: user signals intent to log off
        print "Message was a dict"

        if (message['type'] == 'send'):
            #handle send function
            print "received send type"
            send_handle(message, client_directory, routing_table, message_inbox) #working on
        if (message['type'] == 'handshake'):
            handshake_response(message, client_directory, routing_table, message_inbox)
        '''if (message['type'] == 'get'):
        if (message['type'] == 'server_get'):
        if (message['type'] == 'server_deliver'):    
        if (message['type'] == 'ack'):
        if (message['type'] == 'routing_update'):
        if (message['type'] == 'exit'):  '''  

def handshake_response (message, client_directory, routing_table, message_inbox):
    #first we will check if the user name is being hosted by another server
    if message['user_name'] not in routing_table:
        #username was not taken, tell user it was good
        print "username was good"
        user_ack = {'type': 'user_good'}
        #send message to user
        sock.sendto(pickle.dumps(user_ack), (message['source'], CLIENT_PORT))
        if message['user_name'] not in client_directory:
            #this will pair up the client's username with their IP, add to directory
            print "client added to client directory"
            client_directory[message['user_name']] = message['source']
        if message['user_name'] not in message_inbox:
            #if the client had no message_inbox, make them an empty box (list)
            print "new mailbox made for client", message['user_name']
            message_inbox[message['user_name']] = []
        routing_message = {'type': 'routing_update', 'server_source': socket.gethostbyname(socket.gethostname()), 'payload': routing_table, 'life_time': 0}
        print "letting other servers know about new user via routing update"
        #sock.sendto(pickle.dumps(routing_message), (neighbor1, SERVER_PORT))
        #sock.sendto(pickle.dumps(routing_message), (neighbor2, SERVER_PORT))
        print "sending out server get to find messages for client: ", message['user_name']
        
    

#this function is responsible for dealing with a send type message
def send_handle(message, client_directory, routing_table, message_inbox):
    #check to see if the client's user_name is in the directory already
    if message['destination'] in client_directory:
        #if so, then just store their messages
        store_message(message, message_inbox)
    #if the client is not in the client directory:
    else:
        #check the routing table for the message's destination
        server_host = get_user_host(message['destination'], routing_table)
        #this means that a server host was found for a client
        if server_host != '0':
            sock.sendto(pickle.dumps(message), (server_host, SERVER_PORT))
        #this means that we did not find a servr host for a client
        else:
            #so just store the message for later
            store_message(message, message_inbox)


#function used to store message for a user in the inbox
def store_message(message, message_inbox):
    #if the user has a mailbox in the inbox
    if message['destination'] in message_inbox:
        print "storing a message for : ", message['destination']
        #then we append the current message to the list of messages for the user
        message_inbox[message['destination']].append(message)
    else:
        #we are going to make a mailbox for the user
        new_list = []
        #add the incoming message to the list for the user
        new_list.append(message)
        #put the user's list of messages in the dictionary under their name
        message_inbox[message['destination']] = new_list

#this function is designed to return the ip of a server hosting a user_name            
def get_user_host(user_name, routing_table):
    if user_name in routing_table:
        #this will return the ip of server that is hosting the user we are asking about
        #(relative to the server calling this function)
        return routing_table[user_name][0]
    else:
        #this is a sentinel value indicating that the user could not be found
        return '0'

if __name__ == '__main__':

    #try and create socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #bind the socket for listening for the server
        sock.bind(('', SERVER_PORT))
        print "Server started on port: ", str(SERVER_PORT)
    except socket.error:
        #if socket creation failed, notify and break
        print "Failed to create socket"
        sys.exit()

    while True:
        #start listening
        receive_packet(sock)


                        
                         

                         
                        

