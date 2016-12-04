###################################################################
#File: client.py
#Authors: Lance C & Josh V
#Description: this python script will interact wil the server-script.py scripts in order to send messages between users running the client.py script.
#This program provides an iterface for users to send messages to each other. 
#Last modified: Dec 4th, 2016
###################################################################
import socket
import pickle
import sys
import os
import time


SERVER_IP = ''
UDP_PORT = 5006
SERVER_PORT = 5005
seq_num = 0
user_name = ''
routing_table = {} #this is for the purpose of translating user_names into ip's
####################################################################
#Function: handshake
#Description: Handshake initiates the conversation with the server. It registers the clients username and is also the 'flag' for the server to update its routing table. 
#Implementation: First we make sure that the user types in a unique username/ID. 
#Then we send that username to the server. We wait for a small amount of time for the servers response. 
#Depending on that response we either have the user retype their name (a new handshake function is called) or we inform them that their username was good.
#Then the client needs to check if the user has any messages on the network that were generated before they last (if ever) sent a get request.
###################################################################
def handshake():
    global user_name
    global seq_num
    
    user_name = raw_input("User Name: ")

    while(len(user_name) < 10):
        print "User name <= 10 characters, re-enter"
        user_name = raw_input("User Name: ")

    message = {'seq' : seq_num, 'type': 'handshake', 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name}
    print "Handshaking with server..."
    sock = create_socket()
    sock.sendto(pickle.dumps(message), (SERVER_IP, SERVER_PORT))
    #increment sequence number, may use later
    seq_num += 1
    print "waiting on server response...\n"
    time.sleep(0.5)
    #now we need to check if our entry for username was good
    user_good = False
    #keep making the suer enter a user name until good
    while user_good == False:
        data, address = sock.recvfrom(10240)
        user_ack = pickle.loads(data)
        if user_ack['type'] == 'user_good':
            print "Username registration successful!\n"
            user_good = True
        elif (user_ack['type'] == 'user_error'):
            print "Username is taken, try again...\n"
            sock.close()
            handshake()
    sock.close()
    user_listen()#user needs to listen for initial messages
    
###################################################################
#Function: send_mode
#Description: send mode is how the user interfaes with the client program. They can send messages, get messages, or disconnect from the service. 
#Implementation: Depending on what the user enters into the "address to" and "Message" feilds this function will either:
#1: send the message to the intended recipient (through the server)
#2: send a get request to the connected server host.
#3: send a disconnect notification to the hosting server.
###################################################################
def send_mode():
    global SERVER_IP
    global SERVER_PORT
    global seq_num
    global user_name
    while True:
        # get user input for recipient and payload
        recipient = raw_input("Address to: ")
        message = raw_input("Message: ")
        #if the user enters nothing, we assume a get
        sock = create_socket()
        if recipient == '' and message == '':
            #listen for messages
            sock.close()
            user_listen()
        elif recipient == 'disconnect' and message == 'disconnect':
            exit_message = {'type': 'exit', 'seq': seq_num, 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name, 'life_time': -1}
            print "Sending notification of disconnect...\n"
            sock.sendto(pickle.dumps(exit_message), (SERVER_IP, SERVER_PORT))
            sock.close()
            print "Exiting application..."
            sys.exit()
        else:
            #user wants to send a message
            new_message = {'seq': seq_num, 'type': 'send', 'payload': message, 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name, 'destination': recipient}
            print "Sending message to server..."
            sock.sendto(pickle.dumps(new_message), (SERVER_IP, SERVER_PORT))
            #incrementing sequence number
            seq_num += 1
            sock.close()
