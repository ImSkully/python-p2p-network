# Python Peer-to-Peer File Sharing Network
![License](https://img.shields.io/github/license/ImSkully/python-p2p-network)
![Repo Size](https://img.shields.io/github/languages/code-size/ImSkully/python-p2p-network)
![Version](https://img.shields.io/github/v/tag/ImSkully/python-p2p-network)

A simple peer-to-peer file sharing torrenting network with encrypted payload transportation and support for multiple clients over sockets with multi-threading. The application emulates multiple clients connecting to a single server in order to retrieve a list of clients which have files, and then be able to transport files across each client via sockets.

## Usage
1. Start the torrent server. (`python server.py`)
2. Start a client. (`python client.py <socket (0-25565)>`)

## Help
All clientsided commands are executed with plain words, for serversided commands the global command deilimeter is used to recognize commands that should be encrypted with a payload and sent to the server with the respective request. This can be changed in the `shared.py` file.

You can toggle debug outputs in `shared.py`.

## Design Documentation
For a detailed overview of the full system design and specification, along with usability of all features that exist, refer to the [Design Documentation available in the Wiki](https://github.com/ImSkully/python-p2p-network/wiki).
