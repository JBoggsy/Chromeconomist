#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      James Boggs
#
# Created:     10/04/2014
# Copyright:   (c) James Boggs 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import time
import datetime
import praw
import json
import string
from inflect import *

class bot(object):
    def __init__ (self, reddit,EconomistInfo):
        self.log = open("ChromeconomistRunLog.txt","w+")
        self.lands = ["Midnight Marsh","Cote d'Azure","Oraistedearg"]
        bot.log(self,"Lands: "+self.lands.__str__())
        self.landInfo = EconomistInfo["LandInfo"]
        self.userInfo = EconomistInfo["UserInfo"]
        self.itemInfo = EconomistInfo["ItemInfo"]
        self.data = {"LandInfo":self.landInfo,"UserInfo":self.userInfo,"ItemInfo":self.itemInfo}
        bot.log(self,"JSON info loaded")
        self.r = reddit
        bot.log(self,"Connected to Reddit")
        self.i = engine()
        self.trade_number = 0
        self.active_trades = dict()
        self.recruit_id = '2bfmr6'
        self.mods = ['eliminioa','danster21','zthousand','twilight_octavia','cdos93','dalek1234']
        bot.iterate(self)

    def parseLand(self,land):
        self.curSub = self.r.get_subreddit(self.landStats['srname'])
        print self.curSub
        bot.log(self,"Current sub: "+self.curSub.__str__())
        comments = self.r.get_comments(self.curSub,limit=None)
        bot.log(self,"  Comment generator:" +comments.__str__())
        BotCommands = [] #bot command will be a list [author(str),action,resource]
        placeholder_ID = self.landInfo[land]["placeholder_ID"]
        for comment in comments:
            if comment.id == placeholder_ID:
                bot.log(self,"    Arrived at placeholder!\n")
                print ("Arrived at placeholder!")
                ref_id = comment.id
                break
            if ("#" in comment.body.lower()):
                if len(BotCommands) == 0: #stores the comment id of the first new comment for reference
                    ref_id = comment.id
                    bot.log(self,"  Updated placeholder id to "+str(ref_id)+" @ "+str(time.asctime(time.gmtime(comment.created))))
                    self.landInfo[land]["placeholder_ID"] = ref_id
                    self.data["LandInfo"] = self.landInfo
                if str(comment.author).lower() not in self.userInfo:
                    print ("User "+str(comment.author).lower()+" not found")
                    bot.log(self,"  User "+str(comment.author).lower()+" not found, alerting")
                    comment.reply('User not found! Please register for the Chromeconomist bot [here](http://redd.it/'+self.recruit_id+')')
                bot.log(self,"  New command found: "+comment.__str__())
                rawCmd = comment.body.splitlines()
                for line in rawCmd:
                    if '#' in line:
                        cmdLine = line.strip('#')
                        break
                cmdParts = cmdLine.split()
                cmdTime = comment.created
                bot.log(self,"    Command time: "+str(time.asctime(time.gmtime(comment.created))))
                author = str(comment.author).lower()
                action = cmdParts[0].lower()
                action = action.strip(string.punctuation)
                resource = cmdParts[1:]
                command = [author,action,resource,cmdTime,comment]
                bot.log(self,"    Parsed command as "+command.__str__())
                BotCommands.append(command)
        bot.parseCommands(self,BotCommands)

    def parsePMs(self,PMCommands):
        BotCommands = []
        for PM in PMCommands:
            author = str(PM.author)
            author = author.lower()
            if author not in self.userInfo:
                print ("User "+author+" not found")
                bot.log(self,"  User "+author+" not found, alerting")
                PM.reply('User not found! Please register for the Chromeconomist bot [here](http://redd.it/'+self.recruit_id+')')
            cmdParts = PM.body.split()
            bot.log(self,"Command parts: "+str(cmdParts))
            cmdTime = PM.created
            bot.log(self,"    Command time: "+str(time.asctime(time.gmtime(PM.created))))
            action = cmdParts[0].lower()
            action = action.strip(string.punctuation)
            resource = cmdParts[1:]
            command = [author,action,resource,cmdTime,PM]
            bot.log(self,"    Parsed command as "+command.__str__())
            BotCommands.append(command)
        bot.parseCommands(self,BotCommands)

    def parseCommands(self,BotCommands):
         for command in BotCommands:
            author = command[0]
            action = command[1]
            resource = command[2]
            cmdTime = command[3]
            comment = command[4]
            #This is the part which reads prodcuce commands. DONE as of 6/6/2014
            if action == 'produce':
                bot.change_production(self,author,resource[0].strip(string.punctuation),comment)
                print (author +" changed their resource to "+resource[0]+"\n")
                bot.log(self,author +" changed their resource to "+resource[0])
            #This is the part which reads creation commands. DONE as of 15/6/2014
            elif action == 'create':
                print ("User "+author+" is creating "+str(resource[0])+" "+resource[1]+"s")
                bot.log(self,"User "+author+" is creating "+str(resource[0])+" "+self.i.plural_noun(resource[1],resource[0]))
                self.userInfo[author]["last_creation"] = cmdTime
                bot.create(self,author,int(resource[0]),resource[1],comment)
            #this reads balance display commands, and replies to the user with their account summary. DONE as of 7/1/2014
            elif action == 'balance':
                messageStr = "Hello "+author+", your account balance stands as follows:\n\n-----\n\n"
                for item in self.userInfo[author]:
                    if item in ["last_produced","last_creation","producing","home"]:
                        continue
                    messageStr = messageStr + "   "+self.i.plural_noun(item,self.userInfo[author][item])+": "+str(self.userInfo[author][item])+'\n\n'
                time_to_production = datetime.timedelta(seconds=(self.userInfo[author]["last_produced"]+300-time.time()))
                messageStr = messageStr + "-----\n\nYou will produce "+self.userInfo[author]["producing"]+" in "+str(time_to_production)+"."
                comment.reply(messageStr)
            #this reads trading commands. A brief preface, becaus this command is a bit trickier than the rest DONE as of 7/15/2014:
            #trade command is "trade [count] [item] for [count] [item] with [user]" therefore:
            #resource[0] = the number of items the user is trading away
            #resource[1] = the type of item the user is trading away
            #resource[3] = the number of items the user is trading for
            #resource[4] = the type of item the user is trading for
            #resource[6] = the player the user is trading with
            elif action == 'trade':
                if resource[0] == 'accept':
                    trade_num = int(resource[1].strip("#"))
                    print (author+" has accepted trade offer #"+str(trade_num))
                    bot.log(self,author+" has accepted trade offer #"+str(trade_num))
                    bot.accept_trade_offer(self,author,trade_num)
                else:
                    print (author+" is trying to trade "+str(resource[0])+" "+self.i.plural(resource[1],resource[0])+" for "+str(resource[3])+" "+self.i.plural(resource[4],resource[3])+" with "+resource[6])
                    bot.log(self,author+" is trying to trade "+str(resource[0])+" "+self.i.plural(resource[1],resource[0])+" for "+str(resource[3])+" "+self.i.plural(resource[4],resource[3])+" with "+resource[6])
                    bot.make_trade_offer(self,author,resource[:7],comment)
            #this allows me to add items. DONE as of 7/24/14
            #command resources:
            #resource[0] = the name of the new item
            #resource[1] = cost in format {"item":cost,"item":cost,etc}
            #resource[2] = pre-reqs in format ("item","item",etc)
            elif action =='add' and str(author)=='eliminioa':
                print ('Adding '+resource[0])
                bot.add_item(self,resource,comment)
            else:
                print ('"'+action+'" command is not ready yet!')

    #this function parses a "produce" command, altering what the user produces every iteration
    def change_production(self,author,resource,comment):
        material_keywords = ["wood","lumber","stone","stones","brick","bricks","material","materials"]
        luxury_keyowrds = ["gold","diamonds","pearls","ivory","silk","spice","spices","pearl","chocolate","luxury","luxuries"]
        if resource in material_keywords:
            resource = "material"
        elif resource in luxury_keyowrds:
            resource = "luxury"
        else:
            resource = 'food'
        self.userInfo[author]["producing"] = resource
        self.data["UserInfo"] = self.userInfo
        comment.reply("You are now producing "+resource)


    #this function credits a user with produced goods every iteration
    def produce(self,author):
        if time.time() < self.userInfo[author]["last_produced"]+60:
            bot.log(self,"  User "+author+" has already produced something this hour.")
            return False
        self.userInfo[author]["last_produced"] = time.time()
        resource = self.userInfo[author]["producing"]
        bot.log(self,"    Producing "+resource+" for "+author)
        bonus = self.landInfo[self.userInfo[author]["home"]]["bonus"]
        bot.log(self,"    Land bonus: "+bonus)
        penalty = self.landInfo[self.userInfo[author]["home"]]['penalty']
        bot.log(self,"    Land penalty: "+penalty)
        #this part determines whether the amount a user receives is influenced by their homeland
        if bonus == resource:
            bonusNum = 1.5
        elif penalty == resource:
            bonusNum = .5
        else:
            bonusNum = 1
        for bonus_item in self.itemInfo["craftBuffs"]: # this part needs work. Needs to apply production bonus to the right resource(s)
            if bonus_item in self.userInfo[author]:
                BICount = self.userInfo[author][bonus_item]#amount of the bonus item user has
                bonusNum += self.itemInfo["craftBuffs"][bonus_item] * BICount
                bot.log(self,"    "+author+" has "+str(BICount)+" "+bonus_item+"s, which grants them "+str(self.itemInfo["craftBuffs"][bonus_item] * BICount)+" more production!")
        bot.log(self,"    Bonus multiplier: "+bonusNum.__str__())
        bounty = 1*bonusNum
        bot.log(self,"    Produced resources: "+bounty.__str__()+" "+resource)
        self.userInfo[author][resource] += bounty
        self.data["UserInfo"] = self.userInfo
        return True

    #as titled, this function parses a create command, credits the user with their items, and subtracts the appropriate ammount of resources
    def create(self,author,amount,item,comment):
        if self.i.singular_noun(item):
            item = self.i.singular_noun(item)
        bot.log(self,"    Item to be created: "+item)
        bot.log(self,"    Amount to be created: "+str(amount))
        try:
            itemCost = self.itemInfo[item]
        except KeyError:
            comment.reply("The item you're trying to make isn't a thing yet. Sorry.")
            return None
        bot.log(self,"    Item cost: "+str(itemCost))
        good_for_it = True #can the user pay for it?
        
        #actually make the user pay for it
        for material in itemCost:
            count = float(itemCost[material])*amount
            bot.log(self,"    "+item+" requires "+str(count)+' '+self.i.plural_noun(material,count))
            if material in self.userInfo[author].keys():
                userAmount =self.userInfo[author][material]
            else:
                userAmount = 0
            bot.log(self,"    User has "+str(userAmount)+" "+self.i.plural_noun(material,userAmount))
            if userAmount < count:
                messageStr ="You do not have enough "+material+" to make "+str(amount)+" "+item+"."
                comment.reply(messageStr)
                bot.log(self,"    Informed user that they do not have sufficient resources.")
                good_for_it = False
        if good_for_it:
            for material in itemCost:
                self.userInfo[author][material] -= int(itemCost[material])*amount #takes away cost for each item before crediting
                bot.log(self,"    User's new amount of "+self.i.plural_noun(material,userAmount)+" is "+str(userAmount))
                
                #debuffs a region if the material used was a buffer
                if material in self.itemInfo['combatBuffs'].keys():
                    buffedLand = self.userInfo[author]['home'] #get the land to be buffed, based on the creator's homeland
                    self.landInfo[buffedLand]['DEFbuff'] -= self.itemInfo['combatBuffs'][material] * int(itemCost[material])*amount #add the proper buff to the land
                
        if good_for_it:
            if item not in self.userInfo[author].keys():
                self.userInfo[author][item] = 0
            self.userInfo[author][item] = self.userInfo[author][item] + amount #credits item to user
            self.data["UserInfo"] = self.userInfo
            bot.log(self,"    Credited "+str(amount)+" "+self.i.plural_noun(item,amount)+" to "+author)
            comment.reply("You have successfully created "+str(amount)+" "+self.i.plural_noun(item,amount)+" for "+str(count)+" "+self.i.plural_noun(material,count)+"!")
            print (author + " successfully created "+str(amount)+" "+self.i.plural_noun(item,amount)+" for "+str(count)+" "+self.i.plural_noun(material,count)+"!")
            bot.log(self,"    Sent completion message to "+author)
            
            #this part checks to see if the item created is a buff giving item like a wall
            if item in self.itemInfo['combatBuffs'].keys():
                buffedLand = self.userInfo[author]['home'] #get the land to be buffed, based on the creator's homeland
                self.landInfo[buffedLand]['DEFbuff'] += self.itemInfo['combatBuffs'][item] * amount #add the proper buff to the land
        else:
            print "User not good for it."

    def make_trade_offer(self,author,trade_info,comment):
        bot.log(self,"    User initiating trade: "+author)
        outCount = float(trade_info[0])
        bot.log(self,"    Number of items to be traded: "+str(outCount))
        outItem = self.i.singular_noun(trade_info[1])
        if not outItem:
            outItem = trade_info[1]
        bot.log(self,"    Type of item to be traded: "+outItem)
        inCount = float(trade_info[3])
        bot.log(self,"    Number of items to be traded for: "+str(inCount))
        inItem = self.i.singular_noun(trade_info[4])
        if not inItem:
            inItem = trade_info[4]
        bot.log(self,"    Type of item to be traded for: "+outItem)
        toUser = trade_info[6]
        bot.log(self,"    User to trade with: "+toUser)
        outGFI = self.userInfo[author][outItem]>=outCount
        bot.log(self,"    Initiating User is good for it: "+str(outGFI))
        inGFI = self.userInfo[toUser][inItem]>=inCount
        bot.log(self,"    Receiving User is good for it: "+str(inGFI))
        self.trade_number += 1
        bot.log(self,"    Trade #"+str(self.trade_number))
        if outGFI and inGFI:
            comment.reply('Sending trade offer to '+toUser+".")
            bot.log(self,'    Sending trade off to '+toUser+'.')
            trade_message = '/u/'+author+' has sent you the following trade offer:\n\n     trade your '+str(inCount)+' '+self.i.plural(inItem,inCount)+' for his '+str(outCount)+' '+self.i.plural(outItem,outCount)+'\n\nYour current balance is:\n\n'
            for item in self.userInfo[author]:
                    if item in ["last_produced","last_creation","producing","home"]:
                        continue
                    trade_message += "   "+self.i.plural_noun(item,self.userInfo[author][item])+": "+str(self.userInfo[author][item])+'\n\n'
            trade_message += '-----\n\nTo accept this offer, reply to this message with\n\n>trade accept #'+str(self.trade_number)
            self.r.send_message(toUser,'Trade Offer From '+author.capitalize(),trade_message)
            self.active_trades[self.trade_number]=(author,trade_info,comment)
            return True
        else:
            comment.reply('One of you doesn\'nt have enough resources to complete this trade!')
            bot.log(self,"    One of the parties can't fulfill the trade requirements.")
            return False

    def accept_trade_offer(self,author,trade_num):
        #author is the user who is accepting the trade
        #tAuthor is the user who initiated the trade
        trade_data = self.active_trades[trade_num]
        tAuthor = trade_data[0]
        trade_info = trade_data[1]
        tComment = trade_data[2]
        bot.log(self,"    User: "+author)
        inCount = float(trade_info[0])
        bot.log(self,"    Number of items to be received: "+str(inCount))
        inItem = self.i.singular_noun(trade_info[1])
        if not inItem:
            inItem = trade_info[1]
        bot.log(self,"    Type of item to be received: "+inItem)
        outCount = float(trade_info[3])
        bot.log(self,"    Number of items to be traded out: "+str(outCount))
        outItem = self.i.singular_noun(trade_info[4])
        if not outItem:
            outItem = trade_info[4]
        bot.log(self,"    Type of item to be traded out: "+outItem)
        #add the inbound items to the recipient's inventory
        try: self.userInfo[author][inItem] += inCount
        except: self.userInfo[author][inItem] = inCount    
        
        #this part checks to see if the item traded is a buff giving item like a wall
        if inItem in self.itemInfo['combatBuffs'].keys():
            #get the land to be buffed, based on the creator's homeland
            buffedLand = self.userInfo[author]['home'] 
            
            #add the proper buff to the land
            self.landInfo[buffedLand]['DEFbuff'] += self.itemInfo['combatBuffs'][inItem] * inCount 
            
        #add the outbound items to the initiator's inventory
        try: self.userInfo[tAuthor][outItem] += outCount
        except: self.userInfo[tAuthor][outItem] = outCount

        #this part checks to see if the item traded is a buff giving item like a wall
        if outItem in self.itemInfo['combatBuffs'].keys():
            #get the land to be buffed, based on the creator's homeland
            buffedLand = self.userInfo[tAuthor]['home'] 
            
            #add the proper buff to the land
            self.landInfo[buffedLand]['DEFbuff'] += self.itemInfo['combatBuffs'][outItem] * outCount
            
        #subtract the outbound items from the users' inventories
        self.userInfo[author][outItem] -= outCount
        if outItem in self.itemInfo['combatBuffs'].keys():
            buffedLand = self.userInfo[author]['home'] 
            self.landInfo[buffedLand]['DEFbuff'] -= self.itemInfo['combatBuffs'][outItem] * outCount
        self.userInfo[tAuthor][inItem] -= inCount
        if inItem in self.itemInfo['combatBuffs'].keys():
            buffedLand = self.userInfo[tAuthor]['home'] 
            self.landInfo[buffedLand]['DEFbuff'] -= self.itemInfo['combatBuffs'][inItem] * outCount
        self.data["UserInfo"] = self.userInfo
        tComment.reply('Trade completed!')

    def add_item(self,resource,comment):
        name = resource[0]
        try:
            cost = json.loads(resource[1])
        except:
            comment.reply("JSON format incorrect. Read up on JSON [here](http://json.org/) and use [this](http://www.jsoneditoronline.org/) to do it easier.")
        if name not in self.itemInfo.keys():
            self.itemInfo[name] = cost
            self.data["ItemInfo"] = self.itemInfo
            comment.reply("Added "+name+" to the item database for a cost of "+str(cost)+".")
        else:
            comment.reply("This is already an item!")

    def register(self):
        thread = self.r.get_submission(submission_id = self.recruit_id,comment_sort = 'new')
        cmnts = thread.comments
        recruit_links = self.userInfo.keys()
        for cmnt in cmnts:
            if str(cmnt.author).lower() not in recruit_links:
                parts = cmnt.body.split()
                try:
                    for part in parts:
                        if '#' in part:
                            raw_base = part
                    base = raw_base.strip('#')
                    base = base.replace('-',' ')
                    base = base.replace('_',' ')
                    base = base.replace('/r/','')
                    base = base.replace('r/','')
                    base = base.lower()
                    if base not in self.landInfo.keys():
                        base = 'midnight marsh'
                        cmnt.reply('No base set, defaulting to the [Midnight Marsh](/r/MidnightMarsh)')
                except ValueError:
                    base = 'midnight marsh'
                    cmnt.reply('No base set, defaulting to the [Midnight Marsh](/r/MidnightMarsh)')
                print ("Adding new user "+str(cmnt.author).lower()+" to userInfo with citizenship in "+base+"!")
                bot.log(self,"Adding new user "+str(cmnt.author).lower()+" to userInfo with citizenship in "+base+"!")
                self.userInfo[str(cmnt.author).lower()]={"food": 0, "material": 0, "luxury": 0,"last_produced":0.0,"last_creation":0,"producing":'material',"home":base}
                cmnt.reply('You have now registered as a citizen in '+base+'! By default, you are producing material goods.')
        self.data["UserInfo"] = self.userInfo

    def iterate(self):
        bot.register(self)
        chromaData = open("EconomyInfo.json",'w')
        json.dump(self.data,chromaData)
        chromaData.close()
        while True:
            for land in self.lands:
                bot.log(self,land+': '+(time.asctime()))
                self.landStats = self.landInfo[land]
                bot.parseLand(self,land)
                chromaData = open("EconomyInfo.json",'w')
                json.dump(self.data,chromaData)
                chromaData.close()
                self.log.flush()
            print "Reading PMs"
            newPMs = self.r.get_unread(True,True)
            PMCommands = []
            for PM in newPMs:
                if not PM.was_comment:
                    PMCommands.append(PM)
                    PM.mark_as_read()
            bot.log(self,"PMs: "+str(time.asctime()))
            bot.parsePMs(self,PMCommands)
            print "Updating JSON file"
            chromaData = open("EconomyInfo.json",'w')
            json.dump(self.data,chromaData)
            chromaData.close()
            bot.log(self,"User production: "+str(time.asctime()))
            print("User production")
            for user in self.userInfo:
                bot.produce(self,user)
                chromaData = open("EconomyInfo.json",'w')
                json.dump(self.data,chromaData)
                chromaData.close()
                self.log.flush()
            print "waiting 60 secs"
            time.sleep(60)
##        #except:
##            chromaData = open("EconomyInfo.json",'w')
##            json.dump(self.data,chromaData)
##            chromaData.close()
##            self.log.flush()
##            bot.iterate(self)

    def log(self,text):
        self.log.write(text+'\n')
        self.log.flush()

if __name__ == '__main__':
    reddit = praw.Reddit('Chromeconomist Testing')
    reddit.login('Chromeconomist','BestEconomist')
    print reddit
    chromaData = open("EconomyInfo.json",'r') #open('/home/ec2-user/Chroma.json','r'),open('/home/ec2-user/ChromaUsers.json','r')
    try:
        EconomistInfo = json.load(chromaData)
    except ValueError as e:
        print e
    bot(reddit,EconomistInfo)