import sys
import os
import pygame
from pygame.locals import *
import math
import random

BOARD_WIDTH = 500
BOARD_HEIGHT = 500

class PowerUp(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.images = []
		self.counter = random.randrange(0,6) # starts at a random coin position
		for n in range(1, 7):
			imagename = "media/Coins/coin" + str(n) +".png"
			self.images.append(imagename)
		self.image = pygame.image.load(self.images[self.counter])
		self.rect = self.image.get_rect()
		self.centerx =  random.randrange(0,BOARD_WIDTH)
		self.centery=  random.randrange(0,BOARD_HEIGHT)
		self.rect.center = (self.centerx, self.centery)
#		self.control= 0
	def tick(self):
#		self.control +=1;
#		if self.control%2==0:
		if self.counter > 5:
			self.counter=0
		self.image = pygame.image.load(self.images[self.counter])
		self.counter +=1

class Obstacle(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pass
	def tick(self):
		pass

class Racer(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.image = pygame.image.load("media/cars/blue.png")
		self.rect = self.image.get_rect()
		self.centerx = 200
		self.centery = 200
		self.rect.center = (self.centerx, self.centery)
		# keep original image to limit resize errors
		self.orig_image = self.image
		self.tofire = False
		self.rect = self.image.get_rect()
		self.rect.center = (self.centerx, self.centery)
		self.power = 0
	
	def tick(self):
		self.rect = self.image.get_rect()
		self.rect.center = (self.centerx, self.centery)
		for idx in self.rect.collidelistall(self.gs.powerups):
			del self.gs.powerups[idx]
			self.power +=1;
	def move(self, keycode):
		if keycode == pygame.K_DOWN :
			self.centery +=15
		elif keycode == pygame.K_UP :
			self.centery -=15
		elif keycode == pygame.K_RIGHT:
			self.centerx +=15
		elif keycode == pygame.K_LEFT:
			self.centerx -=15

class GameSpace:
	def main(self):
		# 1) basic initialization
		pygame.init()
		self.size = self.width, self.height = BOARD_WIDTH, BOARD_HEIGHT
		self.black = 0, 0, 0
		self.screen = pygame.display.set_mode(self.size)
		self.powerups = []
		# 2) set up game objects
		self.clock = pygame.time.Clock()
		self.racer = Racer(self)
		
		#self.powerup = PowerUp(self)
		for c in range(0, 10):
			self.powerups.append(PowerUp(self))
		# 3) start game loop
		while 1:
			# 4) clock tick regulation (framerate)
			self.clock.tick(60)
			# 5) this is where you would handle user inputs...
			for event in pygame.event.get():
				if event.type == pygame.KEYDOWN :
					self.racer.move(event.key)
			# 6) send a tick to every game object
			self.racer.tick()
			for p in self.powerups:
				p.tick()
			# 7) and finally, display the game objects
			self.screen.fill(self.black)
			self.screen.blit(self.racer.image, self.racer.rect)
			#self.screen.blit(self.powerup.image, self.powerup.rect)
			for p in self.powerups:
				self.screen.blit(p.image, p.rect)
			
			pygame.display.flip()



if __name__ == '__main__':
	gs = GameSpace()
	gs.main()

