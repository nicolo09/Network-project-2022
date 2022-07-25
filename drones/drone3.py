import socket as sk
import random
import signal
import time
import sys

#UDP connection
s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
ip = "192.168.1.15" # IP address of this drone
gateway_port = 25000 # Port used by the gateway
gateway_address = ('localhost', gateway_port)

flag = False # flag used for message controls
delivering = False # defines if this drone is currently delivering or if it's doing nothing
registered = False # defines if this drone has been registered by the gateway 
BUFSIZE = 1024 # buffer size
MAX_ATTEMPTS = 5 # max number of attempts to receive response from the gateway
TIMEOUT_TIME = 4 # number of seconds before throwing a timeout exception

# Returns the gateway's response to the latest message sent already decoded 
def talk_to_gateway(message, starting_time, relative_time):
    if s is not None:
        s.sendto(message.encode(), gateway_address)
        response, gateway = s.recvfrom(BUFSIZE)
        # Showing time needed to accomplish drone-gateway comunication
        print("Packet sending time: %.4f ms" % ((time.time() - relative_time)*500))
        print("Total elapsed time: %.4f ms" % ((time.time() - starting_time)*1000))
        return response.decode('utf-8')
    return ""

# Using this function to receive commands
# so that recv function doesn't block interrupt signal
def get_command_from_gateway():
    data = ""
    while data == "":
        try:
            data, gateway = s.recvfrom(BUFSIZE)
        except sk.timeout:
            pass
    return data.decode('utf-8').split(":")

# When receiving an interrupt signal the drone shuts down
def exit_on_interrupt(_signo, _stack_frame):
    print("Received interrupt signal, shutting down")
    if not delivering and registered:
        # Telling the gateway that the drone is shutting down
        print("Unregistering from gateway")
        message = ip + ":unregister"
        start = time.time()
        for tries in range(1, MAX_ATTEMPTS + 1):
            try:
                response = talk_to_gateway(message, start, time.time())
                break
            except sk.timeout:
                print("Waiting for response failed. Attempt: %d" % tries)
                if tries == MAX_ATTEMPTS:
                    response = ""
        if response != "OK":
            print("Couldn't inform gateway, shutting down anyway")
    # Letting the user read the previous messages before closing
    time.sleep(3)
    s.close()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_on_interrupt)
signal.signal(signal.SIGTERM, exit_on_interrupt)

s.settimeout(TIMEOUT_TIME) 

message = ip + ":register"
tries = 1
start = time.time()
while tries <= MAX_ATTEMPTS:
    try:
        # Verifying that the gateway received the message
        # and waiting for a response
        response = talk_to_gateway(message, start, time.time())
        break
    # The response took too much time to arrive
    except sk.timeout:
        print("Couldn't register to gateway. Attempt: %d" % tries)
        if tries == MAX_ATTEMPTS:
            flag = True
        tries = tries + 1
    # The gateway could still be offline
    except ConnectionResetError:
        pass
# Checking response            
if (not flag) and response == "OK":
    registered = True
    print("Drone 3 ready to serve...")
    while not flag:
        payload = get_command_from_gateway()
        command = payload[0]
        # Checking requested command
        if command == "deliver":
                delivering = True 
                # Getting the delivery address
                address = payload[1]
                # Informing the gateway that the delivery has started
                message = ip + ":OK"
                s.sendto(message.encode(), gateway_address)
                print("Delivering to: %s" % address)
                # The drone takes some time to deliver the package
                time.sleep(random.randint(1, 5)) 
                message = ip + ":delivered"
                print("Delivery successful")
                start = time.time()
                for tries in range(1, MAX_ATTEMPTS + 1):
                    try:
                        # Informing the gateway that the delivery was successful
                        # and the drone is ready for the next delivery
                        response = talk_to_gateway(message, start, time.time())
                        delivering = False
                        break
                    except sk.timeout:
                        print("Waiting for response failed. Attempt: %d" % tries)
                        # The drone stops trying to receive a response after 5 tries
                        if tries == MAX_ATTEMPTS:
                            flag = True
                            
                if flag or response != "OK":
                    # Response message didn't arrive or didn't match the expected one
                    print("Couldn't receive response from gateway, shutting down")
        else:
            # The requested command is undefined,
            # so it will be ignored
            print("Unknown command: %s" % command)
else:
    # Couldn't connect or received message didn't match the expected one
    print("Connection failed, shutting down")

time.sleep(3)
# Closing the socket    
s.close()

