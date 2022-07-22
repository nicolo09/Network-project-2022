import socket
import os
from threading import Thread

e="EXIT"
my_host='10.10.10.1'
my_port=17000
gateway_address = '127.0.0.1'
gateway_port = 26000
BUFFER=256
d="DRONES"


def client_waits(s):
    try:
        with s as s:
            while True:
                message=s.recv(BUFFER);
                message=message.decode()
                if len(message)>0:
                    print('Received message:')
                    print(message)
                else:
                    print('Gateway has disconnected, ending client')
                    s.close()
                    os._exit(0)
                    
    except socket.error:
        os._exit(0)
    

def client_input(s):
    try:
        while True:
            try:
                address=input("Insert an address to use in the delivery (insert "+d+" to request a list of available drones)\n")
                if len(address)>0:
                    if address.lower()==e.lower():
                        print("Closing Client...")
                        s.close()
                        os._exit(0)
                    else:
                        if address.lower()==d.lower():
                            print("Asking the gateway about available drones...")
                            message = my_host+":"+"drones:"
                            s.sendall(message.encode());
                        else:
                            iden=input("You can choose the drone to carry out your delivery. Insert IPv4 or (insert -1 to go back to address input)\n")
                            if len(iden)>0:
                                if iden.lower()==e.lower():
                                    print("Closing Client...")
                                    s.close()
                                    os._exit(0)
                                else:
                                    if iden!=str(-1):
                                        print("Contacting the gateway about your delivery...")
                                        message = my_host+":"+"deliver:"+iden+":"+address
                                        s.sendall(message.encode())
                else:
                    print("Address is wrong, try again")
            except (KeyboardInterrupt, EOFError):
                print("Recived command to end...")
                s.close()
                os._exit(0)
    except socket.error:
        print("Closing Client...")
        s.close()
        os._exit(0)
                            
            

if __name__=='__main__':
    
    try:
        s=socket.socket(socket.AF_INET ,socket.SOCK_STREAM)
        s.connect((gateway_address, gateway_port))
        message = my_host+":"+'cregister'+":"
        s.sendall(message.encode())

        print("Connected to gateway: "+str(gateway_address)+":"+str(gateway_port)+"\n")
        print("Write "+e+" to close Client")
        
    except socket.error:
        print("Couldn't connect, retry later")
        os._exit(0)
    
    
    ci=Thread(target=client_waits,args=(s,))
    co=Thread(target=client_input,args=(s,))
    ci.start()
    co.start()
    ci.join()
    co.join()
    
    
            