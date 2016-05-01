a = list()
#a = [1, 2, 3]
a.append(1)
a.append(2)
a.append(3)
print a

for i in a:
	print i
	a.remove(i)

print a
