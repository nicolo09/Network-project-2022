import socket as sk
import random
import time

#UDP connection
s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
s.settimeout(5)

ip = "192.168.1.5" #IP address of this drone
gateway_port = 25000 #Port used by the gateway

gateway_address = ('localhost',gateway_port) 
init_message = "Ready to serve..."
completion_message = "Delivery successful"

message = ip + ":register:" + init_message
sent = s.sendto(message.encode(), gateway_address)

try:
    response, gateway = s.recvfrom(4096) 
    # Verifying that the gateway received the message
    # and waiting for a response
    if response == "OK":
        s.settimeout(0)
        while True:
            # Getting the delivery address from the gateway 
            data, gateway = s.recvfrom(4096)
            print("Delivering to: %s" % data.decode('utf8'))
            # The drone takes some time to deliver the package
            time.sleep(random.randint(1, 5)) 
            message = ip + ":delivered:" + completion_message
            # Informing the gateway that the delivery was successful
            # and the drone is ready for the next delivery
            s.sendto(message.encode() ,gateway_address)
    else:
        # The received message didn't match expected message
        print("Connection failed, shutting down")
except sk.timeout:
    # Response took too long to arrive or hasn't been sent at all
    print("No response from gateway, shutting down")
finally:
    # Closing the socket 
    s.close()
    