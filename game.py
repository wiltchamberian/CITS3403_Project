from flask import Flask
import queue
import threading
import time
import pickle
import json
import random
from flask_socketio import SocketIO, emit
from chat_socket import socketio, log
from flask import current_app


#this is a role in the game, can be a pawn or an object
#pawn is the role controled by the player, object is obstale or enemies
#all of them are actors
class Actor:
    def __init__(self, type = 0, id = 0):
        self.context = {
            "x": 0,
            "y": 0,
            "radius": 5,
            "id": id,
            "type": type,
            "color": 'green',
            "state": 1 #0:dead, 1:alive
        }
        if (type == 'obj'):
            self.context["color"] = 'red'
    
    def getState(self):
        return self.context["state"]
    def setState(self, st):
        self.context["state"] = st

    def setRadius(self,r):
        self.context["radius"] = r

    def setPosition(self,x,y):
        self.context["x"] = x
        self.context["y"] = y

    def move(self, dx,dy):
        self.context["x"] += dx
        self.context["y"] += dy

    def getId(self,id):
        return self.context["id"]
    
    def setId(self, id):
        self.context["id"] = id
    
    def setType(self, type):
        self.context["type"] = type

    def getType(self):
        return self.context["type"]

    def collide_with(self, actor):
        return False
# 创建一个对象

#this is for process game logic
class Game: 
    def __init__(self):
        self.width = 480
        self.height = 720
        self.obj_speed = 20

        self.queue = queue.Queue(maxsize = 50)
        self.start_time = 0
        self.interval = 3 #60 frames each second
        self.actors = []#include pawns and objects
        self.actor_update_ids = []
        self.lookup = [] #save the index of removed actors
        self.pawns = []

        self.isStarted = False
        self.players = set()
        self.room = None
        self.frameNo = 0

    #use some algorithms to generate new objects
    def simulate_new_obj(self):
        id = self.addNewActor('obj')
        actor = self.actors[id]
        x = random.uniform(0, self.width)
        y = random.uniform(0, self.height * 0.2)
        actor.setPosition(x, y)
        r = random.uniform(3, 8)
        actor.setRadius(r)
        
    #interface for add a player
    def add_player(self, name):
        self.players.add(name)
        cmds = {"type": 'new-player',"id": 0}
        self.enqueue_cmds(cmds)
        log('add_player_finish')

    def has_player(self,name):
        if name in self.players:
            return True
        return False
        
    #create some objects and move them automatically like ans Ai system
    #these objects are obstacles or enemies
    def simulate(self):
        objNum = len(self.actors)- len(self.pawns)
        if(objNum > 3 and objNum < 10):
            t = random.randint(0, 1)
            if t > 0:
                self.simulate_new_obj()
        elif(objNum < 3):
            self.simulate_new_obj()

        #random move object
        player_ids = []
        for i in range(len(self.actors)):
            ac = self.actors[i]
            if(ac != None):
                dx = random.uniform(0, 10)
                dy = random.uniform(0,10)
                if(ac.getType() == "obj"):
                    ac.move(0, self.obj_speed)
                    ac.move(dx ,dy)
                else:
                    player_ids.append(i)

        #check collision
        for i in range(len(player_ids)):
            for j in range(len(self.actors)):
                actor = self.actors[j]
                if(actor.getState()==1 and actor.getType()=="obj"):
                    player = self.actors[player_ids[i]]
                    collide = player.collide_with(actor)
                    if(collide):
                        self.removeActor(player.getId())
                        self.removeActor(actor.getId())
                    else:
                        pass
        
    def removeActor(self, id):
        self.actors[id].setState(0)
        self.lookup.append(id)
        self.updated_actor_ids.append(id)

    def addNewActor(self, type):
        id = 0
        actor = None
        if(len(self.lookup)==0):
            id = len(self.actors)
            actor = Actor(type, len(self.actors))
            self.actors.append(actor)
        else:
            id = self.lookup[-1]
            actor = Actor(type, self.lookup[-1])
            self.actors[self.lookup[-1]] = actor 
            self.lookup.pop()
        if (type =='player'):
            self.pawns.append(actor)
        return id
    
    def add_actor_to_update_list(self, id):
        self.updated_actor_ids.append(id)

    def enqueue_cmds(self, cmds):
        self.queue.put(cmds)

    #main function, entry
    def run(self, request):
        self.room = request["room"]
        while True:
            start_time = time.perf_counter()
            self.actor_update_ids = []
            while(not self.queue.empty()):
                cmds = self.queue.get()
                self.process_cmds(cmds)

            self.simulate()
            self.send_states(request)
            
            self.frameNo += 1
            
            end_time = time.perf_counter()
            print("tick:{0}".format(end_time))
            dtime = end_time - start_time
            if(dtime < self.interval):
                time.sleep(self.interval - dtime)
            
    #process the commands sent from clients
    def process_cmds(self, cmds):
        id = cmds['id']
        self.updated_actor_ids = []
        #move 
        if(cmds['type'] == 'move'):
            self.actors[id].move(cmds['dx'],cmds['dy'])
        elif(cmds['type'] == 'attack'):
            pass
        elif(cmds['type'] == 'new-player'):
            id = self.addNewActor('player')
            socketio.emit('join-game-success', {'msg':'success','id': id}, room = self.room)
            log("join-game-success")

        self.add_actor_to_update_list(id)
        return 
    
    #after update the states, send back to clients
    def send_states(self, request):
        arr = []
        for i in range(len(self.actor_update_ids)):
            arr.append(self.actors[self.actor_update_ids[i]].context)
            
        #update scene states
        json_string = json.dumps(arr)

        #emit states to clients
        socketio.emit('game', json_string, room = self.room)
        print("emit")