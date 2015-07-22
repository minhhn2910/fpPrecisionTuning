#!/usr/bin/python
""" Python simplified version of greedy search. Assume that the program outputs directly to stdout
Written by Minh Ho (minhhn2910@gmail.com)
(c) Copyright, All Rights Reserved. NO WARRANTY.
"""
import sys
import subprocess
import os
import os.path

LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2

target_result=[]

error_rate = 0.001

ZERO_error_rate=1e-8

current_error = 0.00

error_reduced = [] #contains the reduced amount of errors when increasing each var
#updated = []

lower_precision_bound = 4

minimum_cost = 1000000 #some abitrary big value for cost comparision

#minimum_configurations = [] #result of minimum precisions configurations


  
def update_error(conf_file, num_vars,config_array,program):
#TODO: update error vector based on the increase of precision of vars
	global error_reduced
	min_error_index = 0
	min_error =  1000000 #some abitrary big value for error comparision
	for i in range(num_vars):
		config_array[i] += 1
		write_conf(conf_file,config_array)
		error_reduced[i] = run_program(program)
		if error_reduced[i] < min_error:
			min_error_index = i 
			min_error = error_reduced[i]
		config_array[i] -= 1
	config_array[min_error_index] += 1
	print error_reduced, min_error
	print config_array
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
			if (run_program(program) <= error_rate):
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
	if os.path.exists('log.txt'):
		os.remove('log.txt')	
	min_conf = isolated_var_analysis(conf_file,program)
	error_reduced = [0.00]*len(min_conf)
	result_precision = [53]*len(min_conf)
	current_conf = list(min_conf)
	write_conf(conf_file,min_conf)
	current_error = run_program(program)
	while (current_error>error_rate):
		current_conf, current_error = update_error(conf_file,len(min_conf),current_conf,program)
		#update_cost(precision_array)
		write_log(current_conf, -1 , [str(current_error)])
		#print 'write log '
	write_log(current_conf,-2, ['------Final result-------'])
#	write_conf(conf_file, original_array)		
	
def run_program(program):
#	output = subprocess.Popen(['sh', 'run_lbm_mpfr.sh'], stdout=subprocess.PIPE).communicate()[0]
	output = subprocess.Popen([program, ''], stdout=subprocess.PIPE).communicate()[0]
	floating_result = [float(output)]
	return check_output(floating_result,target_result)

def check_output(floating_result,target_result):
#TODO: modify this func to return checksum error. instead of true and false. feed the checsum error to greedy decision func
	if len(floating_result) != len(target_result):
		print 'Error : floating result has length: %s while target_result has length: %s' %(len(floating_result),len(target_result))
		print floating_result
		return 0.0
	max_error = 0.0
	for i in range(len(floating_result)):
		current_err = 0.0
		if target_result[i] == 0.0:
			#if target == 0.0 => floating_result <= ZERO_error_rate=
                	# it's equivalent to abs((flt_rslt - ZERO_error_rate/2.0)/(ZERO_error_rate/2.0/error_rate))<=error_rate
                	#it is correct if we return the left hand side as current_error
                        current_err = abs((floating_result[i]-ZERO_error_rate/2.0)/(ZERO_error_rate/2.0/error_rate))
			#sum_error += abs(floating_result[i])
		else:
			current_err = abs((floating_result[i] - target_result[i])/target_result[i])
		if current_err > max_error:
                        max_error = current_err
	if max_error == 0.0:
                print 'something went wrong in check_output func, error = 0.0'
        return max_error



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



#def get_group_byIndex(current_index)
#TODO: Return a group of indexes of vars associated with current_index as a result of dependency_graph	
## all indices will need to be reduced by 1. as index 0 is reserved for all tempvars 


#Done
def build_dependency_path(graph_file):
	#TODO: read the graph file in format : destination <--- list of vars that dest depends on
	#for each var, construct a path, trace from that var until we find no reachable vars.
	graph_nodes = []
	reverse_graph_dict = {}
	with open(graph_file) as data_lines:
		for line in data_lines:
			vars_array = line.replace('\n','').split(' ')
			if len(vars_array) > 1 :
				dest_node = vars_array[0]
				for item in vars_array[1:]:
					if reverse_graph_dict.has_key(item):
						current_list = reverse_graph_dict.get(item)
						if dest_node not in current_list:
							current_list.append(dest_node)
					else:
						current_list = []
						current_list.append(dest_node)
						reverse_graph_dict[item]=current_list
	for key in reverse_graph_dict.keys():
		node_list = reverse_graph_dict.get(key)
		new_node_list = list(node_list)
		stop_condition = False
		temp_node_list = list(node_list)
		traversing_node_list = temp_node_list
		while not stop_condition:
			#broad first traverse. the final result(s) is/are the node that doesnt appear on keys list
			temp_node_list = list(traversing_node_list)
			traversing_node_list = []
			for node in temp_node_list:
				stop_condition = True
				if reverse_graph_dict.has_key(node):
					for item in reverse_graph_dict.get(node):
						if item not in new_node_list:
							stop_condition = False
							new_node_list.append(item)
							traversing_node_list.append(item)
				#else = end of path
		#remove key in new_node_list if it has
		if key in new_node_list:
			new_node_list.remove(key)							
		reverse_graph_dict[key] = new_node_list
	print reverse_graph_dict
	return reverse_graph_dict
	

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
	#~ if len(argv) != 3 :
		#~ print "Usage: ./search.py config_file target_file program"
	#~ else :
		#~ if not ('/' in argv[2]):
			#~ argv[2] = './' + argv[2]
#~ 
		#~ greedy_search(argv[0],argv[1],argv[2])
		build_dependency_path('dependency_graph.txt')
			 
if __name__ == "__main__":
   main(sys.argv[1:])
