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
import json
import sys

host = ''
port = 17236
backlog = 5
size = 1024

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((host,port))
s.listen(backlog)

def parseRequest(request):
    """parse the request Chromabot sends, and return the proper buff as a float"""

    #make sure that the json file works, first. If it doesn't, return an error to Chromabot instead
    #the API will take care of errors with Reo needing to code anything else.
    try:
        chromaData = json.load(open("EconomyInfo.json",'r'))
    except:
        e = sys.exc_info()
        return ('ERROR',e)
    
    #check to see if the request is a valid one
    if request in chromaData['landInfo'].keys():
        return (request,chromaData['landInfo'][request]['DEFbuff'])

while True:
    client, address = s.accept()
    request = client.recv(size)
    if request:
        client.send(parseRequest(request))
    client.close()
    
