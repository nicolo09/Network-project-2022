import socket
import sys
from threading import Thread, Lock
import threading
import time

e="EXIT"
d="DRONES"
p='PING'
my_host='10.10.10.1'
my_port=17000
gateway_address = '127.0.0.1'
gateway_port = 26000
BUFFER=1024
MILLISECONDS=1000
ping_ans='pong'
time_waiting=0

terminate_event = threading.Event()

def client_waits(s,lock):
    try:
        with s as s:
            while True:
                message=s.recv(BUFFER)
                message=message.decode()
                a=time.time()
                if len(message)>0:
                    if message.lower()==ping_ans.lower(): 
                        lock.acquire()
                        #reading the time 
                        global time_waiting
                        te=(a-time_waiting)*MILLISECONDS
                        lock.release()
                        print('Time elapsed to send and recive message: '+str(te)+' milliseconds')
                    else:
                        print('Received message:')
                        print(message)
                else:
                    print('Gateway has disconnected, ending client')
                    terminate_event.set()
                    return
    except socket.error:
        terminate_event.set()
        return
    

def client_input(s,lock):
    try:
        while True:
            try:
                address=input("Insert an address to use in the delivery (insert "+d+" to request a list of available drones, or "+p+" to ping the gateway)\n")
                if len(address)>0:
                    if address.lower()==e.lower():
                        print("Closing Client...")
                        terminate_event.set()
                        return
                    else:
                        if address.lower()==d.lower():
                            print("Asking the gateway about available drones...")
                            message = my_host+":"+"drones:"
                            s.sendall(message.encode())
                        else:
                            if address.lower()==p.lower():
                                #Ask for the ping
                                print('Asking the ping...')
                                message=my_host+":"+"ping:"
                                global time_waiting
                                lock.acquire()
                                time_waiting=time.time()
                                lock.release()
                                s.sendall(message.encode())
                            else:
                                iden=input("You can choose the drone to carry out your delivery. Insert IPv4 or (insert -1 to go back to address input)\n")
                                if len(iden)>0:
                                    if iden.lower()==e.lower():
                                        print("Closing Client...")
                                        terminate_event.set()
                                        return
                                    else:
                                        if iden!=str(-1):
                                            print("Contacting the gateway about your delivery...")
                                            message = my_host+":"+"deliver:"+iden+":"+address
                                            s.sendall(message.encode())
                else:
                    print("Address is wrong, try again")
            except (KeyboardInterrupt, EOFError, SystemExit):
                print("Received command to end...")
                terminate_event.set()
                return
    except socket.error:
        print("Closing Client...")
        terminate_event.set()
        return

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
        sys.exit(0)

    lock=Lock()
    co=Thread(target=client_waits,args=(s,lock))
    ci=Thread(target=client_input,args=(s,lock))

    try:
        ci.setDaemon(True)
        ci.start()
        co.start()
        terminate_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        s.close()
        co.join()
