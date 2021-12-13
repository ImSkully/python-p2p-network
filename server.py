'''
    @author  Skully (https://github.com/ImSkully)
    @website https://skully.tech
    @email   contact@skully.tech
    @updated 13/12/21
    
    A simple peer-to-peer file sharing torrenting network with encrypted payload transportation
    and support for multiple clients over sockets with multi-threading.
'''

import socket
import sys
import os
import time
import threading
import shared
import hashlib
from _thread import *

# ======================================================================================================================== #
# Global Variable Definitions
# ======================================================================================================================== #

'''
    COMMANDS = {
        ["commandName"] = handlingFunction,
    }
'''
COMMANDS = {} # Create command dictionary.

'''
    CLIENT_FILES = {
        [(clientAddress)] = (
            "file_1.mp3",
            "file_2.mp3",
        ),
    }
'''
CLIENT_FILES = {} # Create dictionary to maintain what client has which files.
CONNECTIONS = [] # List of all clients currently connected.
SERVER_DIR = "tracked-files" # Name of the directory containing all server files.

# ======================================================================================================================== #
# Server Functions
# ======================================================================================================================== #

'''
    sendClientMessage(clientAddress, clientSocket, message)
        Sends the given message to the specified client socket.
'''
def sendClientMessage(clientAddress, clientSocket, message = False):
    if not message:
        message = "Something went wrong, please try again."

    clientSocket.sendto(message.encode(), clientAddress)

# ======================================================================================================================== #
# Data Input Parsing
# ======================================================================================================================== #

def parseInput(clientAddress = False, clientSocket = False, inputCommand = False):
    if not clientAddress or not clientSocket: return
    if not inputCommand:
        sendClientMessage(clientAddress, clientSocket, "Invalid command specified.")
        return

    print("[CLIENT] [{}:{}]".format(*clientAddress) + ": Input received: " + inputCommand)

    # If the input is a command.
    if (inputCommand[0] == shared.COMMAND_PREFIX):
        inputCommand = inputCommand[1::] # Remove the command prefix.
        commandParameters = inputCommand.split(' ') # Split the string using space as the delimiter.
        theCommand = commandParameters[0] # The command name.
        commandParameters.pop(0) # Remove the command itself from the list.

        # Parameter debug outputs.
        if shared.DEBUG:
            i = 1
            print("[DEBUG] Command: " + theCommand)
            for parameter in commandParameters:
                print("[DEBUG] Parameter #" + str(i) + ": " + parameter)
                i = i + 1

        if (theCommand in COMMANDS): # If the command exists.
            handlingFunction = COMMANDS[theCommand] # Fetch the handling function to invoke.
            handlingFunction(clientAddress, clientSocket, *commandParameters) # Invoke the respective function and pass all parameters.
        else:
            sendClientMessage(clientAddress, clientSocket, "Invalid command specified.")
    else:
        sendClientMessage(clientAddress, clientSocket, "Invalid command specified.")

# ======================================================================================================================== #
# Commands & Command Handlers
# ======================================================================================================================== #

def pingCommand(clientAddress, clientSocket):
    currentTime = time.time() # Get current epoch time.
    sendClientMessage(clientAddress, clientSocket, "[ping]" + str(currentTime)) # Send response to client with server's epoch.
COMMANDS["ping"] = pingCommand

def addFileCommand(clientAddress, clientSocket, fileName = False):
    if not fileName:
        sendClientMessage(clientAddress, clientSocket, "SYNTAX: /addfile [File Name]")
        return

    if (fileName not in CLIENT_FILES[clientAddress]):
        CLIENT_FILES[clientAddress].append(fileName)
        print("[SERVER] Added new file record for client {}:{}".format(*clientAddress) + ", file: " + fileName)
        sendClientMessage(clientAddress, clientSocket, "You have added the file '" + fileName + "' to the server tracker.")
    else:
        print("[SERVER] Client {}:{}".format(*clientAddress) + " attempted to add file '" + fileName + "' though already recorded they have this file, ignoring request.")
        sendClientMessage(clientAddress, clientSocket, "ERROR: You have already added the file '" + fileName + "' to the server tracker.")
COMMANDS["addfile"] = addFileCommand

def findFileCommand(clientAddress, clientSocket, fileName = False):
    if not fileName:
        sendClientMessage(clientAddress, clientSocket, "SYNTAX: /findfile [File Name]")
        return

    foundClients = [] # Array to hold all our clients that have the file.
    for theClient in CLIENT_FILES: # Loop through every client.
        for clientFiles in CLIENT_FILES[theClient]: # Loop through this specific client's files.
            if clientFiles == fileName: # If this file matches the file name we want.
                foundClients.append(theClient) # Add this client to the array since they have the file.

    if (foundClients): # If we found the file.
        clientsString = ""
        for client in foundClients:
            clientsString = clientsString + "[{}:{}".format(*client) + "] "
            print("[SERVER] File has been found on client: {}:{}".format(*client))
        sendClientMessage(clientAddress, clientSocket, "The following clients have that file: " + clientsString)
    else: # File was not found.
        print("[SERVER] The file '" + fileName + "' does not exist on server.")
        sendClientMessage(clientAddress, clientSocket, "The file '" + fileName + "' does not exist on the server.")
