import socket as sk
import random
import time

#UDP connection
s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
s.settimeout(5)

ip = "192.168.1.15" #IP address of this drone
gateway_port = 25000 #Port used by the gateway

gateway_address = ('localhost',gateway_port)

message = ip + ":register"
sent = s.sendto(message.encode(), gateway_address)

try:
    response, gateway = s.recvfrom(4096) 
    # Verifying that the gateway received the message
    # and waiting for a response
    if response.decode('utf-8') == "OK":
        print("Ready to serve...")
        s.settimeout(None)
        while True:
            # Getting the delivery address from the gateway 
            data, gateway = s.recvfrom(4096)
            payload = data.decode('utf-8').split(":")
            command = payload[0]
            if command == "deliver":
                address = payload[1]
                message = ip + ":OK"
                s.sendto(message.encode(),gateway_address)
                print("Delivering to: %s" % address)
                # The drone takes some time to deliver the package
                time.sleep(random.randint(1, 5)) 
                message = ip + ":delivered" 
                # Informing the gateway that the delivery was successful
                # and the drone is ready for the next delivery
                s.sendto(message.encode() ,gateway_address)
                print("Delivery successful")
            else:
                print("Unknown command: %s" % command)
    else:
        # The received message didn't match expected message
        print("Connection failed, shutting down")
except sk.timeout:
    # Response took too long to arrive or hasn't been sent at all
    print("No response from gateway, shutting down")
finally:
    # Closing the socket 
    s.close()
        
    