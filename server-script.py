import socket
import pickle
import time
import sys

CLIENT_PORT = 5006
SERVER_PORT = 5005
SERVER_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
message_inbox = {} # this will be the replacement for the queue
client_directory = {} #this will be a dict of user_names : ip addresses that this server hosts
neighbor1 = ''
neighbor2 = ''

# the format for pairs in the table is:
# routing_table = {user_name: [server_host_ip, hops, user_name's ip address]}
routing_table = {} #dictionary that tells a client which server to send messages to

lifetime_max = 2 #for now...

#lifetime_max = ceiling( number of servers/2)

####################################################################################
#Function: receive packet
#Description: This function is constantly receiving packets, behaviour is decided based on each packets type, and in the case of propgated packets we check their lifetime before doing anything
#Implementation: use the socket to listen for incommining packets. Use the if-else block to choose a behaviour. 
####################################################################################
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
                if message['destination'] in routing_table:
                    sock.sendto(pickle.dumps(message), (get_user_host(message['destination'], routing_table), SERVER_PORT))
                   #deliver_messages(message['destination'], message_inbox)
            #Need to add in the ability to forward these deliverys to their destination. 
        elif (message['type'] == 'exit'):
            if(message['life_time'] < lifetime_max):
                user_disconnect(sock, message, client_directory, routing_table)
        else:
            print "Something went wrong... message's type was not found... Source:", message['server_source']
####################################################################################
#Function: user_disconnect
#Description: Handles the case when a user graefully disconnects from the network. 
#The message is passed on to both neighbors so that we ensure that all servers will delete the user 
#from routing tables and client direcotries. Don't delete users mailbox in case they log back on.
#Implementation: check if this server has the user in their routing table and client directory.
#If the user is in either, then delete them. If they log back on handshake_response() will handle it.
####################################################################################
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

####################################################################################
#Function: handle_ack
#Description: Remove messages from the inbox. Based on the inverse inbox sent by the acker.
#Implementation: The acker is the person sending the acknowledgment, the payload that being sent,
#is an "inverse_inbox" this inbox is organized like: { message's source (user name): [sequence numbers being acknowledged by the person sending this inbox.]}
#So we check the inbox of the acker for these messages and delete them.
#The acknowlegment is then sent to each neighbor so that if they happen to have a copy of the
#messages being acknowledged then they too can be deleted.
####################################################################################
def handle_ack(message, message_inbox):
    print "Acknowledging..."
    acker = message['user_name']
    inv_inbox = message['payload']
    if acker in message_inbox:
        for msg in message_inbox[acker][:]:
            if msg['user_name'] in inv_inbox and msg['seq'] in inv_inbox[msg['user_name']]:
                print "Removed message: ", str(msg['seq'])
                message_inbox[acker].remove(msg)
    #avoid infinite sending....
    message['life_time']+=1
    sock.sendto(pickle.dumps(message), (neighbor1, SERVER_PORT))
    sock.sendto(pickle.dumps(message), (neighbor2, SERVER_PORT))
####################################################################################
#Function: update_routing_table
#Description: When a routing update is received, this will update our routing table. It also forwards our new table to both neighbors.
#Implementation: W check out table against the table received, if a new client is found, we add it to our table. If a better path to a known client is found we add it to our table. 
#if we update our table or not then we send each of our neighbors our new (or unchanged) table.
####################################################################################
def update_routing_table(message, routing_table):
    your_table = message['payload']
    #need to check every user in the received table.
    for user in your_table:
        print "examining ", user , " in routing table from: ", message['server_source']
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
    print "sending table to neighbors"
    sock.sendto(pickle.dumps(routing_update), (neighbor1, SERVER_PORT))
    sock.sendto(pickle.dumps(routing_update), (neighbor2, SERVER_PORT))
####################################################################################
#Function:handle_server_get
#Description: when a server_get is received then we will check to see if we have messages for the client who triggered the server get, if we dont, then we simply forward on the serverget.
#If we do have messages then we need to deliver the messages (via info from the routing table)
#and the forward the message on.
#Implementation is just ;ike description says, except each time we forward the server_get on to neighbors. We change the server_source to be ourself (this server).
####################################################################################
def handle_server_get(sock, message, message_inbox):
    global routing_table
    global neighbor1
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
####################################################################################
#Function: send_server_get
#Description: This function is used to propagate a user's get request to neighbor servers.
#Implementation: Using the socket we construct and send a server_get message to each of our neighbors.
####################################################################################
def send_server_get(sock, user_name, user_ip):
    global neighbor1
    global neighbor2
    global SERVER_PORT
    server_get_send = {'type': 'server_get', 'server_source': socket.gethostbyname(socket.gethostname()), 'source': user_ip, 'user_name': user_name, 'life_time': 0}
    sock.sendto(pickle.dumps(server_get_send), (neighbor1, SERVER_PORT))
    sock.sendto(pickle.dumps(server_get_send), (neighbor2, SERVER_PORT))
    
