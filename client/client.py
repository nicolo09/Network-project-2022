import socket
import sys
from threading import Thread

e="EXIT"
my_host='10.10.10.1'
my_port=17000
gateway_address = '127.0.0.1'
gateway_port = 18000
BUFFER=256
d="DRONES"


def client_waits(s):
    try:
        with s as s:
            while True:
                message=s.recv(BUFFER);
                print('C:Recived message:')
                print(message.decode())
    except socket.error:
        sys.exit()
    

def client_input(s):
    while True:
        address=input("C:Insert an address to use in the delivery (insert "+d+" to request a list of available drones)\n")
        if len(address)>0:
            if address.lower()==e.lower():
                print("C:Closing Client...")
                s.close()
                sys.exit()
            else:
                if address.lower()==d.lower():
                    print("C:Asking the gateway about available drones...")
                    message = my_host+":"+"drones:"
                    s.sendall(message.encode());
                else:
            
                    iden=input("C:You can choose the drone to carry out your delivery. Insert IPv4 or Drone Identifier (insert -1 to go back to address input)\n")
                    if len(iden)>0:
                        if iden.lower()==e.lower():
                            print("C:Closing Client...")
                            s.close()
                            sys.exit()  
                        else:
                            if iden!=str(-1):
                                print("C:Contacting the gateway about your delivery...")
                                message = my_host+":"+"deliver:"+iden+":"+address
                                s.sendall(message.encode());
                            
                        
        else:
            print("C:Address is wrong, try again")
            

if __name__=='__main__':
    
    try:
        s=socket.socket(socket.AF_INET ,socket.SOCK_STREAM)
        s.connect((gateway_address, gateway_port))
        message = my_host+":"+'cregister'+":"
        s.sendall(message.encode())

        print("C:Connected to gateway: "+str(gateway_address)+":"+str(gateway_port)+"\n")
        print("C:Write "+e+" to close Client")
        
    except socket.error:
        print("C:Couldn't connect, retry later")
        sys.exit()
    
    
    ci=Thread(target=client_waits,args=(s,))
    co=Thread(target=client_input,args=(s,))
    ci.start()
    co.start()
    print('\nC:Waiting for threads to end...')
    ci.join()
    co.join()
    print('\nC:Threads have ended, main ends')
    
    
            