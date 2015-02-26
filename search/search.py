#!/usr/bin/python
import sys
import random
import subprocess
import os
import os.path

target_result=[]

error_rate = 0.001

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
		precision_array = list(original_array)
		permutation_array = get_permutation(len(original_array))
		for i in permutation_array:	
			previous_i = precision_array[i]
			write_conf(conf_file,precision_array)
			while run_program(program):
				previous_i = precision_array[i]
				#print precision_array
				precision_array[i] = precision_array[i] - 1;
				if precision_array[i] < lower_precision_bound :
					break
				#print precision_array[i] 
				#decrease the precision at point i
				write_conf(conf_file,precision_array)
			precision_array[i] = previous_i
			#print precision_array
			#print i
			#print permutation_array
		update_cost(precision_array)
		write_log(precision_array, loop , permutation_array[0])
		#print 'write log '
	print 'The list of possible configurations: '
#	final_result=[ii for n,ii in enumerate(minimum_configurations) if ii not in minimum_configurations[:n]]
	for item in minimum_configurations:	
		print item
	write_conf(conf_file, original_array)		
	
def run_program(program):
	output = subprocess.Popen(['../tests/test.py', ''], stdout=subprocess.PIPE).communicate()[0]
	floating_result = parse_output(output)
	return check_output(floating_result,target_result)

def check_output(floating_result,target_result):
	if len(floating_result) != len(target_result):
		print 'Error : floating result has length: %s while target_result has length: %s' %(len(floating_result),len(target_result))
		return False
	for i in range(len(floating_result)):
		if(target_result[i] == 0.0):
			error = abs((floating_result[i] - target_result[i]))
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

def write_log(precision_array, loop, first_variable):
	with open('log.txt', 'a') as log_file:
		log_file.write('Loop ' + str(loop + 1) +' : ' + '1st variable: ' + str(first_variable) +' :  ' )
		log_file.write(str(precision_array) +'\n' )
		
def get_permutation(array_length):
	result = range(array_length)
	random.shuffle(result)
	return result

def parse_output(output_string):
	result = []
	lines = output_string.split('\n')
	count = 0
	valid = False
	for line in lines:
		if 'LBM_showGridStatistics:' in line :
			count = count + 1
			if count == 2 :
				valid = True
		#filter 3 results minRho maxRho mass first
		if valid and ('minRho:' in line or 'minU:' in line):
			filtered_values =  filter(lambda a: a!= '',line.split(' '))
			for i in range(len(filtered_values)):
				if i%2==1:
					try:
						result.append(float(filtered_values[i]))
					except:
						print 'failed to get floating value from output: ' + filtered_values[i]
#	print result		
	return result
			
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

def write_conf(conf_file,precision_array):
	conf_string = ''
	for i in precision_array:
		conf_string += str(i) + ","
	with open(conf_file, 'w') as write_file:
		write_file.write(conf_string)
		
def main(argv):

#	testoutput = subprocess.Popen(['cat', '../tests/output.txt'], stdout=subprocess.PIPE).communicate()[0]
#	parse_output(testoutput)
	if len(argv) != 3 :
		print "Usage: ./search.py config_file target_file program"
	else :
		if not ('/' in argv[2]):
			argv[2] = './' + argv[2]

		random_search(argv[0],argv[1],argv[2])
			 
if __name__ == "__main__":
   main(sys.argv[1:])
