import pickle
import socket
import sys
import multiprocessing as mp
from multiprocessing import Process
import sys
import os
#as of right now (November 24, 2016 @ 19:52) Client shouldn't have to ever have any major changes.
'''Servers IP address'''
SERVER_IP = "10.76.134.106"
UDP_PORT = 5007
UDP_ACK_PORT = 5009
SERVER_PORT = 5005
SERVER_ACK_PORT = 5006
seq_num = 0
message = { 'seq' : seq_num, 'type' : '' , 'source' : socket.gethostbyname(socket.gethostname()), 'destination' : '10.76.69.237', 'payload' : ''}

def user_listen(sock):
    global SERVER_IP
    global SERVER_PORT
    msg = { 'seq' : '', 'type' : 'get' , 'source' : socket.gethostbyname(socket.gethostname()), 'payload' : ''}
    print ("Trying to send get...")
    sock.sendto(pickle.dumps(msg),(SERVER_IP,SERVER_PORT))
    print ("Waiting for server response...")
    data, address = sock.recvfrom(1024)
    message_list = pickle.loads(data) #now the client is getting the entire message list, need to iterate through
    ack_list = []
    if message_list:
        for index in message_list:
            print ("Received Message: " + str(index['payload']))#this may change... JOSH
            ack_list.append(index['seq'])
        ack_handle(ack_list,sock)
    else:
        print("No Messages right now. Check back later.\n")

def send_mode(sock):
    #Open the same stdin as main.
    #sys.stdin = os.fdopen(fileno)
    while True:
        #something is wrong with one of the previous print statements.
        client_destination = input("Address to: ")
        thing = input("Message: ")
        if(thing == '' and client_destination == ''):
            user_listen(sock)
        else:
            global SERVER_IP 
            global SERVER_PORT
            global seq_num
            message['seq'] = seq_num
            print ("sending message with seq_num =" + str(message['seq']))
            message['payload'] = thing
            message['type'] = 'send'
            message['seq'] = seq_num
            message['destination'] = client_destination
            sock.sendto(pickle.dumps(message),(SERVER_IP,SERVER_PORT))
            seq_num += 1


def ack_handle(listy,sock):
    global SERVER_ACK_PORT
    global SERVER_IP
    ack = {'seq': '', 'type': 'ack', 'source': socket.gethostbyname(socket.gethostname()), 'destination': '','payload': listy}
    sock.sendto(pickle.dumps(ack),(SERVER_IP,SERVER_PORT))

def handshake(sock):
    msg = {'type': "handshake", 'source': socket.gethostbyname(socket.gethostname())}
    print ("Handshaking with server...\n")
    sock.sendto(pickle.dumps(msg), (SERVER_IP, SERVER_PORT))
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
    user_listen(sock)
    while True:
        send_mode(sock)

#run main program
if(__name__ == "__main__"):
    # mp.set_start_method('spawn')
    main()