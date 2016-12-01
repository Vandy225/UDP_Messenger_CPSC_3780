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

def handshake(sock):
    global user_name
    global seq_num
    user_name = raw_input("User Name: ")

    while(len(user_name) < 10):
        print "User name <= 10 characters, re-enter"
        user_name = raw_input("User Name: ")

    message = {'seq' : seq_num, 'type': 'handshake', 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name}
    print "Handshaking with server..."
    sock.sendto(pickle.dumps(message), (SERVER_IP, SERVER_PORT))
    #increment sequence number, may use later
    seq_num += 1
    print "waiting on server response..."
    time.sleep(0.5)
    #now we need to check if our entry for username was good
    user_good = False
    #keep making the suer enter a user name until good
    while user_good == False:
        data, address = sock.recvfrom(10240)
        user_ack = pickle.loads(data)
        if user_ack['type'] == 'user_good':
            print "name registration successful"
            user_good = True
        elif (user_ack['type'] == 'user_error'):
            print "username is taken, try again"
            handshake(sock)
    user_listen(sock)#user needs to listen for initial messages
            
def send_mode(sock):
    global SERVER_IP
    global SERVER_PORT
    global seq_num
    global user_name
    
    while True:
        # get user input for recipient and payload
        recipient = raw_input("Address to: ")
        '''while(len(recipient) < 10):
            print "User name < 10 characters (invalid), re-enter"
            recipient = raw_input("Address to: ")'''
        message = raw_input("Message: ")
        #if the user enters nothing, we assume a get
        if recipient == '' and message == '':
            #listen for messages
            user_listen(sock)
        elif recipient == 'disconnect' and message == 'disconnect':
            exit_message = {'type': 'exit', 'seq': seq_num, 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name, 'life_time': -1}
            print "sending notification of disconnect"
            sock.sendto(pickle.dumps(exit_message), (SERVER_IP, SERVER_PORT))
            sock.shutdown(socket.SHUT_RDWR)
            sys.exit()
        else:
            #user wants to send a message
            new_message = {'seq': seq_num, 'type': 'send', 'payload': message, 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name, 'destination': recipient}
            print "constructed message to send, sending"
            sock.sendto(pickle.dumps(new_message), (SERVER_IP, SERVER_PORT))
            #incrementing sequence number
            seq_num += 1

def user_listen(sock):
    global SERVER_IP
    global SERVER_PORT
    global user_name
    #contruct get type message
    message = {'type': 'get', 'source': socket.gethostbyname(socket.gethostname()), 'user_name': user_name}
    #send to server
    #sock.sendto(pickle.dumps(message), (SERVER_IP, SERVER_PORT))
    print "sent get, waiting for server response..."
    #time.sleep(1)
    #Wait for a received message until we have something in the payloads list.
    #Hats off to adam on this one!
    tick = 0
    while(tick < 5):
        sock.sendto(pickle.dumps(message), (SERVER_IP, SERVER_PORT))
        data, address = sock.recvfrom(10240)
        received_packet = pickle.loads(data)
        if received_packet['payload']:
            break
        else:
            tick += 1
    print "Received packet:",str(received_packet)
    if type(received_packet) is dict:
        message_list = received_packet['payload'] #list of messages
        if message_list:
            inv_inbox = {} #this is for storing seq_nums to send acks back
            for msg in message_list:
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

def ack_handle(inv_inbox, sock):
    global SERVER_PORT
    global SERVER_IP
    global user_name
    ack = {'type':'ack', 'source':socket.gethostbyname(socket.gethostname()), 'user_name': user_name, 'payload':inv_inbox, 'life_time':-1}
    sock.sendto(pickle.dumps(ack), (SERVER_IP,SERVER_PORT))
            


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

    #try and create sockets
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #bind the socket for listening for the server
        sock.bind(('', UDP_PORT))
    except socket.error:
        #if socket creation failed, notify and break
        print "Failed to create socket"
        sys.exit()
    #try and handshake with the server
    handshake(sock)
    #sit in listen mode forever after that
    while True:
        send_mode(sock)

        
    
           