###################################################################
#Function: user_listen
#Description: User listen sends get requests to the server in order to receive any messages intended for the user.
#The messages are then displayed to the user as well as the username of the user who sent the message. 
#Implementation: We send five get requests to the server, and yes this does infact trigger a round of five server_gets being sent by ther server. 
#However, the reason that we send 5 is so that we ensure that we are getting any and all messages intended for us that are surrently sitting on other servers in the network.
#In order to make sure that the user doesnt receive true duplicates (meaning that I can still send someone 'hello' six times and they will receive it), 
#is to check each dictionary in the message list that we receive. If it has already been placed in the buffer then we simply ignore the message since it is a duplicate.
#We also construct the inverse inbox that is used as part of the acknowledgement process. (The inverse inbox is explained in the description of the handle_ack() server code.) 
###################################################################
def user_listen():
    global SERVER_IP
    global SERVER_PORT
    global user_name
    sock = create_socket()
    #contruct get type message
    message = {'type': 'get', 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name}
    #send to server
    #sock.sendto(pickle.dumps(message), (SERVER_IP, SERVER_PORT))
    print "Sending get requests, waiting for server response..."
    #time.sleep(1)
    #Wait for a received message until we have something in the payloads list.
    #Hats off to adam on this one!
    the_buffer = []
    tick = 0
    while(tick < 5):
        sock.sendto(pickle.dumps(message), (SERVER_IP, SERVER_PORT))
        data, address = sock.recvfrom(10240)
        received_packet = pickle.loads(data)
        if received_packet['payload']:
            for msg in received_packet['payload']:
                #This allows the client to ignore true dulicate messages.
                if msg not in the_buffer:
                    the_buffer.append(msg)
            tick += 1
        else:
            tick += 1
    #Used for debugging purposes to see the whole received packet.
    #print "Received packet:",str(received_packet)
    if type(received_packet) is dict:
        #message_list = received_packet['payload'] #list of messages
        if the_buffer:
            inv_inbox = {} #this is for storing seq_nums to send acks back
            for msg in the_buffer:
                print "Message: ", msg['payload'], "From: ", msg['user_name']
                if msg['user_name'] in inv_inbox:
                    inv_inbox[msg['user_name']].append(msg['seq'])
                else:
                    inv_inbox[msg['user_name']] = [msg['seq']]
            ack_handle(inv_inbox, sock)
        else:
            print "No messages right now..."
    #this condition is to say that an empty list was sent to the user, therefore no messages
    else:
        print "Got something strange... disregarding..."
    sock.close()
###################################################################
#Function: ack_handle()
#Description: Helper function that is used by user_listen(). 
#This function takes in a constructed inverse inbox and the socket that is currently being used and sends the inv_ibox to the hosting server.
#Implementation: Uses the socket and pickle libraries to send the inv_inbox to hosting server.
###################################################################
def ack_handle(inv_inbox, sock):
    global SERVER_PORT
    global SERVER_IP
    global user_name
    ack = {'type':'ack', 'source':socket.gethostbyname(socket.gethostname()), 'user_name': user_name, 'payload':inv_inbox, 'life_time':-1}
    sock.sendto(pickle.dumps(ack), (SERVER_IP,SERVER_PORT))
###################################################################
#Function: create_socket()
#Description: The purpose of this function is to create a socket object for one time use.
#Implementation: In our crusade to try and get as many edge cases as possible. We realized that if two users wanted to use the same IP address then they would have to share the socket.
#What we then did was create this function in order to "take" the socket when it was free to be used. 
#The way weve written our code should avoid deadlock as our convention is "use it, drop it". So everytime it is used it is then dropped before someone else will need it. 
#Had we used multiprocesseing for our client code this may have been absolutly nessecary. (it still is, but there would have been more required)
###################################################################
def create_socket():
    global SERVER_IP
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #bind the socket for listening for the server
            #May not actually need to bind... it seems to be working for Josh M and Dawson to not do so.
            sock.bind(('', UDP_PORT))
            break
        except socket.error:
            #if socket creation failed, notify and break
            print "Waiting for socket to become avaliable... Please wait..."
            print "If you are seeing this  in an infinite loop something has gone wrong with the socket..."
    return sock
            

#main function
if __name__ == '__main__':
    #global SERVER_IP
    #get the server ID from the
    SERVER_ID = raw_input("Enter Server # you want to connect to: ")
    #cast to an int
    INT_SERVER_ID = int(SERVER_ID)
    #trap to keep users from entering an invalid SERVER_ID
    while INT_SERVER_ID < 1 or INT_SERVER_ID > 5:
        SERVER_ID = raw_input("Invalid Server ID, retry: ")
        INT_SERVER_ID = int(SERVER_ID)
    #based on server ID, set the SERVER_IP to the appropriate value
    if INT_SERVER_ID == 1:
        SERVER_IP = "142.66.140.36"
    elif INT_SERVER_ID == 2:
        SERVER_IP = "142.66.140.37"
    elif INT_SERVER_ID == 3:
        SERVER_IP = "142.66.140.38"
    elif INT_SERVER_ID == 4:
        SERVER_IP = "142.66.140.39"
    else:
        SERVER_IP = "142.66.140.40"

    #try and handshake with the server
    handshake()
    #sit in listen mode forever after that
    while True:
        send_mode()

        
    
           
