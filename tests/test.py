#!/usr/bin/python
import os
array=[]
with open(os.path.dirname(os.path.abspath(__file__))+'/conf.txt') as conf_file:
	for line in conf_file:
		array = line.split(',')
if int(array[0]) > 2 and int(array[1]) > 6 and int(array[2]) > 4 and int(array[3]) > 1 and  int(array[3]) > 5:
	with open(os.path.dirname(os.path.abspath(__file__))+'/output.txt') as output_file:
		for line in output_file:
			print line
else:
	with open(os.path.dirname(os.path.abspath(__file__))+'/output1.txt') as output_file:
		for line in output_file:
			print line
