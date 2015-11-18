#!/usr/bin/env python
import os
import sys
import time

def main (num_vars, value):
	f = open('config_file.txt', 'w')
	out_string = '%s,'%(value)*num_vars + '\n'
	f.write(out_string);
if __name__ == '__main__':
	arguments = sys.argv[1:]
	if len(arguments)!=2:
		print "usage ./write_config.py numvars value"
	main(int(arguments[0]),int(arguments[1]))

