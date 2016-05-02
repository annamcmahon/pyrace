# pyrace
###python racing game 
Anna McMahon & Katie Quinn
CSE 30332: Programming Paradigms
Pygame + Twisted Project

###Game Description
	2 out of 2 users recommend this game! Available on localhost now! 
	This is a fun racing game in which two users pick up coins and avoid obstacles.
	The object of the game is to get 200 points before your opponenent

###To run the game:
1. One player must first run -> python gamespace.py host 'port number'.
	* ex: python gamespace.py host 9001
2. Then the second payer must run -> python gamespace.py join 'same port number'.
	* ex: python gamespace.py join 9001
* Make sure both players are running gamespace.py on the same machine. We have specified the machine as 'localhost'.
* Note, game play gui will show up until both players have done 'gamespace.py host/join 'port number'' 

###To play the game:
Choose your car color. When both players have chosen, the game will begin.
Avoid the obstacles (!) and try to collect the coins to earn points.
Trying to go off the screen to avoid/collect anything will result in a loss of points.
Move your car with the arrow keys.
The game will go until a player gets over 200 points. The screen will be cleared and a message is displayed telling the users who won. 
TODO: Add more description

###Exiting the game:
	In any stage of the game the player can exit the game by clicking the exit button or the ESC key. 
	If the connection was lost(if one player exits the game) both game windows will close and the game will terminate. 
