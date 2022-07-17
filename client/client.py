import socket
import pickle
import sys
import time
from threading import Thread

e="EXIT"
my_host='10.10.10.0'
my_port='24'
gateway_address = '127.0.0.1'
gateway_port = 18000
BUFFER=256;

    

def client_waits(s):
    try:
        with s as s:
            while True:
                message=s.recv(BUFFER)
                time.sleep(1);
                msg=pickle.loads(message)
                #Unpickled
                print('C:Recived message : '+str(msg))
    except socket.error:
        #print('C:Socket has been closed, closing client... ')
        #due volte closing è inutile(tanto viene iniziato dal input)
        sys.exit();
        #EOFError: Ran out of input...
    

def client_input(s):
    while True:
        address=input("C:Insert an address to use in the delivery ")
        if len(address)>0:
            if address.lower()==e.lower():
                print("C:Closing Client...")
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                sys.exit()
            else:
                iden=input("C:You can choose the drone to carry out your delivery. Insert IPv4 or Drone Identifier (insert -1 to go back to address input)")
                if len(iden)>0:
                    if iden.lower()==e.lower():
                        print("C:Closing Client...")
                        s.shutdown()
                        s.close()
                        sys.exit();
                    else:
                        if iden!=str(-1):
                            print("C:Contacting the gateway about your delivery...")
                            message = (address,iden,my_host,my_port)
                            msg=pickle.dumps(message);
                            s.sendall(msg)
                        
        else:
            print("C:Address is wrong, try again ")
            

if __name__=='__main__':
    
    try:
        s=socket.socket(socket.AF_INET ,socket.SOCK_STREAM)
        s.connect((gateway_address, gateway_port))
        message = ('Client_Connect',my_host,my_port)
        msg=pickle.dumps(message);
        s.sendall(msg)

        print("C:Connected to gateway: "+str(gateway_address)+":"+str(gateway_port))
        print("C:Write "+e+" to close Client")
        
    except socket.error:
        print("C:Couldn't connect, retry later")
        sys.exit()
    
    
    ci=Thread(target=client_waits,args=(s,))
    co=Thread(target=client_input,args=(s,))
    ci.start()
    co.start()
    #print("C:Spawned threads, now sleep")
    #time.sleep(1)
    
    #print("C:Ended sleep, now main ends")
    print('C: Waiting for threads to end...')
    ci.join()
    co.join()
    print('C: Threads have ended, main ends')
    
    
            