'''
    @author  Skully (https://github.com/ImSkully)
    @website https://skully.tech
    @email   contact@skully.tech
    @updated 13/12/21
    
    A simple peer-to-peer file sharing torrenting network with encrypted payload transportation
    and support for multiple clients over sockets with multi-threading.

    Usage:
        #> python client.py <socket>
            <socket>: If specified, the client will use the socket number given to connect to the server.
'''

import socket
import sys
import random
import time
import os
import shutil
import shared
import gzip
import hashlib
import struct
from fsplit.filesplit import FileSplit

# ======================================================================================================================== #
# Global Variable Definitions
# ======================================================================================================================== #

'''
    COMMANDS = {
        ["commandName"] = handlingFunction,
    }
'''
COMMANDS = {} # Create command dictionary.

CLIENT_SOCKET = random.randrange(1, 25565) # Generate a random socket number.
if len(sys.argv) > 1: CLIENT_SOCKET = int(sys.argv[1]) # If socket ID was provided in command line, use that.

DIRECTORY = str(CLIENT_SOCKET) # Each client places its file into a folder named after its socket number.

CLIENT_ADDRESS = (shared.SERVER_ADDRESS[0], CLIENT_SOCKET) # Socket IP and port to establish a connection to.

print("[CLIENT] Establishing connection to server..")
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket.
SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SOCKET.bind(CLIENT_ADDRESS)
SOCKET.connect(shared.SERVER_ADDRESS) # Connect the socket to the port where the server is listening.


# ======================================================================================================================== #
# Client Functions
# ======================================================================================================================== #

'''
[DIRECTORY : Socket]
    > [raw]
        > [fileName]
            > fileName_X (where _X is the file partition)

    > fileName.mp3
'''

'''
    buildBinaryFile(fileName = False, fileBinary = False)
        Starts building the binary file using the binary data provided and places it into the client's directory.
'''
def buildBinaryFile(fileName = False, fileBinary = False):
    if not fileName or not fileBinary: return

    print("[CLIENT] Start build of file '" + fileName + "'..")
    newFile = open(DIRECTORY + "/" + fileName, "wb")
    newFile.write(fileBinary.encode())
    newFile.close()
    print("[CLIENT] Done! (File location: " + DIRECTORY + "/" + fileName + ")")

# ======================================================================================================================== #
# Data Input Parsing
# ======================================================================================================================== #

def parseClientCommand(command):
    commandParameters = command.split(' ') # Split the string using space as the delimiter.
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
        handlingFunction(*commandParameters) # Invoke the respective function and pass all parameters.
    else:
        print("[CLIENT] Invalid command specified.")

# ======================================================================================================================== #
# Commands & Command Handlers
# ======================================================================================================================== #

"""
    Command: /compress [File Name]
        [File Name] - The path to the file to compress.
"""
def compressFile(fileName = False):
    if not fileName:
        print("SYNTAX: /compress [File Name]")
        return

    print("Starting compression..")
    # Check to see if the client has the file to split.
    if not os.path.exists(DIRECTORY + "/" + fileName):
        print("ERROR: You do not have the full file!")
        return

    with open(DIRECTORY + "/" + fileName, "rb") as fileInput, open(DIRECTORY + "/" + fileName + ".gz", "wb") as fileOutput:
        shutil.copyfileobj(fileInput, fileOutput)
    print("Done! (File location: " + DIRECTORY + "/" + fileName + ".gz)")
COMMANDS["compress"] = compressFile

"""
    Command: /decompress [File Name]
        [File Name] - The path to the file to decompress.
"""
def decompressFile(fileName = False):
    if not fileName:
        print("SYNTAX: /decompress [File Name]")
        return

    print("Starting decompression..")
    # Check to see if the client has the file to split.
    if not os.path.exists(DIRECTORY + "/" + fileName + ".gz"):
        print("ERROR: A compressed version of that file does not exist!")
        return

    with open(DIRECTORY + "/" + fileName + ".gz", "rb") as fileInput, open(DIRECTORY + "/" + fileName, "wb") as fileOutput:
        shutil.copyfileobj(fileInput, fileOutput)
    print("Done! (File location: " + DIRECTORY + "/" + fileName + ".gz)")
COMMANDS["decompress"] = decompressFile

