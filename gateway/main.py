from email import message
from http import client
from socket import *
import threading

connected_drones = []
deliveries_to_do = []
deliveries_in_progress = {}
bufferSize = 1024


def wait_for_drone(droneSocket):
    while True:
        print("Thread waiting for a drone to register as free on {this_ip}:{drone_port}".format(
            this_ip=gethostbyname(gethostname()), drone_port=dronePort))
        bytesAddressPair = droneSocket.recvfrom(bufferSize)

        # Get the drone's address and port from message
        payload = bytesAddressPair[0].decode("utf-8").split(":")
        addressPort = (payload[0], int(payload[1]))
        message = (payload[2])

        print("Message from drone:{}".format(message))
        print("Drone IP Address:{}".format(addressPort))

        if (message == "register"):
            print("Drone registered as free on {address}".format(
                address=addressPort[0], port=addressPort[1]))
            connected_drones.append(addressPort)
        elif (message == "unregister"):
            print("Drone unregistered on {address}".format(
                address=addressPort[0], port=addressPort[1]))
            connected_drones.remove(addressPort)
        elif (message == "delivered"):
            print("Drone {drone} delivered to {delivery_address}. Now its free.".format(
                drone=addressPort, delivery_address=deliveries_in_progress[addressPort]))
            deliveries_in_progress.pop(addressPort)
        elif (message == "fail"):
            print("Drone {drone} failed to deliver to {delivery_address}. Now its free.".format(
                drone=addressPort, delivery_address=deliveries_in_progress[addressPort]))
            deliveries_to_do.append(deliveries_in_progress.pop(addressPort))
        print(connected_drones)


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
                while True:
                    bytesAddressPair = clientConnectionSocket.recv(bufferSize)
                    # Get the client's address and port from message
                    payload = bytesAddressPair.decode("utf-8").split(":")
                    addressPort = (payload[0], int(payload[1]))
                    command = (payload[2])
                    data = (payload[3])
                    print("Message from client:{}".format(command))
                    print("Client IP Address:{}".format(addressPort))
                    if (command == "deliver"):
                        print("Client {client} wants to deliver to {delivery_address}".format(
                            client=addressPort, delivery_address=payload[3]))
                        deliveries_to_do.append((addressPort, payload[3]))
                    elif (command == "drones"):
                        print("Client {client} wants to know all available drones".format(
                            client=addressPort))
                        print("Sending available drones...")
                        clientConnectionSocket.send(bytes(str(connected_drones), "utf-8"))
            except:
                print("Client {client} dropped".format(client=connectedClient))

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
