#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The listening server for the Chromeconomist's connection with Chromabot.

Very, very sketchy and impromptu, my first try at something even remotely similar to a 
REST-like API. Hopefully the pseudo-API I provide Reostra with, in addition to this listening
server, will allow Chromabot and Chromeconomist to mesh, adding new depth to the game.

Thanks go to Daniel Zappala at BYU for the skeleton of the listening code, found here:
http://ilab.cs.byu.edu/python/socket/echoserver.html
"""

import socket

host = ''
port = 17236
backlog = 5
size = 1024

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((host,port))
s.listen(backlog)

def pareRequest(request):
    print request
    return request

while True:
    client, address = s.accept()
    request = client.recv(size)
    if request:
        client.send(parseRequest(request))
    client.close()
    
