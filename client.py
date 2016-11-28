import pickle
import socket
import sys
import os
import time
#as of right now (November 24, 2016 @ 19:52) Client shouldn't have to ever have any major changes.
'''Servers IP address'''
SERVER_IP = "10.76.69.237"
UDP_PORT = 5007
UDP_ACK_PORT = 5009
SERVER_PORT = 5005
SERVER_ACK_PORT = 5006
seq_num = 0
# message = { 'seq' : seq_num, 'type' : '' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : '10.76.69.237', 'payload' : ''}

def user_listen(sock):
    global SERVER_IP
    global SERVER_PORT
    msg = { 'seq' : '', 'type' : 'get' , 'source' : socket.gethostbyname(socket.gethostname()), 'payload' : ''}
    print ("Trying to send get...")
    sock.sendto(pickle.dumps(msg),(SERVER_IP,SERVER_PORT))
    print ("Waiting for server response...")
    data, address = sock.recvfrom(10240)
    message_list = pickle.loads(data) #now the client is getting the entire message list, need to iterate through
    if message_list:
        inv_inbox = {}
        for mess in message_list:
            print ("Message: " + mess['payload'] + " From: " + mess['source']) #this may change... JOSH
            if mess['source'] in inv_inbox:
                inv_inbox[mess['source']].append(mess['seq'])
            else:
                inv_inbox[mess['source']] = [mess['seq']]
        ack_handle(inv_inbox,sock)
    else:
        print("No Messages right now. Check back later.\n")

def send_mode(sock):
    global SERVER_IP
    global SERVER_PORT
    global seq_num
    #Open the same stdin as main.
    #sys.stdin = os.fdopen(fileno)
    while True:
        #something is wrong with one of the previous print statements.
        client_destination = input("Address to: ")
        thing = input("Message: ")
        if(thing == '' and client_destination == ''):
            user_listen(sock)
        elif(client_destination == "disconnect"):
            message = {'type': 'exit', 'source': socket.gethostbyname(socket.gethostname()), 'life_time': 0}
            sock.sendto(pickle.dumps(message), (SERVER_IP, SERVER_PORT))
            sock.shutdown(socket.SHUT_RDWR)
            sys.exit()
        else:
            message = {}
            message['seq'] = seq_num
            print ("sending message with seq_num =" + str(message['seq']))
            message['payload'] = thing
            message['type'] = 'send'
            message['destination'] = client_destination
            message['source'] = socket.gethostbyname(socket.gethostname())
            sock.sendto(pickle.dumps(message),(SERVER_IP,SERVER_PORT))
            seq_num += 1


def ack_handle(inv_inbox,sock):
    global SERVER_ACK_PORT
    global SERVER_IP
    ack = {'seq': '', 'type': 'ack', 'source': socket.gethostbyname(socket.gethostname()), 'payload': inv_inbox, 'life_time': 0}
    sock.sendto(pickle.dumps(ack),(SERVER_IP,SERVER_PORT))

def handshake(sock):
    msg = {'type': "handshake", 'source': socket.gethostbyname(socket.gethostname())}
    print ("Handshaking with server...\n")
    sock.sendto(pickle.dumps(msg), (SERVER_IP, SERVER_PORT))
    print ("waiting 0.5 seconds")
    time.sleep(0.5)
    user_listen(sock) #listen back from server

def main():
    #fn = sys.stdin.fileno()
    #global user_name
    #user_name = input("What is your name?: ")

    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except socket.error:
        print ("Failed to create sockets.")
        sys.exit()

    #Setting up the LISTENING udp portion
    sock.bind((socket.gethostbyname(socket.gethostname()),UDP_PORT))
    handshake (sock) #handshake with server to be admitted
    # user_listen(sock)
    while True:
        send_mode(sock)

#run main program
if(__name__ == "__main__"):
    # mp.set_start_method('spawn')
    main()