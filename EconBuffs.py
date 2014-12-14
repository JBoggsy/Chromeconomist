# -*- coding: utf-8 -*-
"""
Created on Sun Dec 14 14:49:05 2014

@author: boggs

Module to retrieve defensive buffs from Chromeconomist's DB
"""

import socket

host = "ec2-54-191-166-247.us-west-2.compute.amazonaws.com"
port = 17236
size = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def getEconBuffs(territory):
    """takes the territory name as the first argument. Please don't use the subreddit format
    e.g. "/r/MidnightMarsh" """
    s.connect((host,port))
    s.send(territory)
    data = s.recv(size)
    s.close()
    parts = data.split(':')
    context = parts[0]
    if context != 'ERROR':
        buff = float(parts[1])
        return buff
    else:
        return 0.0
        
if __name__ == '__main__':
    pass