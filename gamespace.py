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

BOARD_WIDTH = 512
BOARD_HEIGHT = 512
# get the coins to travel on the road
# home screen/ pick a car
# specifying a host machine
# levels?/ multiple terrains
BLACK = (255, 255, 255)


class PowerUp(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.images = []
		self.player = self.gs.racer #this will be the racer
		self.counter = random.randrange(0,6) # starts at a random coin position
		for n in range(1, 7):
			imagename = "media/Coins/coin" + str(n) +".png"
			self.images.append(imagename)
		self.image = pygame.image.load(self.images[self.counter])
		self.rect = self.image.get_rect()
		self.centerx =  random.randrange(0,BOARD_WIDTH)
		self.centery=  random.randrange(0,BOARD_HEIGHT)
		#this all needs to be changed vvv
		#if (len(self.player.rect.collidelistall([self.rect])) != 0):
		#	print "hi" #if you use a while this creates a seemingly infinite loop
		#	self.centerx = random.randrange(400,BOARD_WIDTH)
		#	self.centery = random.randrange(400, BOARD_HEIGHT)
		self.rect.center = (self.centerx, self.centery)
	def tick(self):
		if self.counter > 5:
			self.counter=0
		self.image = pygame.image.load(self.images[self.counter])
		self.counter +=1

class Racer(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.crash = None 
		#maybe add a variable self.canMove = true then crash set to false?
		self.image = pygame.image.load("media/cars/blue.png")
		self.rect = self.image.get_rect()
		self.centerx = 200
		self.centery = 200
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
			#del self.gs.powerups[idx]
			#print self.gs.powerups[idx].centerx,self.gs.powerups[idx].centery
			#print self.centerx, self.centery
			del self.gs.powerups[idx]
			self.power +=1;
		for idx in self.rect.collidelistall(self.gs.obstacles):
			#print self.gs.powerups[idx].centerx,self.gs.powerups[idx].centery
			#print self.centerx, self.centery
			del self.gs.obstacles[idx]
			#add another
			self.gs.obstacles.append(Obstacle(self.gs))
			self.power -=1;
			
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
		if (self.rect.left < 0) or (self.rect.right > BOARD_WIDTH) or (self.rect.bottom > BOARD_HEIGHT) or (self.rect.top < 0):
			self.crash = Crash(self.gs)
			

class Crash(pygame.sprite.Sprite): #could change this to on crash, decrease the health
	def __init__(self,gs = None):
		self.gs = gs
		self.font = pygame.font.Font(None, 30)
		self.text = "You crashed!!"
		self.image = self.font.render(self.text,1,(0,255,0))
		self.rect = self.image.get_rect()
		self.rect.center = ((BOARD_HEIGHT / 2), (BOARD_WIDTH / 2))


class Score(pygame.sprite.Sprite): #display how many coins have been retrieved
	def __init__(self,gs = None):
		self.player = gs.racer
		self.gs = gs
		self.font = pygame.font.Font(None, 30)
		self.text = str(self.player.power)
		self.image = self.font.render(self.text,1,(0,255,0))
		self.rect = self.image.get_rect()
		self.rect.center = self.player.rect.center

	def tick(self):
		self.rect.center = self.player.rect.center 
		self.text = "Score: " + str(self.player.power)
		self.image = self.font.render(self.text,1,(0,255,0))

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
		#check if off the grid, if so add to player score
		self.centery += self.speed		
		self.rect.center = (self.centerx, self.centery)
	
	
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
		# 2) set up game objects
		self.clock = pygame.time.Clock()
		self.racer = Racer(self)
		self.showStartMenu=False
		self.showPlayGame= True
		self.showEndMenu=False
		self.showPauseMenu=False
		for c in range(0, 10):
			self.powerups.append(PowerUp(self))
	def main(self):
		if self.showStartMenu:
			self.startMenu()
		elif self.showPlayGame:
			self.playGame()
	
	def startMenu(self):
		pass
	def playGame(self):
	
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN :
				if event.key == pygame.K_ESCAPE:
					reactor.stop()		
				self.racer.move(event.key)
				print "key down"
				connections['data'].sendLine('key\t' + str(pygame.K_LEFT)) #event.key))

		# 6) send a tick to every game object
		self.racer.tick()
		self.racer2.tick()
		for p in self.powerups:
			p.tick()
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
		pygame.display.flip()

	def endMenu(self):
		pass
	def pauseMenu(self):
		pass


class PlayerConnection(LineReceiver):
	def connectionMade(self):
		print "connection made "
		self.setLineMode()
		connections['data'] = self
		self.gs = GameSpace()
		self.gs.racer2 = Racer(self.gs)
		lc = LoopingCall( self.gs.main )
		lc.start( 1 / 60)
	def lineReceived(self, line): # line received
		data = line.split('\t') # split to get what kind of signal we are getting
		print "line recieved, " , line
		if data[0] == 'key': #key input
			print "key recieved, ", data[1]
			if int(data[1]) == pygame.K_RIGHT:
				self.gs.racer2.move(int(data[1]))
			elif int(data[1]) == pygame.K_LEFT:
				self.gs.racer2.move(int(data[1]))
		elif data[0] == 'ready': # ready to play
			print "ready"
			self.gs.bothLaunch()
		elif data[0] == 'end': # someone lost
			self.gs.winner = True
	def sendLine(self, line):
		print "sending line"
		line += '\r\n'
		connections['data'].transport.write(line)
	def connectionLost(self, reason):
		reactor.stop()
		print reason
class PlayerConnectionFactory( ReconnectingClientFactory ):
	def buildProtocol( self, address ):
		return PlayerConnection()
		self.score = Score(self) #to update the score	
	
		#self.powerup = PowerUp(self,self.racer)#pass in racer to compare locations
		for c in range(0, 10):
			self.powerups.append(PowerUp(self))

		self.obstacles = [] #for avoiding things
		for i in range (0,10):
			self.obstacles.append(Obstacle(self))

		# 3) start game loop
		while 1:
			# 4) clock tick regulation (framerate)
			self.clock.tick(60)
			# 5) this is where you would handle user inputs...
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					sys.exit(0) #end the game
				elif event.type == pygame.KEYDOWN :
					self.racer.move(event.key)
			# 6) send a tick to every game object
			self.racer.tick()
			self.score.tick()
			for p in self.powerups:
				p.tick()
			for o in self.obstacles:
				o.tick()
			# 7) and finally, display the game objects
		
			self.screen.fill(self.black)
			speed += 2
			bg.scroll(speed, orientation)
			speed -= 2
			bg.draw(screen)
			for p in self.powerups:
				self.screen.blit(p.image, p.rect)
			self.screen.blit(self.racer.image, self.racer.rect)
			self.screen.blit(self.score.image, self.score)
		        for o in self.obstacles:
				self.screen.blit(o.image, o.rect)
			if(self.racer.crash != None):
				self.screen.blit(self.racer.crash.image, self.racer.crash)	
			pygame.display.flip()


if __name__ == '__main__':
	isHost = False
	connections = {}
	if sys.argv[1] == 'host': # star host connection
		isHost = True
		reactor.listenTCP(int(sys.argv[2]), PlayerConnectionFactory())
		reactor.run()
	
	elif sys.argv[1] == 'join': # join the other connection
		reactor.connectTCP('localhost', int(sys.argv[2]), PlayerConnectionFactory())
		reactor.run()

	else:
		print "Incorrect usage: python gamespace.py [host/join] [post number]\n"
		sys.exit(1)



