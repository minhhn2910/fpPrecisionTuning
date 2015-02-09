#!/usr/bin/python
import os
array=[]
with open(os.path.dirname(os.path.abspath(__file__))+'/conf.txt') as conf_file:
	for line in conf_file:
		array = line.split(',')
if int(array[0]) > 2 and int(array[1]) > 3:	
	print "Hello World!"