"""
    Command: /build [File Name]
        [File Name] - The path to the file that should be built using segments that have been fetched.
"""
def constructFile(fileName):
    print("Starting construct of file '" + fileName + "'..")
    
    # Check to see if the client already has the file constructed.
    if os.path.exists(DIRECTORY + "/" + fileName):
        print("ERROR: You already have this file constructed!")
        return

    # Check to see if the client has segments.
    if not os.path.exists(DIRECTORY + "/raw/" + fileName):
        print("ERROR: You don't have any segments of that file to build from!")
        return

    for rawFile in sorted(os.listdir(DIRECTORY + "/raw/" + fileName)):
        # Iterating through each file, add them on to the output mp3 file.
        with open(DIRECTORY + "/" + fileName, "ab") as outputFile, open(DIRECTORY + "/raw/" + fileName + "/" + rawFile, "rb") as inputFile:
            outputFile.write(inputFile.read()) # Read the contents and add to output.
    print("Done! (File location: " + DIRECTORY + "/" + fileName + ")")
COMMANDS["build"] = constructFile

"""
    Command: /split [File Name]
        [File Name] - The path to a file that should be split into specific bytes.
"""
def splitFile(fileName):
    print("Starting split of file '" + fileName + "'..")

    # Check to see if the client has the file to split.
    if not os.path.exists(DIRECTORY + "/" + fileName):
        print("ERROR: You do not have the full file!")
        return

    outputLocation = DIRECTORY + "/raw/" + fileName + "/"
    if not os.path.exists(outputLocation): # If a directory for this client socket doesn't exist.
        os.makedirs(outputLocation) # Create a directory.

    FileSplit(file = DIRECTORY + "/" + fileName, splitsize = 50000, output_dir = outputLocation).split()
    print("Done! (Raw Files: " + outputLocation + ")")
COMMANDS["split"] = splitFile

"""
    Command: /help
    Outputs all available commands to the CLI.
"""
def showHelpCommand():
    print("[CLIENT] Available Commands:" + COMMAND_LIST)
COMMANDS["help"] = showHelpCommand

# Generate the command list.
COMMAND_LIST = ""
for commandName in COMMANDS: COMMAND_LIST = COMMAND_LIST + " /" + commandName + ","
COMMAND_LIST = COMMAND_LIST[:-1]

# ======================================================================================================================== #
# Socket Data Input/Output
# ======================================================================================================================== #

try:
    while True:
        if not os.path.exists(DIRECTORY): # If a directory for this client socket doesn't exist.
            os.makedirs(DIRECTORY) # Create a directory.

        command = input("Please specify a command: ") # Get user input from command line.
        if len(command) > 0: # If the client has provided an input.
            if (command[0] == shared.COMMAND_PREFIX) or command == "exit": # If user is providing a server command.
                rawCommand = command
                command = hashlib.sha224(command.encode()).hexdigest() + ";HASH;" + command
                command = command.encode() # Encode the command to byte code.
                SOCKET.sendall(command) # Send the encoded command to the server.

                if rawCommand == "exit": break # Exit command to quit.
                
                # Listen for a response from server.
                serverResponse = SOCKET.recv(10000)

                if serverResponse:
                    serverResponse = str(serverResponse).replace("'", '').replace("\"", '') # Convert to string, remove apostrophes and quotations.
                    serverResponse = serverResponse[1::] # Remove starting apostrophe and byte code prefix. [b]

                    # Parse command specific responses from server.
                    if "[ping]" in serverResponse:
                        currentTime = time.time() # Get the current epoch time.
                        serverResponse = serverResponse.replace("[ping]", '') # Remove the [ping] prefix.
                        difference = currentTime - float(serverResponse) # Take the client's epoch from the servers to calculate difference in ms.
                        print("Pong! (Response took " + str(round(difference, 4)) + "ms)")
                    elif "[fetchfile]" in serverResponse:
                        serverResponse = serverResponse.replace("[fetchfile]", '') # Remove the [fetchfile] prefix.
                        responseData = serverResponse.split(";SEPARATOR;b") # Separate the file
                        buildBinaryFile(responseData[0], responseData[1])
                    else:
                        # No command specific action, just print raw response.
                        print("[SERVER] " + serverResponse)
            else:
                parseClientCommand(command)
finally:
    print('Closing connection to server..')
    SOCKET.close()
    print("Goodbye!")