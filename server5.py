import socket
import pickle
import time
import sys

CLIENT_PORT = 5006
SERVER_PORT = 5005
SERVER_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
message_inbox = {} # this will be the replacement for the queue
client_directory = {} #this will be a dict of user_names : ip addresses that this server hosts
neighbor1 = '142.66.140.39'
neighbor2 = '142.66.140.36'

# the format for pairs in the table is:
# routing_table = {user_name: [server_host_ip, hops, user_name's ip address]}
routing_table = {} #dictionary that tells a client which server to send messages to

lifetime_max = 1 #for now...

#lifetime_max = ceiling( number of servers/2)

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
        elif (message['type'] == 'handshake'):
            print "received Handshake"
            handshake_response(message, client_directory, routing_table, message_inbox)
        elif (message['type'] == 'get'):
            print "received get"
            send_server_get(sock, message['user_name'], message['source'])
            deliver_messages(message['user_name'], message_inbox)
        elif (message['type'] == 'server_get'):
            if(message['life_time'] < lifetime_max):
                print "received good server_get"
                handle_server_get(sock, message, message_inbox)
        elif (message['type'] == 'routing_update'):
            if(message['life_time'] < lifetime_max):
                print "received good routing update"
                update_routing_table(message, routing_table)
        elif (message['type'] == 'ack'):
            if(message['life_time'] < lifetime_max):
                print "Received ack..."
                handle_ack(message, message_inbox)
        elif (message['type'] == 'server_deliver'):
            if(message['destination'] in client_directory):
                   for msg in message['payload']:
                       message_inbox[msg['destination']].append(msg)
            else:
                if message['user_name'] in routing_table:
                    sock.sendto(pickle.dumps(message), (get_user_host(message['user_name'], routing_table), SERVER_PORT))
                   #deliver_messages(message['destination'], message_inbox)
            #Need to add in the ability to forward these deliverys to their destination. 
        elif (message['type'] == 'exit'):
            if(message['life_time'] < lifetime_max):
                user_disconnect(sock, message, client_directory, routing_table)
        else:
            print "Something went wrong... message's type was not found... Source:", message['server_source']

def user_disconnect(sock, message, client_directory, routing_table):
    global SERVER_PORT
    global neighbor1
    global neighbor2
    user = message['user_name']
    #need to delete user from the routing table.
    print "deleteing user from routing table..."
    if(user in routing_table):
           del routing_table[user]
    #remove from the client_directory
    if(user in client_directory):
        del client_directory[user]
    print "Forwarding exit to neighbors..."
    message['life_time']+=1
    sock.sendto(pickle.dumps(message), (neighbor1,SERVER_PORT))
    sock.sendto(pickle.dumps(message), (neighbor2,SERVER_PORT))
    
     
     

#Remove messages from the inbox. Based on the inverse inbox sent by the acker.
def handle_ack(message, message_inbox):
    print "Acknowledging..."
    acker = message['user_name']
    inv_inbox = message['payload']
    if acker in message_inbox:
        for msg in message_inbox[acker][:]:
            if msg['user_name'] in inv_inbox and msg['seq'] in inv_inbox[msg['user_name']]:
                print "Removed message: ", str(msg['seq'])
                message_inbox[acker].remove(msg)
        '''temp_list = message_inbox[acker]
        del message_inbox[acker]
        temp_list[:] = [msg for msg in temp_list if not(msg['user_name'] in inv_inbox and msg['seq'] in inv_inbox[msg['user_name']])]
        message_inbox[acker] = temp_list'''
    #avoid infinite sending....
    message['life_time']+=1
    sock.sendto(pickle.dumps(message), (neighbor1, SERVER_PORT))
    sock.sendto(pickle.dumps(message), (neighbor2, SERVER_PORT))
    