####################################################################################
#Function: Deliver messages
#Description:When a client sends a get request, we either deliver them their whole inbox, or we send them an empty list to indicate that they currently have no messages.
#Implementation: As description says...
#################################################################################### 
def deliver_messages(user_name, message_inbox):
    global client_directory
    if user_name in client_directory and user_name in message_inbox:
        print "user_name: ", user_name, " was in client_directory and message_inbox, delivering", str(message_inbox[user_name])
        delivery = {'payload': message_inbox[user_name]}
        sock.sendto(pickle.dumps(delivery), (client_directory[user_name], CLIENT_PORT))
    else:
        # still want to send the client an empty list, will work out
        print "deliver messages went wrong...."
####################################################################################
#Function: handshake_response
#Description: This function handles "handshake" packets which are received when users login for the first time or subsequent log ins.
#Implementation: The user will send us a username that they wish to use, the server checks this username against its routing table. 
#If its available we signal the client, if its not we tell the client to resend a new username.
#We then add the client into our client directory and routing table ionce they have a good username. 
#This triggers a round of routing updates so that all other servers will know about our new client.
####################################################################################
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
        
        
    
####################################################################################
#Function: send_handle
#Description: this function is responsible for dealing with a send type message, either calling store or forwarding the message to where it needs to go.
#Implementation: Straightforward...
####################################################################################
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

####################################################################################
#Function: store_message
#Implementation: This will check if we have a mailbox for user, and stores the message.
#Description: function used to store message for a user in the inbox
####################################################################################
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
####################################################################################
#Function: get_user_host
#Description: a helper function that returns the server_host of a particular client according to theis servers routing table. 
#Implementation: Returns the string ip address of a server_host for a particular client.
#ASSUMPTION: every server assumes that the server_host in our routing table owns the client.
####################################################################################
def get_user_host(user_name, routing_table):
    if user_name in routing_table:
        #this will return the ip of server that is hosting the user we are asking about
        #(relative to the server calling this function)
        return routing_table[user_name][0]
    else:
        #this is a sentinel value indicating that the user could not be found
        return '0'

if __name__ == '__main__':
    #Dont need to actually flag these because we are in the main function, but this is what is happening. 
    #global neighbor1
    #global neighbor2
    SERVER_ID = raw_input("Initialize server #(1-5): ")
    INT_SERVER_ID = int(SERVER_ID)
    while INT_SERVER_ID < 1 or INT_SERVER_ID > 5:
        SERVER_ID = raw_input("Invalid Server ID, retry: ")
        INT_SERVER_ID = int(SERVER_ID)
    
    #assign neighbors based on the server selected.
    #Left neighbor is neighbor 1
    #right neighbor is neighbor 2
    if INT_SERVER_ID == 1:
        neighbor1 = '142.66.140.40'
        neighbor2 = '142.66.140.37'
    elif INT_SERVER_ID == 2:
        neighbor1 = '142.66.140.36'
        neighbor2 = '142.66.140.38'
    elif INT_SERVER_ID == 3:
        neighbor1 = '142.66.140.37'
        neighbor2 = '142.66.140.39'
    elif INT_SERVER_ID == 4:
        neighbor1 = '142.66.140.38'
        neighbor2 = '142.66.140.40'
    elif INT_SERVER_ID == 5:
        neighbor1 = '142.66.140.39'
        neighbor2 = '142.66.140.36'
    else:
        print "Something went wrong when initializing neighbors. Crashing..."
        sys.exit()
    #try and create socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #bind the socket for listening for the server
        sock.bind(('', SERVER_PORT))
        print "Server started on port: ", str(SERVER_PORT)
    except socket.error:
        #if socket creation failed, notify and break
        print "Failed to create socket, there may already be a server running on this machine."
        sys.exit()

    while True:
        #start listening
        receive_packet(sock)
