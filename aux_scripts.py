# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 14:37:38 2014

@author: boggs
"""
import praw
import traceback
import socket
from requests.exceptions import ConnectionError, HTTPError, Timeout
import logging as log

def failable(f):
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except praw.errors.APIException:
            full = traceback.format_exc()
            log.warning("Reddit API call failed! %s" % full)
            return None
        except ConnectionError:
            full = traceback.format_exc()
            log.warning("Connection error: %s", full)
        except (Timeout, socket.timeout, socket.error):
            full = traceback.format_exc()
            log.warning("Socket timeout! %s" % full)
            return None
        except HTTPError:
            full = traceback.format_exc()
            log.warning("HTTP error timeout! %s" % full)
            return None
    return wrapped
    
def readTerritory(territory):
    territory = str(territory)
    territory = territory.replace("$$","")
    territory = territory.replace("-","")
    territory = territory.replace("_","")
    territory = territory.replace("/r/","")
    territory = territory.replace("r/","")
    territory = territory.replace("'","")
    territory = territory.replace(" ","")
    territory = territory.lower()
    return territory

def flattenComments(comments):
    cmnts_out = []
    for comment in comments:
        if comment._replies:
            cmnts_out += comment._replies
        cmnts_out.append(comment)
    return cmnts_out
    
if __name__ == "__main__":
    pass