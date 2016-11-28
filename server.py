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
neighbor1 = "10.76.69.237"
#neighbor2 = "10.76.134.106"
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
def update_routing_table(message):
    global routing_table
    #iterate over the clients in the received routing table
    your_table = message['payload']
    for user in your_table:
        #if our table does not have an entry for a client, add it
        if user not in routing_table:
            print("Learned about a new client " + user + " owned by " + your_table[user][0])
            #USER CHANGE #2
            routing_table[user] = [message['server_source'],your_table[user][1]+1,your_table[user][2]] #add to my table
        else:
            index = your_table[user][1]
            print ("" + str(index))
            if your_table[user][1] + 1 < routing_table[user][1]:
                print("Got better info about a client from a neighbor....")
                routing_table[user] = [message['server_source'], your_table[user][1] + 1,your_table[user][2]]

    message = {'type': 'routing_update', 'server_source': socket.gethostbyname(socket.gethostname()),
               'payload': routing_table, 'life_time': message['life_time'] + 1}
    print ("Sending table to neighbors")
    sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
    #sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))

#Given a dest (client) return the server IP that that client is connected to as far as THIS server knows.
def check_table(user_name):
    global routing_table
    if(user_name in routing_table):
        return routing_table[user_name][0]
    else:
        return "0"

def send_get_request(source):
    global neighbor1
    global neighbor2
    global UDP_PORT
    mess = {'type' : "server_get" , 'server_source' : socket.gethostbyname(socket.gethostname()), 'source' : source, 'life_time' : 0}
    sock.sendto(pickle.dumps(mess),(neighbor1,UDP_PORT))
    #sock.sendto(pickle.dumps(mess),(neighbor2, UDP_PORT))

#Server_get type meswsage received by server.
#If we have messages for the gets source, send them back.
#Also send the request on, incase other servers have messages.
def handle_server_get(message, message_queue):
    temp_dict = message_queue.get()
    if message['source'] in temp_dict:
        mess = {'type': "server_deliver", 'destination' : message['source'], 'payload' : temp_dict[message['source']]}
        print ("SERVER GET ROUTING TABLE CHECK = " + str(check_table(message['source'])))
        print ("Deliver messages to server: " + str(message['server_source']))
        sock.sendto(pickle.dumps(mess),(check_table(message['source']),UDP_PORT))
    message['life_time'] += 1
    if(message['server_source'] == neighbor1):
        message['server_source'] = socket.gethostbyname(socket.gethostname())
        #sock.sendto(pickle.dumps(message),(neighbor2,UDP_PORT))
    else:
        message['server_source'] = socket.gethostbyname(socket.gethostname())
        sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
    message_queue.put(temp_dict)

def receive_message(message_queue):
    global client_list
    global routing_table
    data, address = sock.recvfrom(10240)  # listen on socket for messages
    print("Attempting to decode the death star plans...")
    message = pickle.loads(data)  # load received data into message
    print("MESSAGE RAW: ", str(message))  # show the contents of the message for now
    #We have to check if a server has accidently received a list of messages.
    if type(message) is dict:
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
                send_get_request(message['source'])
                deliver_messages(message['source'], address, message_queue)

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
                for mes in message['payload']:
                    temp_dict[message['destination']].append(mes)
                message_queue.put(temp_dict)
                #issues here
                deliver_messages(message['destination'], address, message_queue)
        if (message['type'] == 'ack'):
            if(message['life_time'] < lifetime_max):
                handle_acknowledgement(message,message_queue)
        if (message ['type'] == 'handshake'):
            print ("Trying to handshake...\n")
            handshake(sock, message['source'])
        if (message['type'] == 'routing_update'):
            print("Received table from " + message['server_source'])
            if (message['life_time'] < lifetime_max):
                update_routing_table(message)
        if(message['type'] == 'exit' and message['life_time'] < lifetime_max + 1):
            print ("client " + message['source'] + " is disconnecting")
            #call function to delete user from routing table and client_list
            user_disconnect(message, routing_table, client_list, message_queue)
    else:
        #We've received a list of messages because there is a client with the same IP as this server.
        #So we ignore the message and receive the next packet.
        print ("Received lis by accident, ignoring....")


