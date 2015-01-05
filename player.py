#!/usr/bin/env python2.7

"""A module for the Player class for the Chromeconomist bot, which will 
hold the different information for each player."""

import logging as log
from time import time

class Player(object):
    """A class that contains player info for the Chromeconomist bot, as
    well as some basic functions to create items, change the user's homeland, and change the type of 
    resource produced."""
    
    def __init__(self,username,homeland):
        self.username = username
        self.homeland = homeland
        self.home_buffs = (homeland.buff,homeland.penalty)
        self.items = {"food":0.0,"material":0.0,"luxury":0.0}
        self.resource_buffs = {"food":0.0,"material":0.0,"luxury":0.0}
        self.DEF_items = {}
        self.OFF_items = {}
        self.TRP_items = {}
        self.SPD_items = {}
        self.producing = homeland.buff
        self.last_produced = 0.0
        
    def produce(self):
        if time() < self.last_produced+3600:
            log.info("  User %s has already produced something this hour." % self.username)
            return False
        self.last_produced = time()
        log.info("    Producing %s for %s" % (self.producing,self.username))
        #this part determines whether the amount a user receives is influenced by their homeland
        if self.producing == self.home_buffs[0]:
            raw_bounty = 3
        elif self.producing == self.home_buffs[1]:
            raw_bounty = 1
        else:
            raw_bounty = 2
        bounty = raw_bounty * self.resource_buffs[self.producing]
        self.items[self.producing] += bounty
        return True
    
    def change_production(self,new_type):
        if new_type == "luxuries":
            new_type = "luxury"
        if new_type == "materials":
            new_type = "material"
        if new_type == "foods" or new_type == "foodstuff":
            new_type = "food"
        self.producing = new_type