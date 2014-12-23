#!/usr/bin/env python2.7

"""
Name:        chromeconomist
Purpose:     To regulate the economy of the reddit based game Chroma.
Author:      James Boggs
Created:     10/04/2014
Copyright:   (c) James Boggs 2014
Licence:     Beer license (You can use this all you want, but if you
             meet me you owe me a beer)
            
Current features: Allows users to register with a subreddit as a home
territory, change their production type, create from a list of items,
check their account balance, and trade ith other players. At the moment,
all data is stored on a humongous JSON file is a mess of nested lists
and dictionaries. 

Inr the future:
Convert to PEP8 guidlines, turn users, lands, trades, and commands into
classes, create a comment aggregator and sorter, refactor command 
extraction into a separate method, and add more features and items.
"""

#### NOTES FOR REO:
#### @failable doesn't appear to work inside of a function, or perhaps
#### when its not above a function definition. Can decorators wrap single
#### lines of code or do they have to be applied to whole functions?

import logging as log
from datetime import timedelta
from string import punctuation
from json import load,dump,loads
from time import asctime,gmtime,time,sleep


import praw
from aux_scripts import failable, readTerritory, flattenComments
from inflect import engine

class Bot(object):
    def __init__ (self, reddit,economist_info):
        log.basicConfig(filename="ChromeconomistRunLog.txt",level=log.WARNING,
                        format="%(levelname)s @ %(asctime)s : %(message)s")
        log.info("Beginning a new run of the Chromeconomist bot.")
        self.land_info = economist_info["land_info"]
        self.user_info = economist_info["user_info"]
        self.item_info = economist_info["item_info"]
        self.data = {"land_info":self.land_info,"user_info":self.user_info,
                    "item_info":self.item_info}
        self.lands = self.land_info.keys()
        log.info("Lands: %s" % self.lands)
        log.info("JSON info loaded")
        self.r = reddit
        log.info("Connected to Reddit")
        self.i = engine()
        self.trade_number = 0
        self.active_trades = dict() #need to persist this
        self.recruit_id = "2pd4di"
        self.mods = ["eliminioa","reostra"]
        
