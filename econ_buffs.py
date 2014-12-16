"""
Created on Sun Dec 14 14:49:05 2014

@author: boggs

Module to retrieve defensive buffs from Chromeconomist's DB

Big thanks to redditor /u/Reostra for looking over this code and making suggestions!
"""

import socket

host = "ec2-54-191-166-247.us-west-2.compute.amazonaws.com"
port = 17236
size = 1024



def getEconBuffs(territory):
    """Takes the territory name as the first argument. Any format should work."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host,port))
        s.send(territory)
        buff = s.recv(size)
        s.close()
        if buff != None:
            return buff
        else:
            return None
    except socket.error:
        return None
    except socket.timeout:
        return None
        
if __name__ == '__main__':
    pass