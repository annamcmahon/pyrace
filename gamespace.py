#Anna McMahon and Katie Quinn
import sys
import os
import pygame
from pygame.locals import *
import math
import random
import parallax
from twisted.internet.protocol import Factory, Protocol, ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
import cPickle as pickle

BOARD_WIDTH = 512
BOARD_HEIGHT = 512
GREEN = (0, 255, 0)
WHITE = (255,255,255)
COIN_BONUS = 15
OBSTACLE_COST = 10
OFF_SCREEN = 20
TO_MOVE = 15
TO_WIN = 200


class PowerUp(pygame.sprite.Sprite): #the coin class 
#these coins will "fall" down the top of the screen and the player can get coins to increase their score
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.images = [] #to be able to iterate through coin images, appearance of spinning
		self.counter = random.randrange(0,6) # starts at a random coin position
		for n in range(1, 7):
			imagename = "media/Coins/coin" + str(n) +".png"
			self.images.append(imagename)
		self.image = pygame.image.load(self.images[self.counter])
		self.rect = self.image.get_rect()
		self.centerx =  random.randrange(0,BOARD_WIDTH) #initially position it randomly at the top/off screen
		self.centery=  random.randrange(-500,25)
		self.rect.center = (self.centerx, self.centery)
		self.speed = 2 #this will be used to increase the position, allows the coin to move

	def tick(self):
		#determine what image to display
		if self.counter > 5:  
			self.counter=0
		self.image = pygame.image.load(self.images[self.counter])
		self.counter +=1
		self.centery += self.speed		
		self.rect.center = (self.centerx, self.centery)

class Racer(pygame.sprite.Sprite): #this is the player class
	def __init__(self,  x, y, color, gs=None):
		#print "making racer init: ", x, " ", y
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs		
		imagename = "media/cars/" + color +".png" #pick the right color car
		self.image = pygame.image.load(imagename)
		self.rect = self.image.get_rect()
		self.centerx = x #we pass in the x and y coordinates to create the cars in the right places based on if host
		self.centery = y 
		self.rect.center = (self.centerx, self.centery)
		# keep original image to limit resize errors
		self.orig_image = self.image
		self.rect = self.image.get_rect()
		self.power = 0
		
	
	def tick(self):
		self.rect = self.image.get_rect()
		self.rect.center = (self.centerx, self.centery)
		self.checkCrash() #deduct points if they moved "off" track
		for idx in self.rect.collidelistall(self.gs.powerups): #check to see if they got any coins
			del self.gs.powerups[idx] #delete the coin from both screens
			#if you are the host, create a new coin and send this to the other game
			if self.gs.isHost: 
				self.gs.powerups.append(PowerUp(self.gs)) #create new power up and get coordinates
				to_send = list()
				to_send.append({'x': self.gs.powerups[-1].centerx, 'y': self.gs.powerups[-1].centery})
				newPower = pickle.dumps(to_send) #pickle/compress the list to send over, easy way of converting lists/strings
				connections['data'].sendLine('add1_P\t' + newPower) #send message
			self.power += COIN_BONUS; #update score
	
		for idx in self.rect.collidelistall(self.gs.obstacles): #check to see if they hit an obstacle
			del self.gs.obstacles[idx] #delete off screen 
			if self.gs.isHost: #similar to above
				self.gs.obstacles.append(Obstacle(self.gs))
				to_send = list()
				to_send.append({'x': self.gs.obstacles[-1].centerx, 'y': self.gs.obstacles[-1].centery})
				newObs = pickle.dumps(to_send)
				connections['data'].sendLine('add1_O\t' + newObs) 
			self.power -= OBSTACLE_COST; #update score
			
	def move(self, keycode): #move according to keycode
		if keycode == pygame.K_DOWN :
			self.centery += TO_MOVE
		elif keycode == pygame.K_UP :
			self.centery -= TO_MOVE
		elif keycode == pygame.K_RIGHT:
			self.centerx += TO_MOVE
		elif keycode == pygame.K_LEFT:
			self.centerx -= TO_MOVE

		#check if overlapped - close not quite there yet
		#if self.gs.isHost:
		#	if self.gs.racer.rect.right > self.gs.racer2.rect.left:
		#		self.gs.racer.centerx -= 15
		#else:
		#	if self.gs.racer.rect.left < self.gs.racer2.rect.right:
		#		self.gs.racer.centerx += 15
		#self.gs.racer.rect.center = (self.gs.racer.centerx, self.gs.racer.centery)
		#self.gs.racer2.rect.center = (self.gs.racer2.centerx, self.gs.racer2.centery)

	def checkCrash(self): #check if the car goes off the screen
		if (self.rect.left < 0):
			self.power -= OFF_SCREEN
			self.centerx = 50
		elif (self.rect.right > BOARD_WIDTH):
			self.power -= OFF_SCREEN
			self.centerx = BOARD_WIDTH - 50
		elif (self.rect.bottom > BOARD_HEIGHT):
			self.power -= OFF_SCREEN
			self.centery = BOARD_HEIGHT - 100
		elif (self.rect.top < 0):
			self.power -= OFF_SCREEN
			self.centery = 100
		self.rect.center = (self.centerx, self.centery)
			
