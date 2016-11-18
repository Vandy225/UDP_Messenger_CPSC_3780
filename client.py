import socket

UDP_IP = "142.66.140.36"
UDP_PORT = 5005
seq_num = 0
Message = { 'seq' : seq_num, 'type' : 'send' , 'source' : '142.66.140.37', 'destination' : '142.66.140.36', 'payload' : ''}

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

while True:
    Message['payload'] = raw_input("Message: ")
    sock.sendto(pickle.dumps(Message).encode('utf-8'),(UDP_IP,UDP_PORT))
    seq_num = seq_num + 1
    
