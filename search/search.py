#!/usr/bin/python
import sys

def random_search(conf_file, program):
	precision_array = read_conf(conf_file)
	for loop in range(len(precision_array)):
		permutation_array = get_permutation(len(precision_array))
		for i in permutation_array:
			while run_program(program):
				precision_array[i] = precision_array[i] - 1;
				write_conf(conf_file,precision_array)
				#decrease the precision at point i
		write_log(precision_array, loop)	

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
	for i in precision_array:
		conf_string += string(i) + ","
	with open(conf_file, 'w') as write_file:
		write_file.write(conf_string)
		
def main(argv):
		if len(argv) != 2 :
			print "Usage: ./search.py config_file program"
		else :
			random_search(argv[0],argv[1])
			 
if __name__ == "__main__":
   main(sys.argv[1:])
