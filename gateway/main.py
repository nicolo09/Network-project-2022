import signal
from socket import *
import sys
import threading
import time

# Set to false to disable simulation and work on effective network instead of localhost
SIM = True

connected_drones = {}
deliveries_to_do = {}
deliveries_in_progress = {}
bufferSize = 1024
localhost = "127.0.0.1"
timeoutTime = 4
clientConnectionSocket = None
deliveriesLock = threading.Lock()
maxTries = 4


def getDroneTrueAddressPort(drone):
    if (SIM == True):
        return (localhost, connected_drones[drone])
    else:
        return (drone, connected_drones[drone])


def start_deliver(drone, address):
    # Check if drone is available
    if deliveries_in_progress.get(drone) is None:
        # Send deliver command to drone
        print("Asking drone {drone} to deliver to {address}".format(
            drone=drone, address=address))
        tries = 0
        exitFlag = False
        while not exitFlag and tries < maxTries:
            t1 = time.time()
            droneSocket.sendto(("deliver:{address}".format(
                address=address)).encode(), getDroneTrueAddressPort(drone))
            try:
                message = ""
                # Wait for drone to respond discarding every other message
                while message != "OK":
                    droneSocket.settimeout(timeoutTime)
                    bytesAddressPair, realAddress = droneSocket.recvfrom(
                        bufferSize)
                    # Get the drone's address and port from message
                    payload = bytesAddressPair.decode("utf-8").split(":")
                    #addressPort = (payload[0], realAddress[1])
                    message = (payload[1])
                    if (message == "OK"):
                        deliveries_in_progress[drone] = address
                        print("Drone {drone} is now delivering to {address}, packet travel time was {time}ms".format(
                            drone=drone, address=address, time=((time.time() - t1)/2)*1000))
                        exitFlag = True
            except timeout:
                # Retry
                print("Drone {drone} response wait time out, retrying...".format(
                    drone=drone))
                tries = tries + 1
            except error:
                # Drone packet raised an error, assuming drone is dead
                print("Drone {drone} reset connection, telling client...".format(
                    drone=drone))
                connected_drones.pop(drone)
                tell_client(
                    "fail: {drone} reset connection".format(drone=drone))
                exitFlag = True
        if (exitFlag == False):
            # Drone did not respond in time assuming it has timed out, inform client
            print("Drone {drone} timed out, telling client...".format(
                drone=drone))
            connected_drones.pop(drone)
            tell_client("fail: {drone} timed out".format(drone=drone))


def wait_for_drone(droneSocket):
    # Handle drone messages
    print("Thread waiting for a drone to send messages on {this_ip}:{drone_port}".format(
        this_ip=gethostbyname(gethostname()), drone_port=dronePort))
    while True:
        try:
            droneSocket.settimeout(timeoutTime)
            # This recvfrom will stay blocked for a limited amount of time (timeoutTime), so that this thread can handle deliveries to do
            bytesAddressPair, realAddress = droneSocket.recvfrom(bufferSize)
            # Get the drone's address from message and port from sender address (real port)
            payload = bytesAddressPair.decode("utf-8").split(":")
            addressPort = (payload[0], realAddress[1])
            message = (payload[1])

            print("Drone({drone}): {message}".format(
                drone=addressPort[0]+":"+str(addressPort[1]), message=message))

            # Different possible messages from drones
            if (message == "register"):
                print("Drone registered as free on {address}".format(
                    address=addressPort[0], port=addressPort[1]))
                connected_drones[addressPort[0]] = addressPort[1]
                droneSocket.sendto(b"OK", realAddress)
            elif (message == "unregister"):
                if (addressPort[0] in deliveries_in_progress):
                    # Drone is unregistering while delivering, inform client
                    print("Drone {drone} unregistering while delivering, informing client...".format(
                        drone=addressPort[0]))
                    tell_client("fail: {drone} unregistered while delivering".format(
                        drone=addressPort[0]))
                if (addressPort[0] in connected_drones):
                    print("Drone unregistered on {address}".format(
                        address=addressPort[0]))
                    connected_drones.pop(addressPort)
                # Sending ACK anyway
                droneSocket.sendto(b"OK", realAddress)
            elif (message == "delivered"):
                if (addressPort[0] in deliveries_in_progress):
                    msg = "Drone {drone} delivered to {delivery_address}. Now its free.".format(
                        drone=addressPort, delivery_address=deliveries_in_progress[addressPort[0]])
                    print(msg)
                    deliveries_in_progress.pop(addressPort[0])
                    droneSocket.sendto(b"OK", realAddress)
                    tell_client(msg)
                else:
                    msg = "Drone {drone} delivered to {delivery_address} but was not delivering".format(
                        drone=addressPort, delivery_address=deliveries_in_progress[addressPort[0]])
                    print(msg)
                    droneSocket.sendto(b"NO", realAddress)
                    tell_client(msg)
            # elif (message == "failed"):
            #     print("Drone {drone} failed to deliver to {delivery_address}. Now its free.".format(
            #         drone=addressPort, delivery_address=deliveries_in_progress[addressPort]))
            #     deliveries_to_do.append(deliveries_in_progress.pop(addressPort))
            else:
                print("Unknown message from drone: " + message)
            #print("Connected drones are: " + connected_drones)
        except timeout:
            # No messages received from drones in 1 second, continue by checking if there are deliveries to do
            with deliveriesLock:
                if deliveries_to_do:
                    print("Dispatching deliveries...")
                    for delivery in deliveries_to_do:
                        start_deliver(delivery, deliveries_to_do[delivery])
                    deliveries_to_do.clear()
        except OSError:
            print("Drone thread is terminating")
            return


