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
# get the coins to travel on the road
# home screen/ pick a car
# specifying a host machine
# levels?/ multiple terrains
GREEN = (0, 255, 0)
WHITE = (255,255,255)


class PowerUp(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.images = []
		#self.player = self.gs.racer #this will be the racer
		self.counter = random.randrange(0,6) # starts at a random coin position
		for n in range(1, 7):
			imagename = "media/Coins/coin" + str(n) +".png"
			self.images.append(imagename)
		self.image = pygame.image.load(self.images[self.counter])
		self.rect = self.image.get_rect()
		self.centerx =  random.randrange(0,BOARD_WIDTH)
		self.centery=  random.randrange(-500,25)
		self.rect.center = (self.centerx, self.centery)
		self.speed = 2

	def tick(self):
		if self.counter > 5: 
			self.counter=0
		self.image = pygame.image.load(self.images[self.counter])
		self.counter +=1
		self.centery += self.speed		
		self.rect.center = (self.centerx, self.centery)

class Racer(pygame.sprite.Sprite):
	def __init__(self,  x, y, color, gs=None):
		print "making racer init: ", x, " ", y
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.crash = None 
		#maybe add a variable self.canMove = true then crash set to false?
		
		imagename = "media/cars/" + color +".png"
		self.image = pygame.image.load(imagename)
		self.rect = self.image.get_rect()
		self.centerx = x
		self.centery = y

		self.rect.center = (self.centerx, self.centery)
		# keep original image to limit resize errors
		self.orig_image = self.image
		self.rect = self.image.get_rect()
		self.power = 0
		
	
	def tick(self):
		self.rect = self.image.get_rect()
		self.rect.center = (self.centerx, self.centery)
		self.checkCrash()
		for idx in self.rect.collidelistall(self.gs.powerups):
			del self.gs.powerups[idx]
			if self.gs.isHost:
				self.gs.powerups.append(PowerUp(self.gs))
				to_send = list()
				to_send.append({'x': self.gs.powerups[-1].centerx, 'y': self.gs.powerups[-1].centery})
				#pickle the list
				#now need to send this instance so the other one adds it
				newPower = pickle.dumps(to_send)
				connections['data'].sendLine('add1_P\t' + newPower) 
			self.power +=15;
	
		for idx in self.rect.collidelistall(self.gs.obstacles):
			del self.gs.obstacles[idx] #delete off screen no matter what
			if self.gs.isHost:
				self.gs.obstacles.append(Obstacle(self.gs))
				to_send = list()
				to_send.append({'x': self.gs.obstacles[-1].centerx, 'y': self.gs.obstacles[-1].centery})
				newObs = pickle.dumps(to_send)
				connections['data'].sendLine('add1_O\t' + newObs) 
			self.power -=10;
			
	def move(self, keycode):
		if keycode == pygame.K_DOWN :
			self.centery +=15
		elif keycode == pygame.K_UP :
			self.centery -=15
		elif keycode == pygame.K_RIGHT:
			self.centerx +=15
		elif keycode == pygame.K_LEFT:
			self.centerx -=15

	def checkCrash(self): #check if the car goes off the screen
		if (self.rect.left < 0):
			self.power -= 5
			self.centerx = 50
		elif (self.rect.right > BOARD_WIDTH):
			self.power -= 5
			self.centerx = BOARD_WIDTH - 50
		elif (self.rect.bottom > BOARD_HEIGHT):
			self.power -= 5
			self.centery = BOARD_HEIGHT - 100
		elif (self.rect.top < 0):
			self.power -= 5
			self.centery = 100
		self.rect.center = (self.centerx, self.centery)
			
class Win(pygame.sprite.Sprite): #could change this to on crash, decrease the health
	def __init__(self,gs = None):
		self.gs = gs
		#remove all obstacles and power ups from the gamespace
		self.gs.obstacles[:] = []
		self.gs.powerups[:] = []

		self.font = pygame.font.Font(None, 100)
		#TODO fix this bug - might be off
		if (self.gs.isWinner == 1 and self.gs.isHost == True) or (self.gs.isWinner == 2 and self.gs.isHost == False):
			self.win = 1 
		elif (self.gs.isWinner == 1 and self.gs.isHost == False) or (self.gs.isWinner == 2 and self.gs.isHost == True):
			self.win = 2
		self.text = "Player " + str(self.win) + " wins!"
		self.image = self.font.render(self.text,1,GREEN)
		self.rect = self.image.get_rect()
		self.rect.center = ((BOARD_HEIGHT / 2), (BOARD_WIDTH / 2) - 200)

class Score(pygame.sprite.Sprite): #display how many coins have been retrieved
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

class Obstacle(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.image = pygame.image.load("media/danger2.png")
		self.rect = self.image.get_rect()
		self.centerx = random.randrange(0,BOARD_WIDTH)
		self.centery = random.randrange(-1000,-10) #to start off the screen
		self.orig_image = self.image
		self.rect = self.image.get_rect()
		self.rect.center = (self.centerx, self.centery)
		self.speed = 1
		
	
	def tick(self):
		#check if off the grid, delete and create?
		#if self.centery > BOARD_HEIGHT: 
		#	self.centerx = random.randrange(0,BOARD_WIDTH)
		#	self.centery = random.randrange(-1000,-10) #to start off the screen
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
		self.speed=0
		self.winner = False
		self.ready= False
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
			#self.obstaclePos.append(self.obstacles[i].centerx)
			#self.obstaclePos.append(self.obstacles[i].centery)
			self.obstaclePos.append({ 'x': self.obstacles[i].centerx, 'y': self.obstacles[i].centery})
			print  'y',self.obstacles[i].centery, 'x', self.obstacles[i].centerx


		obsStr = pickle.dumps(self.obstaclePos)
		connections['data'].sendLine('obstacle\t' + obsStr) 
		#return self.obstacles

	def makePowerUp(self):
		for c in range(0, 10):
			self.powerups.append(PowerUp(self))
			self.powerUpPos.append({ 'x': self.powerups[c].centerx, 'y': self.powerups[c].centery})
			print 'y', self.powerups[c].centery, 'x', self.powerups[c].centerx 
		powerStr = pickle.dumps(self.powerUpPos)
		connections['data'].sendLine('powerup\t' + powerStr) 
		#send them  

	def checkObstacles(self):
		for i in self.obstacles:
			if i.centery > BOARD_HEIGHT: 
				del i #does this work?
				#remove and add a new one, send to other if not host
				if self.isHost:
					self.obstacles.append(Obstacle(self))
					to_send = list()
					to_send.append({'x': self.obstacles[-1].centerx, 'y': self.obstacles[-1].centery})
					newObs = pickle.dumps(to_send)
					connections['data'].sendLine('add1_O\t' + newObs) 

	def checkPower(self):
		for i in self.powerups:
			if i.centery > BOARD_HEIGHT: 
				del i #does this work?
				#remove and add a new one, send to other if not host
				if self.isHost:
					self.powerups.append(PowerUp(self))
					to_send = list()
					to_send.append({'x': self.powerups[-1].centerx, 'y': self.powerups[-1].centery})
					#pickle the list
					#now need to send this instance so the other one adds it
					newPower = pickle.dumps(to_send)
					connections['data'].sendLine('add1_P\t' + newPower) 

	def makeRacer(self, x, y, color):
		print "making racer: ", x," ", y
		racer = Racer(x, y,color, self)
		return racer

	def makeScore(self):
		self.score1 = Score(self,self.racer) #to update the score
		self.score2 = Score(self,self.racer2) #bad idea to pass in but I want 2 distinct objects

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
		for c in colors:
			car= StartMenuRacer(xpos, ypos, c)
			cars.append(car)
			xpos +=100
			if counter ==3:
				ypos+=200
				xpos = 100
			self.screen.blit(car.carimage, car.rect)
			counter+=1
		#white = (255,255,255)
		#green = (0, 255, 0)

		mx, my = pygame.mouse.get_pos()
		for c in cars:
			if c.rect.collidepoint(mx,my):
				#white = (255,255,255)
				pygame.draw.rect(self.screen, WHITE, (c.x-40,c.y-78,80,155), 5)
			
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

		if self.racerselected:
			pygame.draw.rect(self.screen, GREEN, (self.selected.x-40,self.selected.y-78,80,155), 5)
			self.screen.blit(w.waitexitimage, w.rect)

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
			self.obstacles[:] = [] #- make sure that these are cleared - change to a better way
			self.powerups[:] = [] #could check in player if isWinner != none then don't add
		else:
			self.checkWin()	
		pygame.display.flip()
		print "lenght of coins: ", len(self.powerups)
		print "lenght of obstacles: ", len(self.obstacles)
		self.checkObstacles()
		self.checkPower()

	def checkWin(self):
		#check win
		if(self.racer.power > 200):
			self.isWinner = 1
			self.win = Win(self) 
		elif(self.racer2.power > 200):
			self.isWinner = 2
			self.win = Win(self)

	def endMenu(self):
		pass
	def pauseMenu(self):
		pass


class PlayerConnection(LineReceiver):
	def __init__(self, isHost):
		self.isHost= isHost
	def connectionMade(self):
		print "connection made "
		self.setLineMode()
		connections['data'] = self
		self.gs = GameSpace()
		self.gs.isHost = self.isHost
	
		print "is Host?", self.gs.isHost
		#need a way to check to see whether or not to start the loops

		lc = LoopingCall( self.gs.main )
		lc.start( 1 / 60)

	def lineReceived(self, line): # line received
		data = line.split('\t') # split to get what kind of signal we are getting
		print "line recieved, " , line
		if data[0] == 'key': #key input
			print "key recieved, ", data[1]
			if int(data[1]) == pygame.K_RIGHT or int(data[1]) == pygame.K_LEFT or int(data[1]) == pygame.K_UP or int(data[1]) == pygame.K_DOWN:
				self.gs.racer2.move(int(data[1]))
			#elif int(data[1]) == pygame.K_LEFT:
			#	self.gs.racer2.move(int(data[1]))
		elif data[0] == 'obstacle':
			my_array = pickle.loads(data[1])
			idx = 0
			for i in my_array:
				print i #{ x : y}
				self.gs.obstacles.append(Obstacle(self.gs))
				self.gs.obstacles[idx].centerx = i['x']
				self.gs.obstacles[idx].centery = i['y']
				self.gs.obstacles[idx].rect.center = (i['x'], i['y'])
				idx += 1 #increase the index for the obstacles


		elif data[0] == 'powerup':
			my_array = pickle.loads(data[1])
			idx = 0
			for i in my_array:
				print i #{ x : y}
				self.gs.powerups.append(PowerUp(self.gs))
				self.gs.powerups[idx].centerx = i['x']
				self.gs.powerups[idx].centery = i['y']
				self.gs.powerups[idx].rect.center = (i['x'], i['y'])
				idx += 1 #increase the index for the obstacle

		elif data[0] == 'add1_P':
			print "adding powerup"
			powerUp_data = pickle.loads(data[1])
			powerUp_data = powerUp_data[0] #just a list of 1 element, set this var to the actual dict
			self.gs.powerups.append(PowerUp(self.gs))
			self.gs.powerups[-1].centerx = powerUp_data['x']
			self.gs.powerups[-1].centery = powerUp_data['y']
			self.gs.powerups[-1].rect.center = (powerUp_data['x'], powerUp_data['y'])

		elif data[0] == 'add1_O':
			print "adding obstacle"
			obstacle_data = pickle.loads(data[1])
			obstacle_data = obstacle_data[0] #just a list of 1 element, set this var to the actual dict
			self.gs.obstacles.append(Obstacle(self.gs))
			self.gs.obstacles[-1].centerx = obstacle_data['x']
			self.gs.obstacles[-1].centery = obstacle_data['y']
			self.gs.obstacles[-1].rect.center = (obstacle_data['x'], obstacle_data['y'])

			#self.gs.obstacles = pickle.loads(data[1]) #set obstacles on both
		elif data[0] == 'ready': # ready to play
			print "ready"
			self.gs.bothLaunch()
		elif data[0] == 'end': # someone lost
			self.gs.winner = True
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
	if sys.argv[1] == 'host': # star host connection
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


