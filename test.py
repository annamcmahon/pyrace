# -*- coding: utf-8 -*-

#    Copyright (C) , 2012 Åke Forslund (ake.forslund@gmail.com)
#
#    Permission to use, copy, modify, and/or distribute this software for any
#    purpose with or without fee is hereby granted, provided that the above
#    copyright notice and this permission notice appear in all copies.
#
#    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#


import os, sys
import pygame
from pygame.locals import *

sys.path.append ("../")
import parallax

pygame.init()
screen = pygame.display.set_mode((512, 512), pygame.DOUBLEBUF)
pygame.display.set_caption('Parallax-test')
pygame.mouse.set_visible(0)

bg = parallax.ParallaxSurface((512, 512), pygame.RLEACCEL)
bg.add('media/tunnel_road.jpg', 1)
#bg.add('media/road/left.png', 5)
#bg.add('media/road/right.png', 2)

run = True
speed = 0
t_ref = 0
while run:
	speed += 2
#	for event in pygame.event.get():
#		if event.type == QUIT:
#			run = False
#		if event.type == KEYDOWN and event.key == K_RIGHT:
#			speed += 10
#		if event.type == KEYUP and event.key == K_RIGHT:
#			speed -= 10
#        if event.type == KEYDOWN and event.key == K_LEFT:
#			speed -= 10
#        if event.type == KEYUP and event.key == K_LEFT:
#			speed += 10
#		if event.type == KEYDOWN and event.key == K_UP:
#			orientation = 'vertical'
#		if event.type == KEYDOWN and event.key == K_DOWN:
#			orientation = 'horizontal'
	orientation = 'vertical'
	bg.scroll(speed, orientation)
	speed -= 2
	t = pygame.time.get_ticks()
	if (t - t_ref) > 60:
		bg.draw(screen)
		pygame.display.flip()


