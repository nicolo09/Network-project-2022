from email import message
from http import client
from socket import *
import threading

connected_drones = {}
deliveries_to_do = {}
deliveries_in_progress = {}
bufferSize = 1024
localhost = "127.0.0.1"
timeoutTime = 3
clientConnectionSocket = None
lock = threading.Lock()

def start_deliver(drone, address):
    if deliveries_in_progress.get(drone) is None:
        #drone = (localhost, connected_drones[drone])
        print("Telling drone {drone} to deliver to {address}".format(drone=drone, address=address))
        droneSocket.sendto(("deliver:{address}".format(address=address)).encode(), (localhost, connected_drones[drone]))
        try:
            message = ""
            while message != "OK":
                droneSocket.settimeout(timeoutTime)
                bytesAddressPair, realAddress = droneSocket.recvfrom(bufferSize)
                # Get the drone's address and port from message
                payload = bytesAddressPair.decode("utf-8").split(":")
                addressPort = (payload[0], realAddress[1])
                message = (payload[1])
                if (message == "OK"):
                    deliveries_in_progress[drone] = address
            #else handle all messages arrived from drones
        except timeout:
            print("Drone {drone} timed out, telling client...".format(drone=drone))
            connected_drones.pop(drone)
            tell_client("Failed due to {drone} timeout".format(drone=drone))
    
def wait_for_drone(droneSocket):
    print("Thread waiting for a drone to send messages on {this_ip}:{drone_port}".format(
        this_ip=gethostbyname(gethostname()), drone_port=dronePort))
    while True:
        droneSocket.settimeout(timeoutTime)
        try:
            bytesAddressPair, realAddress = droneSocket.recvfrom(bufferSize)
            # Get the drone's address and port from message
            payload = bytesAddressPair.decode("utf-8").split(":")
            addressPort = (payload[0], realAddress[1])
            message = (payload[1])

            print("Message from drone:{}".format(message))
            print("Drone IP Address:{}".format(addressPort))

            if (message == "register"):
                print("Drone registered as free on {address}".format(
                    address=addressPort[0], port=addressPort[1]))
                connected_drones[addressPort[0]] = addressPort[1]
                droneSocket.sendto(b"OK", realAddress)
            elif (message == "unregister"):
                print("Drone unregistered on {address}".format(
                    address=addressPort[0], port=addressPort[1]))
                connected_drones.pop(addressPort)
                droneSocket.sendto(b"OK", realAddress)
            elif (message == "delivered"):
                print("Drone {drone} delivered to {delivery_address}. Now its free.".format(
                    drone=addressPort, delivery_address=deliveries_in_progress[addressPort[0]]))
                deliveries_in_progress.pop(addressPort[0])
                droneSocket.sendto(b"OK", realAddress)
            # elif (message == "failed"):
            #     print("Drone {drone} failed to deliver to {delivery_address}. Now its free.".format(
            #         drone=addressPort, delivery_address=deliveries_in_progress[addressPort]))
            #     deliveries_to_do.append(deliveries_in_progress.pop(addressPort))
            else:
                print("Unknown message from drone: " + message)
            print(connected_drones)
        except timeout:
            #No messages received from drones in 1 second, continue checking deliveries to do
            with lock:    
                if deliveries_to_do:
                    print("Dispatching deliveries...")
                    for delivery in deliveries_to_do:
                        start_deliver(delivery, deliveries_to_do[delivery])
                    deliveries_to_do.clear()

def wait_for_client(clientSocket):
    while True:
        print("Thread waiting for a client to register on {this_ip}:{client_port}".format(
            this_ip=gethostbyname(gethostname()), client_port=clientPort))
        clientSocket.listen(1)
        clientConnectionSocket, clientRealAddress = clientSocket.accept()
        try:
            print("Client trying to register...")
            bytesAddressPair = clientConnectionSocket.recv(bufferSize)
            # Get the client's address and port from message
            payload = bytesAddressPair.decode("utf-8").split(":")
            addressPort = (payload[0], int(payload[1]))
            command = (payload[2])
            data = (payload[3])
        except:
            print("Error receiving connection message from client")
            command = ""
        if (command == "cregister"):
            print("Client registered on {address}:{port}".format(
                address=addressPort[0], port=addressPort[1]))
            connectedClient = addressPort
            try:
                #Message handling
                while True:
                    bytesAddressPair = clientConnectionSocket.recv(bufferSize)
                    # Get the client's address and port from message
                    payload = bytesAddressPair.decode("utf-8").split(":")
                    addressPort = (payload[0], int(payload[1]))
                    command = (payload[2])
                    data = (payload[3:])
                    print("Message from client:{}".format(command))
                    print("Client IP Address:{}".format(addressPort))
                    if (command == "deliver"):
                        drone = data[0]
                        address = data[1]
                        print("Client {client} wants {drone} to deliver to {delivery_address}".format(
                            client=addressPort, drone=drone, delivery_address=address))
                        with lock:
                            if drone not in deliveries_to_do:
                                deliveries_to_do[drone] = address
                            else:
                                tell_client("Failed due to {drone} already busy".format(drone=drone))
                    elif (command == "drones"):
                        print("Client {client} wants to know all available drones".format(
                            client=addressPort))
                        print("Sending available drones...")
                        clientConnectionSocket.send(bytes(str(connected_drones), "utf-8"))
            except:
                print("Client {client} dropped".format(client=connectedClient))

def tell_client(message):
    clientConnectionSocket.send(bytes(message, "utf-8"))

# Host dal lato droni
droneIp = "localhost"
# Porta dal lato droni
dronePort = 25000
# crea un socket INET per i droni di tipo DGRAM (UDP)
droneSocket = socket(AF_INET, SOCK_DGRAM)
# associa il socket alla porta scelta per i droni
droneSocket.bind((droneIp, dronePort))

# Stacco un thread che aspetti i droni che si registrano
threading.Thread(target=wait_for_drone, args=[droneSocket]).start()

# Host dal lato client
clientIp = "localhost"
# Porta dal lato client
clientPort = 26000
# crea un socket INET per il client di tipo STREAM (TCP)
clientSocket = socket(AF_INET, SOCK_STREAM)
# associa il socket alla porta scelta per il client
clientSocket.bind((clientIp, clientPort))

# Stacco un thread che aspetti i droni che si registrano
threading.Thread(target=wait_for_client, args=[clientSocket]).start()