def wait_for_client(clientSocket):
    # This while makes it possible for a client to reconnect after a disconnection
    while True:
        try:
            # Wait for client to connect on TCP socket
            print("Thread waiting for a client to register on {this_ip}:{client_port}".format(
                this_ip=gethostbyname(gethostname()), client_port=clientPort))
            clientSocket.listen(1)
            global clientConnectionSocket
            clientConnectionSocket, clientRealAddress = clientSocket.accept()
        except error:
            # Error on accept, socket is not valid or it has been closed, terminate thread
            print("Client thread is terminating")
            return
        try:
            # Client has opened connection, wait for registering message
            print("Client trying to register...")
            bytesAddressPair = clientConnectionSocket.recv(bufferSize)
            # Get the client's address and port from message
            payload = bytesAddressPair.decode("utf-8").split(":")
            addressPort = (payload[0], clientRealAddress[1])
            command = payload[1]
            data = payload[2]
        except Exception:
            print("Error receiving connection message from client")
            command = ""
        if (command == "cregister"):
            print("Client registered on {address}:{port}".format(
                address=addressPort[0], port=addressPort[1]))
            connectedClient = addressPort
            # Client registration complete
            closed = False
            try:
                # Message handling loop
                while closed == False:
                    bytesAddressPair = clientConnectionSocket.recv(bufferSize)
                    # Get the client's address and port from message
                    payload = bytesAddressPair.decode("utf-8").split(":")
                    if (payload[0] == ""):
                        print("Client closed connection")
                        clientConnectionSocket.close()
                        closed = True
                    else:
                        addressPort = (payload[0], clientRealAddress[1])
                        command = payload[1]
                        data = payload[2:]
                        print("Client({client}): {command}".format(
                            client=addressPort[0]+":"+str(addressPort[1]), command=command))
                        if (command == "deliver"):
                            # Deliver message received
                            drone = data[0]
                            address = data[1]
                            print("Client {client} wants {drone} to deliver to {delivery_address}".format(
                                client=addressPort, drone=drone, delivery_address=address))
                            with deliveriesLock:
                                # Try to add delivery job to deliveries to do, check if requested drone is connected and is free
                                if drone not in connected_drones:
                                    message = "fail: {drone} not connected".format(
                                        drone=drone)
                                    print(message)
                                    tell_client(message)
                                elif drone in deliveries_to_do or drone in deliveries_in_progress:
                                    message = "fail: {drone} already busy".format(
                                        drone=drone)
                                    print(message)
                                    tell_client(message)
                                else:
                                    deliveries_to_do[drone] = address
                        elif (command == "drones"):
                            # Send to client the list of connected drones
                            print("Client {client} wants to know all available drones, sending list...".format(
                                client=addressPort))
                            tell_client(str(connected_drones))
                        elif (command == "ping"):
                            # Client asked for a ping
                            print("Client {client} sent a ping request, answering".format(
                                client=addressPort))
                            tell_client("pong")
                        else:
                            tell_client("unknown command")
            except error as e:
                print("Client {client} dropped: {error}".format(
                    client=connectedClient, error=e))
                clientConnectionSocket.close()
                closed = True
                clientConnectionSocket = None
        else:
            clientConnectionSocket.shutdown(SHUT_RDWR)
            clientConnectionSocket.close()
            print("Client did not send cregister command, connection dropped")
            clientConnectionSocket = None


def tell_client(message):
    if (clientConnectionSocket is not None):
        clientConnectionSocket.send(message.encode("utf-8"))


def exit_gracefully(_signo, _stack_frame):
    # Close all sockets and exit
    print("Exiting...")
    droneSocket.shutdown(SHUT_RDWR)
    droneSocket.close()
    global clientConnectionSocket
    if clientConnectionSocket is not None:
        clientConnectionSocket.shutdown(SHUT_RDWR)
        clientConnectionSocket.close()
    try:
        clientSocket.shutdown(SHUT_RDWR)
    except OSError:
        pass
    clientSocket.close()
    clientThread.join()
    droneThread.join()
    sys.exit(0)


if __name__ == "__main__":
    # Drone side ip
    droneIp = "0.0.0.0"
    # Drone side port
    dronePort = 25000
    # Create a DGRAM (UDP) type socket for drones
    droneSocket = socket(AF_INET, SOCK_DGRAM)
    droneSocket.bind((droneIp, dronePort))

    # Thread that handles drone messages
    droneThread = threading.Thread(target=wait_for_drone, args=[droneSocket])
    droneThread.start()

    # Client side ip
    clientIp = "0.0.0.0"
    # Client side port
    clientPort = 26000
    # Create a STREAM (TCP) type socket for client
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.bind((clientIp, clientPort))

    # Thread that handles client messages
    clientThread = threading.Thread(
        target=wait_for_client, args=[clientSocket])
    clientThread.start()

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    # Since the main thread will have to catch the signals, it just loop until signal is received
    while True:
        time.sleep(2)
