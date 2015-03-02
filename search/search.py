#!/usr/bin/python
import sys
import random
import subprocess
import os
import os.path

LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2

target_result=[]

error_rate = 0.001

ZERO_error_rate=1e-8

num_var_ignore = 5

lower_precision_bound = 4

minimum_cost = 1000000 #some abitrary big value for cost comparision

minimum_configurations = [] #result of minimum precisions configurations
  
def random_search(conf_file,target_file, program):
	global target_result
	if os.path.exists('log.txt'):
		os.remove('log.txt')
	random.seed()
	target_result = read_target(target_file)
	original_array = read_conf(conf_file)
	reach_lower_bound = False

	for loop in range(len(original_array)):
#	for fake_precision in range(2,65):
		precision_array = list(original_array)
		permutation_array = get_permutation(len(original_array))
		for i in permutation_array:	
#			previous_i = precision_array[i]
			write_conf(conf_file,precision_array)

			boundary = [2,64,33]
			while ((boundary[UPPER_BOUND] - boundary[LOWER_BOUND]) != 1):
				precision_array[i] = boundary[AVERAGE];
				write_conf(conf_file,precision_array)
				if (run_program(program)):
					boundary[UPPER_BOUND] = boundary[AVERAGE]
				else:
					boundary[LOWER_BOUND] = boundary[AVERAGE]	
				boundary[AVERAGE] = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND])/2
			if boundary[UPPER_BOUND] < lower_precision_bound:
				boundary[UPPER_BOUND] = lower_precision_bound
			precision_array[i] = boundary[UPPER_BOUND]
			
		update_cost(precision_array)
		write_log(precision_array, loop , permutation_array)
		#print 'write log '
	print 'List of possible configurations: '
#	final_result=[ii for n,ii in enumerate(minimum_configurations) if ii not in minimum_configurations[:n]]
	for item in minimum_configurations:	
		write_log(item,-2, ['------Final result-------'])
		print item
	write_conf(conf_file, original_array)		
	
def run_program(program):
#	output = subprocess.Popen(['sh', 'run_lbm_mpfr.sh'], stdout=subprocess.PIPE).communicate()[0]
	output = subprocess.Popen([program, ''], stdout=subprocess.PIPE).communicate()[0]
	floating_result = parse_output(output)
	return check_output(floating_result,target_result)

def check_output(floating_result,target_result):
	if len(floating_result) != len(target_result):
		print 'Error : floating result has length: %s while target_result has length: %s' %(len(floating_result),len(target_result))
		print floating_result
		return False
	for i in range(len(floating_result)):
		if(target_result[i] == 0.0):
			if (abs(floating_result[i]) > ZERO_error_rate):
				print 'Wrong result at variable: %s , MPFR_result: %s , target_result: %s' %(i+1,floating_result[i],target_result[i])
				return False
		else:
			error = abs((floating_result[i] - target_result[i]))/target_result[i]
			
		if error > error_rate :
			print 'Wrong result at variable: %s (error = %s), MPFR_result: %s , target_result: %s' %(i+1,error,floating_result[i],target_result[i])
			return False
	return True

def update_cost(precision_array):
	global minimum_configurations
	global minimum_cost
	temp=sum(precision_array) 
	if temp< minimum_cost:
		minimum_cost = temp
		#delete result list
		minimum_configurations = [] 
		minimum_configurations.append(precision_array)
	elif temp == minimum_cost:
		#append to result
		minimum_configurations.append(precision_array)

def write_log(precision_array, loop, permutation):
	with open('log.txt', 'a') as log_file:
		log_file.write('Loop ' + str(loop + 1) +' : ')
		log_file.write('Permutation vector : ' + str(permutation) + '\n') 
		log_file.write('Result : ' +  str(precision_array) +'\n' )
		log_file.write('------------------------------------\n')

def get_permutation(array_length):
	result = range(array_length)
	random.shuffle(result)
	return result

def parse_output(line):
	list_target = []
	line.replace(" ", "")
	line.replace('\n','')
	#remove unexpected space
	array = line.split(',')
#	print array
	for target in array:
		try:
			if(len(target)>0 and target!='\n'):
				list_target.append(float(target))
		except:
			#print "Failed to parse output string"
			continue
#		print list_target
	return 	list_target[5:]	
		
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
