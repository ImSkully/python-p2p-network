'''
    @author  Skully (https://github.com/ImSkully)
    @website https://skully.tech
    @email   contact@skully.tech
    @updated 13/12/21
    
    A simple peer-to-peer file sharing torrenting network with encrypted payload transportation
    and support for multiple clients over sockets with multi-threading.
'''

# ======================================================================================================================== #
# Shared Variable Definitions
# ======================================================================================================================== #

DEBUG = True # Toggles debugging outputs.
COMMAND_PREFIX = "/" # The prefix to use for the command.
SERVER_ADDRESS = ('localhost', 10000) # Socket IP and port to establish a connection to.