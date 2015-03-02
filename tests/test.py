#!/usr/bin/python
import os
import sys
def main(argv):
	array=[]
	if (len(argv)>0):
		int_precision = int(argv[0])
	else:
		int_precision = 10
	with open(os.path.dirname(os.path.abspath(__file__))+'/conf.txt') as conf_file:
		for line in conf_file:
			array = line.split(',')
			break
	#ran1 = random.randint(2,5)
	#ran2 = random.randint(6,10)
	if int(array[0]) > int_precision and int(array[1]) > int_precision and int(array[2]) > int_precision and int(array[3]) > int_precision and  int(array[4]) > int_precision :
		with open(os.path.dirname(os.path.abspath(__file__))+'/output.txt') as output_file:
			for line in output_file:
				print line
	else:
		with open(os.path.dirname(os.path.abspath(__file__))+'/output1.txt') as output_file:
			for line in output_file:
				print line
	
if __name__ == "__main__":
   main(sys.argv[1:])
