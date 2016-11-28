import socket
import pickle
import sys
import os
import time


SERVER_IP = '142.66.140.34'
UDP_PORT = 5006
SERVER_PORT = 5005
seq_num = 0
user_name = ''
routing_table = {} #this is for the purpose of translating user_names into ip's

def handshake(sock):
    global user_name
    global seq_num
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
            



#main function
if __name__ == '__main__':
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

        
    
           
