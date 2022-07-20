import socket as sk
import random
import time

#UDP connection
s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
s.settimeout(5)

bufsize = 4096 # buffer size
ip = "192.168.1.10" # IP address of this drone
gateway_port = 25000 # Port used by the gateway
flag = False # flag used for message controls

gateway_address = ('localhost',gateway_port)

message = ip + ":register"
for tries in range(1,5):
    try:
        # Verifying that the gateway received the message
        # and waiting for a response
        s.sendto(message.encode(), gateway_address)
        response, gateway = s.recvfrom(bufsize)
        break
    except sk.timeout:
        print("Couldn't register to gateway. Attempt: %d" % tries)
        if tries == 5:
            flag = True
# Checking response            
if (not flag) and response.decode('utf-8') == "OK":
    print("Ready to serve...")
    while True:
        # There is no time limit for requests to arrive
        s.settimeout(None)
        data, gateway = s.recvfrom(bufsize)
        payload = data.decode('utf-8').split(":")
        command = payload[0]
        # Checking requested command
        if command == "deliver":
                # Getting the delivery address
                address = payload[1]
                # Informing the gateway that the delivery has started
                message = ip + ":OK"
                s.sendto(message.encode(),gateway_address)
                print("Delivering to: %s" % address)
                # The drone takes some time to deliver the package
                time.sleep(random.randint(1, 5)) 
                message = ip + ":delivered"
                s.settimeout(5)
                print("Delivery successful")
                for tries in range(1,5):
                    try:
                        # Informing the gateway that the delivery was successful
                        # and the drone is ready for the next delivery
                        s.sendto(message.encode() ,gateway_address)
                        # Waiting response from gateway
                        response, gateway = s.recvfrom(bufsize)
                        break
                    except sk.timeout:
                        print("Waiting for response failed. Attempt: %d" % tries)
                        # The drone stops trying to receive a response after 5 tries
                        if tries == 5:
                            flag = True
                            
                if flag or response.decode('utf-8') != "OK":
                    # Response message didn't arrive or didn't match the expected one
                    print("Couldn't receive response from gateway, shutting down")
                    break
        else:
            # The requested command is undefined,
            # so it will be ignored
            print("Unknown command: %s" % command)
else:
    # Couldn't connect or received message didn't match the expected one
    print("Connection failed, shutting down")

# Closing the socket    
s.close()
        