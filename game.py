from flask import Flask
import queue
import threading
import time
import pickle
import json
import random
from flask_socketio import SocketIO, emit
from chat_socket import socketio, log, users, user_lock
from flask import current_app
from threading import Lock , Thread

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

    def getPosition(self):
        return self.context["x"],self.context["y"]

    def move(self, dx,dy):
        self.context["x"] += dx
        self.context["y"] += dy

    def getId(self):
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
        self.height = 270
        self.obj_speed = 5

        self.queue = queue.Queue(maxsize = 50)
        self.start_time = 0
        #60 frames each second
        self.interval = 1/30
        self.actors = []#include pawns and objects
        self.updated_actor_ids = []
        self.lookup = [] #save the index of removed actors
        self.pawns = []

        self.isStarted = False
        #this is a dictionary, key:name, value:id
        self.players = {}
        self.room = None
        self.frameNo = 0
        self.lock = Lock()
        self.setFlag(False)

        self.thread = None
    

    ################### these are interfaces for being called outside game thread###########
    ###################so need to use the queue to deliver command##########################
    #interface for add a player
    def add_player(self, name):
        cmds = {"type": 'new-player',"id": 0,'name':name}
        self.enqueue_cmds(cmds)
    
    def remove_player(self, name):
        #the id here has no use but for preventing none
        cmds = {"type":'remove-player','name':name ,"id": 0} 
        self.enqueue_cmds(cmds)

    def setFlag(self, b):
        with self.lock:
            self.run_flag = b

    def is_run(self):
        fg = False
        with self.lock:
            fg = self.run_flag
        return fg
    
    def start(self, request):
        with self.lock:
            if(self.run_flag == False):
                #socketio.start_background_task(game_process, request)
                self.thread = Thread(target = Game.run, args= (self, request))
                self.thread.start()

    ################################called internally################################
    def out_of_screen(self,actor):
        x,y = actor.getPosition()
        if y > self.height or y < 0:
            return True
        if x < 0 or x > self.width:
            return True
        return False

    def has_player(self,name):
        if name in self.players:
            return True
        return False
    
    #stop the game and clear the memory
    def stop_run(self):
        self.__init__()

    #use some algorithms to generate new objects
    def simulate_new_obj(self):
        id = self.addNewActor('obj')
        actor = self.actors[id]
        x = random.uniform(0, self.width)
        y = random.uniform(0, self.height * 0.2)
        actor.setPosition(x, y)
        r = random.uniform(3, 8)
        actor.setRadius(r)
        
    #create some objects and move them automatically like ans Ai system
    #these objects are obstacles or enemies
    def simulate(self):
        objNum = len(self.actors)- len(self.pawns)-len(self.lookup)
        if(objNum > 3 and objNum < 10):
            t = random.randint(0, 1)
            if t > 0:
                self.simulate_new_obj()
        elif(objNum < 3):
            self.simulate_new_obj()

        #random move object
        player_ids = []
        for i in range(len(self.actors)):
            if(self.actors[i].getState() == 1):
                ac = self.actors[i]
                if(ac != None):
                    dx = random.uniform(0, 10)
                    dy = random.uniform(0,10)
                    if(ac.getType() == "obj"):
                        ac.move(0, self.obj_speed)
                        ac.move(dx ,dy)
                        if(self.out_of_screen(ac)):
                            self.removeActor(ac.getId())
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
        self.setFlag(True)
        #can't make sure if the thread run here after queue has been push something
        #self.queue = queue.Queue(maxsize = 50)#use clear to instead
        self.room = request["room"]
        print("game{0} ".format(self.room),"starts")
        while self.run_flag == True:
            start_time = time.perf_counter()
            self.updated_actor_ids = []
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

        print("game{0} ".format(self.room),"over")
            
    #process the commands sent from clients
    def process_cmds(self, cmds):
        id = cmds.get('id', None)
        name = cmds.get('name',None)
        if name == None or id == None:
            print("id or name is None")
            return
        self.updated_actor_ids = []
        #move 
        if(cmds['type'] == 'move'):
            self.actors[id].move(cmds['dx'],cmds['dy'])
            if self.out_of_screen(self.actors[id]):
                self.actors[id].move(-cmds['dx'],-cmds['dy'])
                
        elif(cmds['type'] == 'attack'):
            pass
        elif(cmds['type'] == 'new-player'):
            if(not self.has_player(name)):
                id = self.addNewActor('player')
                self.players[name] = id
                socketio.emit('join-game-success', {'msg':'success','id': id}, room = self.room)
                log("join-game-success")     
        elif(cmds['type'] == 'remove-player'):
            if(self.players.get(cmds['name']) != None):
                self.players.pop(cmds['name'], None)
                self.removeActor(cmds['id'])
                if(len(self.players) == 0):
                    self.stop_run()
            

        self.add_actor_to_update_list(id)
        return 
    
    #after update the states, send back to clients
    def send_states(self, request):
        arr = []
        #for i in range(len(self.updated_actor_ids)):
         #   arr.append(self.actors[self.updated_actor_ids[i]].context)
            
        #update scene states
        #json_string = json.dumps(arr)
        for i in range(len(self.actors)):
            #if self.actors[i] != None and self.actors[i].getState() == 1:
            if self.actors[i] != None: #if the actor die, still need to send
                arr.append(self.actors[i].context)
        json_string = json.dumps(arr)

        #emit states to clients
        socketio.emit('game', json_string, room = self.room)
        print("room:",self.room)
        print(json_string)