def update_routing_table(message, routing_table):
    your_table = message['payload'] 
    for user in your_table:
        if user not in routing_table:
            print "learned about a new client: ", user
            #the entry in my routing table for the new user will be equal to the
            #a list composed of:
            #[0]: the assumed server host
            #[1]: the number of hops to reach the new user from me through assumed host
            #[2]: the user's ip address
            routing_table[user] = [message['server_source'], your_table[user][1]+1, your_table[user][2]]
        else:
            #we already have an entry for a user, need to see if a better route exists
            if your_table[user][1]+1 < routing_table[user][1]:
                print "got better info about ", user, "from ", message['server_source']
                routing_table[user] = [message['server_source'], your_table[user][1]+1, your_table[user][2]]
    routing_update = {'type': 'routing_update', 'server_source': socket.gethostbyname(socket.gethostname()), 'payload': routing_table, 'life_time': message['life_time']+1}
    sock.sendto(pickle.dumps(routing_update), (neighbor1, SERVER_PORT))
    sock.sendto(pickle.dumps(routing_update), (neighbor2, SERVER_PORT))

#handle server get is going to need some serious rewriting as well  as the ack handler. 
def handle_server_get(sock, message, message_inbox):
    global routing_table
    global neighor1
    global neighbor2
    if message['user_name'] in message_inbox:
        server_deliver_message = {'type': 'server_deliver','destination': message['user_name'], 'payload': message_inbox[message['user_name']]}
        print "this server is delivering messages to server ", message['server_source']
        sock.sendto(pickle.dumps(server_deliver_message), (get_user_host(message['user_name'],routing_table), SERVER_PORT))
    message['life_time'] += 1
    if message['server_source'] == str(neighbor1):
        message['server_source'] = socket.gethostbyname(socket.gethostname())
        print "forwarding server_get to neighbor 2"
        sock.sendto(pickle.dumps(message), (neighbor2, SERVER_PORT))
    elif(message['server_source'] == str(neighbor2)):
        print "forwarding  server_get to neighbor 1"
        message['server_source'] = socket.gethostbyname(socket.gethostname())
        sock.sendto(pickle.dumps(message), (neighbor1, SERVER_PORT))
    else:
        print "SOMETHING WENT WRONG WITH HANDLE SERVER GET."
    
#this function is used to propagate a user's get request to servers
def send_server_get(sock, user_name, user_ip):
    global neighbor1
    global neighbor2
    global SERVER_PORT
    server_get_send = {'type': 'server_get', 'server_source': socket.gethostbyname(socket.gethostname()), 'source': user_ip, 'user_name': user_name, 'life_time': 0}
    sock.sendto(pickle.dumps(server_get_send), (neighbor1, SERVER_PORT))
    sock.sendto(pickle.dumps(server_get_send), (neighbor2, SERVER_PORT))
    

def deliver_messages(user_name, message_inbox):
    global client_directory
    if user_name in client_directory and user_name in message_inbox:
        print "user_name: ", user_name, " was in client_directory and message_inbox, delivering", str(message_inbox[user_name])
        delivery = {'payload': message_inbox[user_name]}
        sock.sendto(pickle.dumps(delivery), (client_directory[user_name], CLIENT_PORT))
    else:
        # still want to send the client an empty list, will work out
        print "deliver messages went wrong...."

def handshake_response (message, client_directory, routing_table, message_inbox):
    #first we will check if the user name is being hosted by another server
    if message['user_name'] not in routing_table:
        routing_table[message['user_name']] = [socket.gethostbyname(socket.gethostname()), 0, message['source']]
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
        sock.sendto(pickle.dumps(routing_message), (neighbor1, SERVER_PORT))
        sock.sendto(pickle.dumps(routing_message), (neighbor2, SERVER_PORT))
        '''print "sending out server get to find messages for client: ", message['user_name']
        server_get_send = {'type': 'server_get', 'server_source': socket.gethostbyname(socket.gethostname()), 'source': message['source'], 'user_name': message['user_name'], 'life_time': 0}
        sock.sendto(pickle.dumps(server_get_send), (neighbor1, SERVER_PORT))
        # sock.sendto(pickle.dumps(server_get_send), (neighbor2, SERVER_PORT))'''
        
        
    

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