## Will refactor the extraction of commands in parse_land and parse_PMs
## into an extract_commands(self,message) method. This will be far more
## powerful than the current extraction method I use. The aim is for it
## to allow multiple commands.

    @failable
    def grab_commands(self):
        """Used to find all comments and pms that contain a command, then 
        put them in a list for their commands to be extracted. First half
        of a refactored version of the old parse_lands() and parse_pms()
        functions."""
        for land in self.lands:
            land_stats = self.land_info[land]
            self.current_sub = self.r.get_subreddit(land_stats["srname"])
            print self.current_sub
            log.info("Current sub: %s" % self.current_sub)
            
            #make this part work better, sort comments by time
            #can't proceed on this part until I figure out the
            #issue with praw.helpers.flatten_tree
            comments = [c for c in self.r.get_comments(self.current_sub,limit=200)]
            
            raw_cmnds = [] 
            placeholder_ID = land_stats["placeholder_ID"]
            got_placeholder = False #make sure only the first comment is used as a place holder
            for comment in comments:
                if not got_placeholder:
                    ref_id = comment.id
                    log.info("  Updated placeholder id to %s @ %s" % (ref_id,
                                           asctime(gmtime(comment.created))))
                    self.land_info[land]["placeholder_ID"] = ref_id
                    self.data["land_info"] = self.land_info
                    got_placeholder = True
                if comment.id == placeholder_ID:
                    log.info("    Arrived at placeholder!")
                    print ("Arrived at placeholder!")
                    ref_id = comment.id
                    break
                if ("$$" in comment.body):
                    log.info("  New command found: %s" % comment)
                    raw_cmnds.append(comment)
        new_pms = self.r.get_unread(True,True)
        for pm in new_pms:
            if not pm.was_comment:
                raw_cmnds.append(pm)
                pm.mark_as_read()
        self.extract_commands(raw_cmnds)
            
    @failable
    def extract_commands(self,raw_cmnds):
        bot_cmnds = []
        for comment in raw_cmnds:
            if ("$$" in comment.body):
                if str(comment.author).lower() not in self.user_info:
                    print ("  User %s not found, alerting" % comment.author)
                    log.warning("  User %s not found, alerting" % comment.author)
                    comment.reply("User not found! Please register for the \
                                 Chromeconomist bot [here](http://redd.it/%s)"\
                                 % (self.recruit_id))
                else:
                    log.info("  New command found: %s" % comment)
                    raw_cmd = comment.body.splitlines()
                    for line in raw_cmd:
                        if "$$" in line:
                            cmd_line = line.replace("$$","")
                            cmd_parts = cmd_line.split()
                            cmd_time = comment.created
                            author = str(comment.author).lower()
                            action = cmd_parts[0].lower()
                            resource = cmd_parts[1:]
                            command = [author,action,resource,cmd_time,comment]
                            bot_cmnds.append(command)
                            log.info("    Parsed command as %s" % command)
        self.parse_commands(bot_cmnds)
    
    @failable
    def parse_commands(self,bot_cmnds):
        for command in bot_cmnds:
            author, action, resource, cmd_time, comment = command
            #This is the part which reads produce commands. DONE as of 6/6/2014
            if action == "produce":
                self.change_production(author,resource[0].strip(punctuation),comment)
                print ("%s changed their resource to %s" % (author,resource[0]))
                log.info("%s changed their resource to %s" % (author,resource[0]))
            #This is the part which reads creation commands. DONE as of 15/6/2014
            elif action == "create":
                print ("User %s is creating %s %s" % (author, resource[0],self.i.plural_noun(resource[1],resource[0])))
                log.info("User %s is creating %s %s" % (author, resource[0],self.i.plural_noun(resource[1],resource[0])))
                self.user_info[author]["last_creation"] = cmd_time
                self.create(author,int(resource[0]),resource[1],comment)
                
            #this reads balance display commands, and replies to the user with their account summary. DONE as of 1/7/2014
            elif action == "balance":
                messages = []
                messages.append("Hello %s, your account balance stands as follows:\
                                \n\n-----\n" % author)
                for item in self.user_info[author]:
                    # Will make this more automated when user is made into a class.
                    # User.balance will contain item counts alone.
                    if item in ["last_produced","last_creation","producing","home"]:
                        continue
                    
                    messages.append("%s: %s \n" % (self.i.plural_noun(
                                                      item,self.user_info[author][item]),
                                                  self.user_info[author][item]
                                                  ))
                time_to_production = timedelta(seconds=(self.user_info[author]["last_produced"]+300-time()))
                messages.append("-----\n\nYou will produce %s in %s." % (self.user_info[author]["producing"],
                                                                         str(time_to_production)))
                comment.reply("\n".join(messages))
                
            #this reads trading commands. A brief preface, becaus this command is a bit trickier than the rest DONE as of 15/7/2014:
            #trade command is "trade [count] [item] for [count] [item] with [user]" therefore:
            #resource[0] = the number of items the user is trading away
            #resource[1] = the type of item the user is trading away
            #resource[3] = the number of items the user is trading for
            #resource[4] = the type of item the user is trading for
            #resource[6] = the player the user is trading with
            elif action == "trade":
                if resource[0] == "accept":
                    trade_num = int(resource[1].strip("$$"))
                    print ("%s has accepted trade offer #%s" % (author,trade_num))
                    log.info("%s has accepted trade offer #%s" % (author,trade_num))
                    self.accept_trade_offer(self,author,trade_num,comment)
                else:                    
                    log.info("%s is trying to trade %s %s for %s %s with %s" % (author,resource[0],
                                                                                self.i.plural(resource[1],resource[0]),
                                                                                resource[3],
                                                                                self.i.plural(resource[4],resource[3]),
                                                                                resource[6]))
                    self.make_trade_offer(self,author,resource[:7],comment)
            #this allows me to add items. DONE as of 24/7/14
            #command resources:
            #resource[0] = the name of the new item
            #resource[1] = cost in format {"item":cost,"item":cost,etc}
            #resource[2] = pre-reqs in format ("item","item",etc)
            elif action =="add" and str(author)=="eliminioa":
                print ("Adding %s" % resource[0])
                log.info("Adding %s" % resource[0])
                self.add_item(self,resource,comment)
            else:
                print ("%s tried the '%s' command, which is not ready yet!" % (author,action))
                log.warning("%s tried the '%s' command, which is not ready yet!" % (author,action))
                
    #this function parses a "produce" command, altering what the user produces every iteration
    @failable
    def change_production(self,author,resource,comment):
        ## At the moment, users can only produce base materials. In the
        ## future I will change it so that users can produce "free"
        ## items directly, e.g. ores, coal, or basic foodstuff
        material_keywords = ["wood","lumber","stone","stones","brick","bricks","material","materials"]
        luxury_keyowrds = ["gold","diamonds","pearls","ivory","silk","spice","spices","pearl","chocolate","luxury","luxuries"]
        if resource in material_keywords:
            resource = "material"
        elif resource in luxury_keyowrds:
            resource = "luxury"
        else:
            resource = "food"
        self.user_info[author]["producing"] = resource
        self.data["user_info"] = self.user_info
        comment.reply("You are now producing %s" % resource)


    #this function credits a user with produced goods every iteration
    def produce(self,author):
        if time() < self.user_info[author]["last_produced"]+60:
            log.info("  User %s has already produced something this hour." % author)
            return False
        self.user_info[author]["last_produced"] = time()
        resource = self.user_info[author]["producing"]
        log.info("    Producing "+resource+" for "+author)
        bonus = self.land_info[self.user_info[author]["home"]]["bonus"]
        log.info("    Land bonus: "+bonus)
        penalty = self.land_info[self.user_info[author]["home"]]["penalty"]
        log.info("    Land penalty: "+penalty)
        #this part determines whether the amount a user receives is influenced by their homeland
        if bonus == resource:
            bounty = 1.5
        elif penalty == resource:
            bounty = .5
        else:
            bounty = 1
        for bonus_item in self.item_info["craftBuffs"]: 
            if bonus_item[0] == resource:
                if bonus_item in self.user_info[author]:
                    BICount = self.user_info[author][bonus_item] #amount of the bonus item user has
                    bonus_factor = self.item_info["craftBuffs"][bonus_item][1] * BICount
                    bounty = bounty*(1 + (self.item_info["craftBuffs"][bonus_item] * BICount))
                    log.info("    %s has %s %s, which grants them %s percent more production for %s!"
                             % (author, BICount,bonus_item,bonus_factor,resource))
        log.info("    Produced resources: %s %s" % (bounty,resource))
        self.user_info[author][resource] += bounty
        self.data["user_info"] = self.user_info
        return True

    #As titled, this function parses a create command, credits the user
    #with their items, and subtracts the appropriate amount of resources.
    @failable    
    def create(self,author,amount,item,comment):
        if self.i.singular_noun(item):
            item = self.i.singular_noun(item)
        log.info("    Item to be created: %s" % item)
        log.info("    Amount to be created: %s" % amount)
        try:
            item_cost = self.item_info[item]
        except KeyError:
            comment.reply("The item you're trying to make isn't a thing yet. Sorry.")
            log.warning("%s tried to make %s, which isn't an item yet!" % (author,item))
            return
        log.info("    Item cost: %s" % item_cost)
        good_for_it = True #can the user pay for it?
        
        #actually make the user pay for it
        for material in item_cost:
            count = float(item_cost[material])*amount
            log.info("    %s requires %s %s" % (item,count,self.i.plural_noun(material,count)))
            if material in self.user_info[author].keys():
                user_amount =self.user_info[author][material]
            else:
                user_amount = 0
            log.info("    User has %s %s" % (user_amount,self.i.plural_noun(material,user_amount)))
            if user_amount < count:
                msg_str ="You do not have enough %s to make %s %s." % (material,amount,item)
                comment.reply(msg_str)
                log.info("    Informed user that they do not have sufficient resources.")
                good_for_it = False
        if good_for_it:
            for material in item_cost:
                self.user_info[author][material] -= int(item_cost[material])*amount #takes away cost for each item
                log.info("    User's new amount of %s is %s" % (self.i.plural_noun(material,user_amount),user_amount))
                
                #debuffs a region if the material used was a buffer
                if material in self.item_info["combatBuffs"].keys():
                    buffed_land = self.user_info[author]["home"] #get the land to be buffed, based on the creator's homeland
                    self.land_info[buffed_land]["DEFbuff"] -= (
                                    self.item_info["combatBuffs"][material] * 
                                    int(item_cost[material])*amount
                                    )
            if item not in self.user_info[author].keys():
                self.user_info[author][item] = 0
            self.user_info[author][item] = self.user_info[author][item] + amount #credits item to user
            self.data["user_info"] = self.user_info
            log.info("    Credited %s %s to %s" % (amount,self.i.plural_noun(item,amount),author))
            comment.reply("You have successfully created %s %s for %s %s!" % (
                                        amount,self.i.plural_noun(item,amount),
                                        count,self.i.plural_noun(material,count)
                                        ))
            log.info("    Sent completion message to %s " % author)
            
            #this part checks to see if the item created is a buff giving item like a wall
            if item in self.item_info["combatBuffs"].keys():
                buffed_land = self.user_info[author]["home"] #get the land to be buffed, based on the creator's homeland
                self.land_info[buffed_land]["DEFbuff"] += self.item_info["combatBuffs"][item] * amount #add the proper buff
        else:
            print "User not good for it."

    @failable
    def make_trade_offer(self,author,trade_info,comment):
        log.info("    User initiating trade: %s" % author)
        out_count = float(trade_info[0])
        log.info("    Number of items to be traded: %s" % out_count)
        out_item = self.i.singular_noun(trade_info[1])
        if not out_item:
            out_item = trade_info[1]
        log.info("    Type of item to be traded: %s " % out_item)
        in_count = float(trade_info[3])
        log.info("    Number of items to be traded for: %s" % in_count)
        in_item = self.i.singular_noun(trade_info[4])
        if not in_item:
            in_item = trade_info[4]
        log.info("    Type of item to be traded for: %s" % out_item)
        to_user = trade_info[6]
        log.info("    User to trade with: %s" % to_user)
        out_GFI = self.user_info[author][out_item]>=out_count
        log.info("    Initiating User is good for it: %s" % out_GFI)
        in_GFI = self.user_info[to_user][in_item]>=in_count
        log.info("    Receiving User is good for it: %s" % in_GFI)
        self.trade_number += 1
        log.info("    Trade #%s" % self.trade_number)
        if out_GFI and in_GFI:
            comment.reply("Sending trade offer to %s." % to_user)
            log.info("    Sending trade offer to %s." % to_user)
            
            #construct trade message
            trade_message = """
/u/%s has sent you the following trade offer:

    trade your %s %s for his %s %s

To accept this offer, reply to this message with 

    $$trade accept #%s

-----

Your current own %s %s

"""    %    (to_user, in_count, self.i.plural(in_item,in_count), out_count, 
            self.i.plural(out_item,out_count), self.trade_number,
            self.user_info[to_user][in_item], in_item)
       
            self.r.send_message(to_user,"Trade Offer From %s" % author.capitalize(),trade_message)
            self.active_trades[self.trade_number]=(author,trade_info,comment)
            return True
        else:
            comment.reply("One of you doesn't have enough resources to complete this trade!")
            log.info("    One of the parties can't fulfill the trade requirements.")
            return False

    @failable
    def accept_trade_offer(self,author,trade_num,comment):
        #author is the user who is accepting the trade
        #originator is the user who initiated the trade
        if author != self.active_trades[trade_num][1][6]:
            comment.reply("You are not the user this trade is intended for!")
            log.warning("%s tried to accept a trade that is not theirs: #%s" % (author,trade_num))
        if trade_num not in self.active_trades:
            comment.reply("Trade #%s is not an active trade!" % trade_num)
            log.warning("%s has tried to accept an invalid trade: %s" % (author,trade_num))
            return
        trade_data = self.active_trades[trade_num]
        originator = trade_data[0]
        trade_info = trade_data[1]
        trade_cmnt = trade_data[2]
        log.info("    User: %s" % author)
        in_count = float(trade_info[0])
        log.info("    Number of items to be received: %s" % in_count)
        in_item = self.i.singular_noun(trade_info[1])
        if not in_item:
            in_item = trade_info[1]
        log.info("    Type of item to be received: %s" % in_item)
        out_count = float(trade_info[3])
        log.info("    Number of items to be traded out: %s" % out_count)
        out_item = self.i.singular_noun(trade_info[4])
        if not out_item:
            out_item = trade_info[4]
        log.info("    Type of item to be traded out: %s" % out_item)
        #add the inbound items to the recipient's inventory
        try: 
            self.user_info[author][in_item] += in_count
        except KeyError: 
            self.user_info[author][in_item] = in_count    
        
        #this part checks to see if the item traded is a buff giving item like a wall
        if in_item in self.item_info["combatBuffs"].keys():
            #get the land to be buffed, based on the creator's homeland
            buffed_land = self.user_info[author]["home"] 
            
            #add the proper buff to the land
            self.land_info[buffed_land]["DEFbuff"] += self.item_info["combatBuffs"][in_item] * in_count 
            
        #add the outbound items to the initiator's inventory
        try: 
            self.user_info[originator][out_item] += out_count
        except KeyError: 
            self.user_info[originator][out_item] = out_count

        #this part checks to see if the item traded is a buff giving item like a wall
        if out_item in self.item_info["combatBuffs"].keys():
            #get the land to be buffed, based on the creator's homeland
            buffed_land = self.user_info[originator]["home"] 
            
            #add the proper buff to the land
            self.land_info[buffed_land]["DEFbuff"] += self.item_info["combatBuffs"][out_item] * out_count
            
        #subtract the outbound items from the users' inventories
        self.user_info[author][out_item] -= out_count
        if out_item in self.item_info["combatBuffs"].keys():
            buffed_land = self.user_info[author]["home"] 
            self.land_info[buffed_land]["DEFbuff"] -= self.item_info["combatBuffs"][out_item] * out_count
        self.user_info[originator][in_item] -= in_count
        if in_item in self.item_info["combatBuffs"].keys():
            buffed_land = self.user_info[originator]["home"] 
            self.land_info[buffed_land]["DEFbuff"] -= self.item_info["combatBuffs"][in_item] * out_count
        self.data["user_info"] = self.user_info
        trade_cmnt.reply("Trade completed!")

    @failable
    def add_item(self,resource,comment):
        name = resource[0]
        try:
            cost = loads(resource[1])
        except ValueError:
            comment.reply("JSON format incorrect. Read up on JSON [here](http://json.org/)\
                         and use [this](http://www.jsoneditoronline.org/) to do it easier.")
        if name not in self.item_info.keys():
            self.item_info[name] = cost
            self.data["item_info"] = self.item_info
            comment.reply("Added "+name+" to the item database for a cost of "+str(cost)+".")
        else:
            comment.reply("This is already an item!")
    
    @failable
    def register(self):
        thread = self.r.get_submission(submission_id = self.recruit_id,comment_sort = "new")
        cmnts = praw.helpers.flatten_tree(thread.comments)
        users = self.user_info.keys()
        for cmnt in cmnts:
            author = str(cmnt.author).lower()
            if author not in users:
                base = False #is the user actually setting their base here
                parts = cmnt.body.split("\n")
                try:
                    for part in parts:
                        if "$$" in part:
                            base = readTerritory(part)
                            if base not in self.lands:
                                base = "midnightmarsh"
                                cmnt.reply("No base set, defaulting to the [Midnight Marsh](/r/MidnightMarsh)")
                                log.warning("%s tried to set their base to a non-existent territory: %s" % (author,base))
                except ValueError:
                    base = "midnightmarsh"
                    #cmnt.reply("No base set, defaulting to the [Midnight Marsh](/r/MidnightMarsh)")
                    log.warning("%s messed up the registrationg command: %s" % (author,cmnt.body))
                if base:
                    print ("Adding new user %s to user_info with citizenship in %s!" % (author,base))
                    log.info("Adding new user %s to user_info with citizenship in %s!" % (author,base))
                    self.user_info[author]={"food": 0, "material": 0, "luxury": 0,
                                            "last_produced":0.0,"last_creation":0,
                                            "producing":"material","home":base}
                    cmnt.reply("You have now registered as a citizen in %s!\
                               By default, you are producing material goods." % base)
        self.data["user_info"] = self.user_info

    @failable
    def iterate(self):
        self.register()
        with open("EconomyInfo.json","w") as chroma_data:
            dump(self.data,chroma_data)
        while True:
            self.grab_commands()
            print "Updating JSON file"
            with open("EconomyInfo.json","w") as chroma_data:
                dump(self.data,chroma_data)
            log.info("User production: "+str(asctime()))
            print("User production")
            for user in self.user_info:
                self.produce(user)
                with open("EconomyInfo.json","w") as chroma_data:
                    dump(self.data,chroma_data)

if __name__ == "__main__":
    reddit = praw.Reddit("Chromeconomist Testing")
    reddit.login("Chromeconomist","BestEconomist")
    print reddit
    chroma_data = open("EconomyInfo.json","r")
    try:
        economist_info = load(chroma_data)
    except ValueError as e:
        print e
    bot = Bot(reddit,economist_info)
    bot.iterate()