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
Move your car with the arrow keys. You will not be able to move out of your assigned lane. If you are the host, you will be in the
left lane and if you join the game you will be in the right lane. 
The game will go until a player gets at least 200 points. The screen will be cleared and a message is displayed telling the users who won. 

###Possible issues:
Sometimes due to the clock being off (as you could never create a perfect clock) it is possible for the scores to be off a bit due to latency in messages. To fix this issue, we decided that the host is in charge of the game score. They will send a message to the player that joined the game telling them who won the game and will send the appropriate scores. The scores most likely will not change but in case the networking connection is slow, the host is allowed to determine who wins the game and what their score should be.
For our game, this design made sense as the host determines the coin and obstacle position by choosing random values and sending the
information to their opponent. In a similar fashion, it makes sense that the host is in control of the absolute score for the
players. In our experience, this issue rarely occurs. If it was more prevalent we could change the design of our game to send more 
messages but we wanted to limit the amount of communication. Therefore, the host will only correct the score if there is a winner. 

TODO: add more description

###Exiting the game:
In any stage of the game the player can exit the game by clicking the exit button or the ESC key. 
If the connection was lost(if one player exits the game) both game windows will close and the game will terminate. 