class Win(pygame.sprite.Sprite): #Indicate on the screen who won
	def __init__(self,gs = None):
		self.gs = gs
		#remove all obstacles and power ups from the gamespace
		self.gs.obstacles[:] = []
		self.gs.powerups[:] = []

		self.font = pygame.font.Font(None, 100)
		#TODO check this:
		if (self.gs.isWinner == 1 and self.gs.isHost == True) or (self.gs.isWinner == 2 and self.gs.isHost == False):
			self.win = 1 
		elif (self.gs.isWinner == 1 and self.gs.isHost == False) or (self.gs.isWinner == 2 and self.gs.isHost == True):
			self.win = 2
		self.text = "Player " + str(self.win) + " wins!"
		self.image = self.font.render(self.text,1,GREEN)
		self.rect = self.image.get_rect()
		self.rect.center = ((BOARD_HEIGHT / 2), (BOARD_WIDTH / 2) - 200)

class Score(pygame.sprite.Sprite): #display each player's score on their cars
	def __init__(self,gs = None , racer = None):
		self.player = racer
		self.gs = gs
		self.font = pygame.font.Font(None, 30)
		self.text = "Score: " + str(self.player.power)
		self.image = self.font.render(self.text,1,WHITE)
		self.rect = self.image.get_rect()
		self.rect.center = self.player.rect.center

	def tick(self):
		self.rect.center = self.player.rect.center 
		self.text = "Score: " + str(self.player.power)
		self.image = self.font.render(self.text,1,WHITE)

class Obstacle(pygame.sprite.Sprite): #obstacle objects
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.image = pygame.image.load("media/danger2.png") #load image
		self.rect = self.image.get_rect()
		self.centerx = random.randrange(0,BOARD_WIDTH)
		self.centery = random.randrange(-1000,-10) #to start off the screen random position
		self.orig_image = self.image
		self.rect = self.image.get_rect()
		self.rect.center = (self.centerx, self.centery)
		self.speed = 1 #speed of obstacles - slower than coins
		
	
	def tick(self):
		#increase center y to move the obstacles
		self.centery += self.speed		
		self.rect.center = (self.centerx, self.centery)

	
class StartMenuRacer(pygame.sprite.Sprite):
	def __init__(self,  x, y, color, gs=None):
		self.color = color
		carstr = "media/cars/" + color +".png"
 		self.carimage = pygame.image.load(carstr)
		self.carimage = pygame.transform.scale(self.carimage, (75,150))
		self.rect = self.carimage.get_rect()
		self.x = x
		self.y=y
		self.rect.center = (x, y)	
