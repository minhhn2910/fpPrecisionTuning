#!/usr/bin/python
import sys
import random

def random_search(conf_file, program):
	original_array = read_conf(conf_file)
	for loop in range(len(original_array)):
		precision_array = list(original_array)
		permutation_array = get_permutation(len(original_array))
		for i in permutation_array:	
			previous_i = precision_array[i]
			write_conf(conf_file,precision_array)
			while run_program(program):
				previous_i = precision_array[i]
				#print precision_array
				precision_array[i] = precision_array[i] - 1;
				#print precision_array[i] 
				#decrease the precision at point i
				write_conf(conf_file,precision_array)
			precision_array[i] = previous_i
			#print precision_array
			#print i
			#print permutation_array
		write_log(precision_array, loop)
		#print 'write log '
	write_conf(conf_file, original_array)		
	
def run_program(program):
	import subprocess
	s1 = subprocess.check_output(program)
	s2 = subprocess.check_output(["echo", "Hello World!"])
	#print 's1 ' + s1
	#print 's2 ' + s2
	if s1 == s2 :
		return True
	return False

def write_log(precision_array, loop):
	with open('log.txt', 'a') as log_file:
		log_file.write('Loop ' + str(loop + 1) +' :  ')
		log_file.write(str(precision_array) +'\n' )
		
def get_permutation(array_length):
	result = range(array_length)
	random.seed()
	random.shuffle(result)
	return result
	
def read_conf(conf_file_name):
	#format a1,a2,a3...
	list_argument = []
	with open(conf_file_name) as conf_file:
		for line in conf_file:
			line.replace(" ", "")
			#remove unexpected space
			array = line.split(',')
			for argument in array:
				try:
					if(len(argument)>0):
						list_argument.append(int(argument))
				except:
					print "Failed to parse conf file"
	return 	list_argument	
	
def write_conf(conf_file,precision_array):
	conf_string = ''
	for i in precision_array:
		conf_string += str(i) + ","
	with open(conf_file, 'w') as write_file:
		write_file.write(conf_string)
		
def main(argv):
		if len(argv) != 2 :
			print "Usage: ./search.py config_file program"
		else :
			random_search(argv[0],argv[1])
			 
if __name__ == "__main__":
   main(sys.argv[1:])
