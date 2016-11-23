import pickle
import socket
import sys
import multiprocessing as mp
from multiprocessing import Process
import sys
import os

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
        print("No Messages right now. Check back later.")
    #we need to be able to get the message dump, right now we are only
    #getting one messgage at a time
    #may use a loop to iterate through the messages --> need to implements ACKS
    #or use the seq number to stop iterating through the for loop

def send_mode(sock):
    #Open the same stdin as main.
    #sys.stdin = os.fdopen(fileno)
    while True:
        #something is wrong with one of the previous print statements.
        thing = input("Message: ")
        if(thing == ''):
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
            sock.sendto(pickle.dumps(message),(SERVER_IP,SERVER_PORT))
            seq_num += 1


def ack_handle(listy,sock):
    global SERVER_ACK_PORT
    global SERVER_IP
    ack = {'seq': '', 'type': 'ack', 'source': socket.gethostbyname(socket.gethostname()), 'destination': '','payload': listy}
    sock.sendto(pickle.dumps(ack),(SERVER_IP,SERVER_PORT))

def main():
    #fn = sys.stdin.fileno()
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except socket.error:
        print ("Failed to create sockets.")
        sys.exit()

    #Setting up the LISTENING udp portion
    sock.bind((socket.gethostbyname(socket.gethostname()),UDP_PORT))

    user_listen(sock)
    while True:
        send_mode(sock)
    #while True:
    '''print ("starting process 1")
    p1 = Process(target = user_listen, args=(sock,fn,))
    p1.start()
    print("Process 1 has started.")

    print ("starting process 2")
    p2 = Process(target = send_mode, args=(sock,fn,))
    p2.start()
    print ("process 2 has started")'''



#run main program
if(__name__ == "__main__"):
    mp.set_start_method('spawn')
    main()