def user_disconnect(message, routing_table, client_list, message_queue):
    global UDP_PORT
    global neighbor1
    global neighbor2
    if (message['user_name'] in routing_table):
        del routing_table[message['user_name']] #delete the client from the routing tbale
    #this may need work
    for idx in client_list[:]:
        if (message['source'] == idx):
            print("deleting client " + message['source'] + " from client_list...")
            client_list.remove(idx)
    #delete messages destined for exiting client.
    #now we must tell other servers to do the same.
    print("Forwarding exit to neighbours...")
    message['life_time'] += 1
    sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
    #sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))

    # iterate over the list of stored messages for a particular client.
    # Send each message individually.
def deliver_messages(dest, address, message_queue):
    global routing_table
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

def handle_acknowledgement(message,message_queue):
    print("Acknowledging Messagees...")
    inbox = message_queue.get()
    acker = message['source']
    inv_inbox = message['payload']
    for msg in inbox[acker][:]:
        if msg['source'] in inv_inbox and msg['seq'] in inv_inbox[msg['source']]:
            print ("Removed message: " + str(msg['seq']))
            inbox[acker].remove(msg)
    message_queue.put(inbox)
    #As long as we increment the life time, the packet will die. Also if we receive this ack set again, the above control block SHOULD stop it from accessing memory it shouldn't.
    message['life_time'] +=1
    sock.sendto(pickle.dumps(message),(neighbor1,UDP_PORT))
    #sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))

def handshake(sock, source, user_name):
    global client_list
    global message_list
    global routing_table
    print ("Recieved handshake.\n")

    #USER CHANGE #1 Trying to add user names.
    if user_name not in routing_table:
        user_ack = {'type' : 'user_good'}
        sock.sendto(pickle.dumps(user_ack),(source,UDP_PORT))
        routing_table[user_name] = [socket.gethostbyname(socket.gethostname()), 0, source] #add the client to routing table.
        # sock.sendto(pickle.dumps(client_dict), (source, address[1])) #send this to the person handshaking
        if (source not in client_list):
            client_list.append(source)  # add a new entry in the dictionary for the connected client
        if (source not in message_list):
            message_list[source] = []  # Create a mailbox for the client on this server.
        message = {'type': 'routing_update', 'server_source': socket.gethostbyname(socket.gethostname()),
                   'payload': routing_table, 'life_time': 0}
        print("Sending table to neighbors")
        sock.sendto(pickle.dumps(message), (neighbor1, UDP_PORT))
        # sock.sendto(pickle.dumps(message), (neighbor2, UDP_PORT))
        # this connection shit is fine
        initial_server_get_message = {'type': 'server_get', 'source': source,
                                      'server_source': socket.gethostbyname(socket.gethostname()), 'life_time': 0}
        sock.sendto(pickle.dumps(initial_server_get_message), (neighbor1, UDP_PORT))
        # sock.sendto(pickle.dumps(initial_server_get_message), (neighbor2, UDP_PORT))
    else:#username is not valid
        #Send them a name_error
        print ("Username already in use...")
        user_ack = {'type': 'user_error'}
        sock.sendto(pickle.dumps(user_ack), (source, UDP_PORT))

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



'''We are thinking of reqorking the entire cobase from the ground up.
All packets being sent should be dictionaries. Every packet will have:
1. Type - Indicates how receivers handle this packet
2. life_time - How many hops the packet can make.
3. Source - IP of  client sending
4. Destination - IP of receiving client.
5. Seq number (for packets sent from clients.

Servers will hold a list of local clients in the fourm of a dictionary with pairs: user_name:'Users IP".
Servers will hold a routing table of the form {User_name: [server host, hops, ip of user]}
Servers will hand this to servers on a server update which occurs on handshakes.
Servers will aslo hand their clients updated their routing tables with the list of messages that clients will be getting.
SO that we can both update the clients user list (Basically a routing table) and read out their messages.
 Users are identified by their user_name which should be unique in the network.'''