class waiting(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.waitexitimage  = pygame.image.load("media/texts/waiting.png")	
		self.rect= self.waitexitimage.get_rect()
		self.rect.center= (BOARD_WIDTH/2, BOARD_HEIGHT-7 )
		
		#draw three circles
	def tick(self):
		pass


class GameSpace:
	def __init__(self):
		# 1) basic initialization
		pygame.init()
		self.size = self.width, self.height = BOARD_WIDTH, BOARD_HEIGHT
		self.black = 0, 0, 0
		self.screen = pygame.display.set_mode(self.size)
		self.screen = pygame.display.set_mode((512, 512), pygame.DOUBLEBUF)
		self.bg = parallax.ParallaxSurface((512, 512), pygame.RLEACCEL)
		self.bg.add('media/tunnel_road.jpg', 1)
		self.orientation = 'vertical'
		self.speed = 0
		self.winner = False
		#self.ready = False
		self.powerups = []
		self.obstacles = [] #for avoiding things

		self.racerselected = False
		self.otherracerselected= False

		self.obstaclePos = [] #for the positions
		self.powerUpPos = [] 
		self.clock = pygame.time.Clock()
		
		self.showStartMenu=True
		self.showPlayGame= False
		self.showEndMenu=False
		self.showPauseMenu=False

		self.isWinner = None

	def makeObstacles(self): #only called if host
		for i in range (0,10):
			self.obstacles.append(Obstacle(self))
			self.obstaclePos.append({ 'x': self.obstacles[i].centerx, 'y': self.obstacles[i].centery})
			#print  'y',self.obstacles[i].centery, 'x', self.obstacles[i].centerx

		obsStr = pickle.dumps(self.obstaclePos)
		connections['data'].sendLine('obstacle\t' + obsStr) #send to other game

	def makePowerUp(self): #make power ups if host
		for c in range(0, 10):
			self.powerups.append(PowerUp(self))
			self.powerUpPos.append({ 'x': self.powerups[c].centerx, 'y': self.powerups[c].centery})
			#print 'y', self.powerups[c].centery, 'x', self.powerups[c].centerx 

		powerStr = pickle.dumps(self.powerUpPos)
		connections['data'].sendLine('powerup\t' + powerStr)  #send them  to other tgame

	def checkObstacles(self): #check to see if obstacles need to be replaced
		for i in self.obstacles:
			if i.centery > BOARD_HEIGHT: 
				self.obstacles.remove(i) #remove the one that is too far off the screen
				#remove and add a new one, send to other if not host
				if self.isHost:
					self.obstacles.append(Obstacle(self))
					to_send = list()
					to_send.append({'x': self.obstacles[-1].centerx, 'y': self.obstacles[-1].centery})
					newObs = pickle.dumps(to_send)
					connections['data'].sendLine('add1_O\t' + newObs) #send to join

	def checkPower(self):
		for i in self.powerups:
			if i.centery > BOARD_HEIGHT: 
				self.powerups.remove(i) 
				#remove and add a new one, send to other if not host
				if self.isHost:
					self.powerups.append(PowerUp(self))
					to_send = list()
					to_send.append({'x': self.powerups[-1].centerx, 'y': self.powerups[-1].centery})
					newPower = pickle.dumps(to_send)
					connections['data'].sendLine('add1_P\t' + newPower) 

	def makeRacer(self, x, y, color): #making the players
		print "making racer: ", x," ", y
		racer = Racer(x, y,color, self)
		return racer

	def makeScore(self):
		self.score1 = Score(self,self.racer) #to update the score
		self.score2 = Score(self,self.racer2) #pass in racer to associate score with racer

	def main(self):
		if self.showStartMenu:
			self.startMenu()
		elif self.showPlayGame:
			self.playGame()

	def startMenu(self):
		self.screen.fill(self.black)
		w= waiting()
		welcometext  = pygame.image.load("media/texts/welcome.png")	
		rect= welcometext.get_rect()
		rect.center= (BOARD_WIDTH/2, 50 )
		self.screen.blit(welcometext, rect)

		choosecartext = pygame.image.load("media/texts/choosecar.png")	
		rect= choosecartext.get_rect()
		rect.center= (BOARD_WIDTH/2, 100 )
		self.screen.blit(choosecartext, rect)
		xpos= 100
		ypos= 200
		counter =0	
		colors = ["blue", "green", "darkblue","lightgreen", "orange", "pink", "seafoam", "yellow"]	
		cars = []
		#used to make all of the "StartMenuRacer" cars that are on the start up page
		for c in colors:
			car= StartMenuRacer(xpos, ypos, c)
			cars.append(car)
			xpos +=100
			if counter ==3:
				ypos+=200
				xpos = 100
			self.screen.blit(car.carimage, car.rect)
			counter+=1
	
		#highlighting functionality: draw a box around the current car
		mx, my = pygame.mouse.get_pos()
		for c in cars:
			if c.rect.collidepoint(mx,my):
				pygame.draw.rect(self.screen, WHITE, (c.x-40,c.y-78,80,155), 5)
		#handle the click events: highlight car and send car selection data to player 2
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN :
				if event.key == pygame.K_ESCAPE:
					reactor.stop()		
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mx, my = pygame.mouse.get_pos()	
				for c in cars:
					if c.rect.collidepoint(mx,my):
						self.racerselected = True
						self.selected = c
						self.p1color = c.color
						connections['data'].sendLine('racerselected\t' + c.color) 
						pygame.draw.rect(self.screen, GREEN, (c.x-40,c.y-78,80,155), 5)
		#if you have selected your racer but the other player has not, display message
		if self.racerselected:
			pygame.draw.rect(self.screen, GREEN, (self.selected.x-40,self.selected.y-78,80,155), 5)
			self.screen.blit(w.waitexitimage, w.rect)
		#continue to game play mode of the game
		if self.racerselected and self.otherracerselected:
			if self.isHost:
				self.racer = self.makeRacer(200, 400, self.p1color)
				self.racer2= self.makeRacer(400, 400, self.p2color)
				self.makeObstacles()
				self.makePowerUp()#make the power ups and obstacles if the host 

			else:
				self.racer = self.makeRacer(400, 400, self.p1color)
				self.racer2= self.makeRacer(200,400, self.p2color)
			self.makeScore() #make the scores for the racers
			self.showPlayGame =True
			self.showStartMenu = False

		pygame.display.flip()	
	#play the game, this state is entered once both players have selected a car
	def playGame(self):
	
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN :
				if event.key == pygame.K_ESCAPE:
					reactor.stop()		
				self.racer.move(event.key)
				print "key down"
				connections['data'].sendLine('key\t' + str(event.key)) #event.key))
			elif event.type == pygame.QUIT: #added to check if clicked the 'x' key
				reactor.stop() 

		# 6) send a tick to every game object
		self.racer.tick()
		self.racer2.tick()
		for p in self.powerups:
			p.tick()
		for o in self.obstacles:
			o.tick()
		self.score1.tick()
		self.score2.tick()

		
		# 7) and finally, display the game objects
		self.screen.fill(self.black)
		self.speed += 2
		#set up the parallax object to simulate the scrolling affect
		self.bg.scroll(self.speed, self.orientation)
		self.speed -= 2
		self.bg.draw(self.screen)
		for p in self.powerups:
			self.screen.blit(p.image, p.rect)
		self.screen.blit(self.racer.image, self.racer.rect)
		self.screen.blit(self.racer2.image, self.racer2.rect)
		self.screen.blit(self.score1.image, self.score1)
		self.screen.blit(self.score2.image, self.score2)
		for o in self.obstacles:
			self.screen.blit(o.image, o.rect)
		if(self.isWinner != None):
			self.screen.blit(self.win.image, self.win)
			self.obstacles[:] = [] #- make sure that these are cleared 
			self.powerups[:] = [] 
		else:
			self.checkWin()	
		pygame.display.flip()
		#print "lenght of coins: ", len(self.powerups)
		#print "lenght of obstacles: ", len(self.obstacles)
		self.checkObstacles() #check obstacles and powerups if on screen
		self.checkPower()

	def checkWin(self):
		#check win
		if(self.racer.power > TO_WIN):
			self.isWinner = 1
			self.win = Win(self) 
		elif(self.racer2.power > TO_WIN):
			self.isWinner = 2
			self.win = Win(self)


class PlayerConnection(LineReceiver):
	def __init__(self, isHost):
		self.isHost= isHost
	def connectionMade(self):
		print "connection made "
		self.setLineMode()
		connections['data'] = self
		self.gs = GameSpace()
		self.gs.isHost = self.isHost	
		#print "is Host?", self.gs.isHost
		lc = LoopingCall( self.gs.main )
		lc.start( 1 / 60)

	def lineReceived(self, line): # line received
		data = line.split('\t') # split to get what kind of signal we are getting
		print "line recieved, " , line
		if data[0] == 'key': #key input
			print "key recieved, ", data[1]
			if int(data[1]) == pygame.K_RIGHT or int(data[1]) == pygame.K_LEFT or int(data[1]) == pygame.K_UP or int(data[1]) == pygame.K_DOWN:
				self.gs.racer2.move(int(data[1]))

		elif data[0] == 'obstacle': #create all the obstacles
			my_array = pickle.loads(data[1]) #make the string into an array again
			idx = 0
			for i in my_array:
				#print i 
				self.gs.obstacles.append(Obstacle(self.gs)) #creates a random, updates position
				self.gs.obstacles[idx].centerx = i['x']
				self.gs.obstacles[idx].centery = i['y']
				self.gs.obstacles[idx].rect.center = (i['x'], i['y'])
				idx += 1 #increase the index for the obstacles

		elif data[0] == 'powerup':
			my_array = pickle.loads(data[1]) #string -> array
			idx = 0
			for i in my_array:
				#print i 
				self.gs.powerups.append(PowerUp(self.gs))
				self.gs.powerups[idx].centerx = i['x']
				self.gs.powerups[idx].centery = i['y']
				self.gs.powerups[idx].rect.center = (i['x'], i['y'])
				idx += 1 #increase the index for the obstacle

		elif data[0] == 'add1_P':
			#print "adding powerup"
			powerUp_data = pickle.loads(data[1])
			powerUp_data = powerUp_data[0] #just a list of 1 element, set this var to the actual dict
			self.gs.powerups.append(PowerUp(self.gs))
			self.gs.powerups[-1].centerx = powerUp_data['x']
			self.gs.powerups[-1].centery = powerUp_data['y']
			self.gs.powerups[-1].rect.center = (powerUp_data['x'], powerUp_data['y'])

		elif data[0] == 'add1_O':
			#print "adding obstacle"
			obstacle_data = pickle.loads(data[1])
			obstacle_data = obstacle_data[0] #just a list of 1 element, set this var to the actual dict
			self.gs.obstacles.append(Obstacle(self.gs))
			self.gs.obstacles[-1].centerx = obstacle_data['x']
			self.gs.obstacles[-1].centery = obstacle_data['y']
			self.gs.obstacles[-1].rect.center = (obstacle_data['x'], obstacle_data['y'])

		elif data[0]=='racerselected':
			print "color: ", data[1]
			self.gs.p2color = data[1]
			self.gs.otherracerselected = True
			
	def sendLine(self, line):
		print "sending line"
		line += '\r\n'
		connections['data'].transport.write(line)
	def connectionLost(self, reason):
		reactor.stop()
		print reason
class PlayerConnectionFactory( ReconnectingClientFactory ):
	def __init__(self, isHost):
		self.isHost= isHost
	def buildProtocol( self, address ):
		return PlayerConnection(self.isHost)
		
	
if __name__ == '__main__':
	isHost = False
	connections = {}
	if sys.argv[1] == 'host': # start host connection
		isHost = True
		reactor.listenTCP(int(sys.argv[2]), PlayerConnectionFactory(isHost))
		reactor.run()
	
	elif sys.argv[1] == 'join': # join the other connection
		isHost = False
		reactor.connectTCP('localhost', int(sys.argv[2]), PlayerConnectionFactory(isHost))
		reactor.run()

	else:
		print "Incorrect usage: python gamespace.py [host/join] [post number]\n"
		sys.exit(1)