COMMANDS["findfile"] = findFileCommand

def fetchFileCommand(clientAddress, clientSocket, fileName = False):
    if not fileName:
        sendClientMessage(clientAddress, clientSocket, "SYNTAX: /fetchfile [File Name]")
        return

    # Check to see if the server has the file available.
    if not os.path.exists(SERVER_DIR + "/" + fileName):
        sendClientMessage(clientAddress, clientSocket, "ERROR: No file with the name '" + fileName + "' available on the server.")
        return

    print("[SERVER] [{}:{}]".format(*clientAddress) + ": Request to download file '" + fileName + "', starting..")
    
    #theFile = open(SERVER_DIR + "/" + fileName, 'rb') # Open file in binary.
    #fileData = theFile.read() # Read the contents of the file.

    with open(SERVER_DIR + "/" + fileName, mode = 'rb') as file: # b is important -> binary
        fileData = file.read()
    #theFile.close() # Close file input stream.

    sendClientMessage(clientAddress, clientSocket, "[fetchfile]" + fileName + ";SEPARATOR;" + str(fileData)) # Send data to client.
    print("[SERVER] [{}:{}]".format(*clientAddress) + ": Finished sending file!")
COMMANDS["fetchfile"] = fetchFileCommand

def showHelpCommand(clientAddress, clientSocket):
    sendClientMessage(clientAddress, clientSocket, "Available Commands:" + COMMAND_LIST)
COMMANDS["help"] = showHelpCommand

# Generate the command list.
COMMAND_LIST = ""
for commandName in COMMANDS: COMMAND_LIST = COMMAND_LIST + " /" + commandName + ","
COMMAND_LIST = COMMAND_LIST[:-1]

# ======================================================================================================================== #
# Socket Data Input/Output
# ======================================================================================================================== #

'''
    closeSockets()
        Closes all active socket connections that are still open.
'''
def closeSockets():
    for client in CONNECTIONS:
        print("[SERVER] Dropping connection for client {}:{}".format(*client[1]))
        client[0].close()

'''
    handleClient(clientSocket, clientAddress) : Threaded
        Function that is called whenever a new client connects and is run in a separate thread, handles client input.
'''
def handleClient(clientSocket = False, clientAddress = False):
    if not clientSocket or not clientAddress:
        print("[ERROR] @handleClient: clientSocket or clientAddress not received.")
        return

    if (clientAddress not in CLIENT_FILES):
            print("[SERVER] First time this client is connecting, initializing a file dictionary for them.")
            CLIENT_FILES[clientAddress] = list() # Initialize a new dictionary of client file definitions for this client.

    while True:
        data = clientSocket.recv(10000)
       
        if data:
            payload = data.decode().split(";HASH;") # Client payload.
            payloadHashed = hashlib.sha224(payload[1].encode()).hexdigest() # Serverside hash.

            if not (payload[0] == payloadHashed): # Check clients hash with the server's hash.
                print("[SERVER] Hash mismatch from client {}:{}!".format(*clientAddress))
                print("[SERVER] Ignoring request: '" + payload[1] + "'")
            else:
                if shared.DEBUG:
                    print("[DEBUG] [HASH] {}:{}".format(*clientAddress) + " sent verified payload.")

            if payload[1] == "exit": break # If client is quitting.
            parseInput(clientAddress, clientSocket, payload[1])
    # Actions to conduct when client disconnects.
    print("[SERVER] Closing connection for client {}:{}".format(*clientAddress))
    clientSocket.close() # Close this client's connection.
    CONNECTIONS.remove((clientSocket, clientAddress)) # Remove client from array.
    del(CLIENT_FILES[clientAddress]) # Clear the client's recorded files.

# Create a TCP/IP socket.
print('[SERVER] Opening server socket on {}:{}..'.format(*shared.SERVER_ADDRESS))
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SOCKET.bind(shared.SERVER_ADDRESS) # Bind the socket to the port.
SOCKET.listen(5) # Listen for incoming connections.

while True:
    try:
        if not os.path.exists(SERVER_DIR): # If a directory for the server files doesn't exist.
            os.makedirs(SERVER_DIR) # Create the directory.

        clientSocket, clientAddress = SOCKET.accept() # Wait and accept connections.
        print('[SERVER] Incoming client connection from {}:{}..'.format(*clientAddress))
        CONNECTIONS.append((clientSocket, clientAddress)) # Add this client to the connection list.
        threading._start_new_thread(handleClient, (clientSocket, clientAddress)) # Start new thread for this client.
    except KeyboardInterrupt as e:
        print("Shutting down the server..")
        break
closeSockets()
SOCKET.close()
