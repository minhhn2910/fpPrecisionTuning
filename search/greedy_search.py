""" Python simplified version of greedy search. Assume that the program outputs directly to stdout
Written by Minh Ho (minhhn2910@gmail.com)
(c) Copyright, All Rights Reserved. NO WARRANTY.
"""
#!/usr/bin/python
import sys
import subprocess
import os
import os.path

LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2

target_result=[]

error_rate = 0.001

#ZERO_error_rate=1e-8

current_error = 0.00

error_reduced = [] #contains the reduced amount of errors when increasing each var
#updated = []

lower_precision_bound = 4

minimum_cost = 1000000 #some abitrary big value for cost comparision

minimum_configurations = [] #result of minimum precisions configurations

  
def update_error(num_vars,config_array,program):
#TODO: update error vector based on the increase of precision of vars
	global error_reduced
	min_error_index = 0
	min_error =  1000000 #some abitrary big value for error comparision
	for i in range(num_vars):
		config_array[i] += 1
		write_conf(config_array)
		error_reduced[i] = run_program(program)
		if error_reduced[i] < min_error:
			min_error_index = i 
			min_error = error_reduced[i]
		config_array[i] -= 1
	config_array[min_error_index] += 1
	return config_array, min_error
	
def isolated_var_analysis(conf_file,program):
	original_array = read_conf(conf_file)
	result_array = [53]*len(original_array)
	for i in range(len(original_array)):	
#			previous_i = precision_array[i]
		precision_array = [53]*len(original_array)
		write_conf(conf_file,precision_array)
		boundary = [2,54,28]
		while ((boundary[UPPER_BOUND] - boundary[LOWER_BOUND]) != 1):
			precision_array[i] = boundary[AVERAGE];
			write_conf(conf_file,precision_array)
			if (run_program(program) < error_rate):
				boundary[UPPER_BOUND] = boundary[AVERAGE]
			else:
				boundary[LOWER_BOUND] = boundary[AVERAGE]	
			boundary[AVERAGE] = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND])/2
		if boundary[UPPER_BOUND] < lower_precision_bound:
			boundary[UPPER_BOUND] = lower_precision_bound
		result_array[i] = boundary[UPPER_BOUND]
		
	return result_array

def greedy_search(conf_file,target_file, program):
#TODO: search from min_conf, increase each vars a time so that the error_Reduced is maximum	
	global target_result
	global current_error
	global error_reduced #for debugging purpose
	target_result = read_target(target_file)
	
	min_conf = isolated_var_analysis(conf_file,program)
	error_reduced = [0.00]*len(min_conf)
	result_precision = [53]*len(min_conf)
	current_conf = list(min_conf)
	write_conf(conf_file,min_conf)
	current_error = run_program(program)
	while (current_error>error_rate):
		current_conf, current_error = update_error(len(min_conf),program)
		#update_cost(precision_array)
		write_log(current_conf, -1 , [str(current_error)])
		#print 'write log '
	write_log(current_conf,-2, ['------Final result-------'])
#	write_conf(conf_file, original_array)		
	
def run_program(program):
#	output = subprocess.Popen(['sh', 'run_lbm_mpfr.sh'], stdout=subprocess.PIPE).communicate()[0]
	output = subprocess.Popen([program, ''], stdout=subprocess.PIPE).communicate()[0]
	floating_result = float(output)
	return check_output(floating_result,target_result)

def check_output(floating_result,target_result):
#TODO: modify this func to return checksum error. instead of true and false. feed the checsum error to greedy decision func
	if len(floating_result) != len(target_result):
		print 'Error : floating result has length: %s while target_result has length: %s' %(len(floating_result),len(target_result))
		print floating_result
		return 0.0
	sum_error = 0.0	
	for i in range(len(floating_result)):
		if target_result[i] == 0.0:
			sum_error += abs(floating_result[i])
		else:
			sum_error += abs((floating_result[i] - target_result[i])/target_result[i])
	return sum_error


def write_log(precision_array, loop, permutation):
	with open('log.txt', 'a') as log_file:
		log_file.write('Loop ' + str(loop + 1) +' : ')
		log_file.write('Permutation vector : ' + str(permutation) + '\n') 
		log_file.write('Result : ' +  str(precision_array) +'\n' )
		log_file.write('------------------------------------\n')

def read_conf(conf_file_name):
	#format a1,a2,a3,...
	list_argument = []
	with open(conf_file_name) as conf_file:
		for line in conf_file:
			line.replace(" ", "")
			#remove unexpected space
			array = line.split(',')	
			for argument in array:
				try:
					if(len(argument)>0 and argument!='\n'):
						list_argument.append(int(argument))
				except:
					print "Failed to parse conf file"
	return 	list_argument	

def read_target(target_file):
	#format a1,a2,a3...
	list_target = []
	with open(target_file) as conf_file:
		for line in conf_file:
			line.replace(" ", "")
			#remove unexpected space
			array = line.split(',')
			for target in array:
				try:
					if(len(target)>0 and target!='\n'):
						list_target.append(float(target))
				except:
					print "Failed to parse target file"
	return 	list_target	

def write_conf(conf_file,original_array):
	conf_string = ''
	for i in original_array:
		conf_string += str(i) + ","
	with open(conf_file, 'w') as write_file:
		write_file.write(conf_string)
		
def main(argv):

#	testoutput = subprocess.Popen(['cat', '../tests/output.txt'], stdout=subprocess.PIPE).communicate()[0]
#	parse_output(testoutput)
#	print parse_output('9.99999999999999944489e-1,9.99999999999999944489e-1,1.29999999999993168001e6,0,0,9.99998146097700935098e-1,1.04314342693500363562,1.30096331451181332761e6,0,1.27236149465357238661e-2,')
	if len(argv) != 3 :
		print "Usage: ./search.py config_file target_file program"
	else :
		if not ('/' in argv[2]):
			argv[2] = './' + argv[2]

		random_search(argv[0],argv[1],argv[2])
			 
if __name__ == "__main__":
   main(sys.argv[1:])
