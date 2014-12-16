#!/usr/bin/env python2.7
"""
The listening server for the Chromeconomist's connection with Chromabot.

Very, very sketchy and impromptu, my first try at something even remotely similar to a 
REST-like API. Hopefully the pseudo-API I provide Reostra with, in addition to this listening
server, will allow Chromabot and Chromeconomist to mesh, adding new depth to the game.

Thanks go to Daniel Zappala at BYU for the skeleton of the listening code, found here:
http://ilab.cs.byu.edu/python/socket/echoserver.html

Big thanks to redditor /u/Reostra for looking over this code and making suggestions!
"""

import socket
import json
from Chromeconomist import failable

host = ''
port = 17236
backlog = 5
size = 1024

@failable
def openConnection(host=host,port=port,backlog=backlog):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.bind((host,port))
    s.listen(backlog)

def readTerritory(territory):
    territory = str(territory)
    territory = territory.replace('-','')
    territory = territory.replace('_','')
    territory = territory.replace('/r/','')
    territory = territory.replace('r/','')
    territory = territory.replace("'",'')
    territory = territory.lower()
    return territory

@failable
def parseRequest(request):
    """Parse the request Chromabot sends, and return the proper buff as
    a float, or None if an error occurs. Request should be any string
    form of the territory name. /r/AreusAntris, Areus Antris, 
    areusantris, and all others should work equally well."""
    
    #convert the territory Reo sends into one guaranteed to be readable
    territory = readTerritory(request)

    #make sure that the json file works, first. If it doesn't, return
    #an error to Chromabot instead the API will take care of errors
    #without Reo needing to code anything else.
    chromaData = None
    with open("EconomyInfo.json",'r') as f:
        chromaData = json.load(f)
    
    #check to see if the request is a valid one
    if territory in chromaData['LandInfo'].keys():
        return chromaData['LandInfo'][territory]['DEFbuff']
    else:
        return None

if __name__ == '__main__':
    openConnection()
    while True:
        try:
            client, address = s.accept()
            request = client.recv(size)
            if request:
                client.send(parseRequest(request))
            client.close()
    
