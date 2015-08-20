#!/usr/bin/python2.6
""" Python simplified version of greedy search. Assume that the program outputs directly to stdout
Written by Minh Ho (minhhn2910@gmail.com)
(c) Copyright, All Rights Reserved. NO WARRANTY.
"""
import sys
import subprocess
import shutil
import os
import os.path
from mpi4py import MPI
LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2


#basic info
mpi_comm = MPI.COMM_WORLD
mpi_rank = MPI.COMM_WORLD.Get_rank()
mpi_size = MPI.COMM_WORLD.Get_size()
mpi_name = MPI.Get_processor_name()

#number of variables
total_num_var = 0


target_result=[]

error_rate = 0.001

#ZERO_error_rate=1e-8

current_error = 0.00

error_reduced = [] #contains the reduced amount of errors when increasing each var
#updated = []

lower_precision_bound = 4

minimum_cost = 1000000 #some abitrary big value for cost comparision

#minimum_configurations = [] #result of minimum precisions configurations

def refine_result (conf_file, num_vars,config_array,program):
	for i in range(num_vars): #mpi here
		if config_array[i] ==4 :
			continue
		stop_error = False 
		while not stop_error:
			config_array[i] -=1
			write_conf(conf_file,config_array)
			current_error = run_program(program)
			print current_error 
			print i 
			if current_error > error_rate:
				stop_error = True
				config_array[i] +=1
			if config_array[i]<=lower_precision_bound:
				stop_error = True
	print config_array
	return config_array	



  
def update_error_master(conf_file, num_vars,config_array,program,dependency_graph ):
#TODO: update error vector based on the increase of precision of vars
	global error_reduced
	min_error_index = 0
	min_error =  1000000 #some abitrary big value for error comparision
	min_error_j=0
	min_error_cost=1000000
	
	num_elements_sent = 0
	recv_element = 0.0
	for i in range(mpi_size-1):
		#~ print "send from %d  to %d data %d"%(0,i+1,i)
		if num_elements_sent < num_vars:
			mpi_comm.send(i, dest=i+1, tag=1)
			num_elements_sent += 1
		else:
			mpi_comm.send(0, dest=i+1, tag=0) #signal finish proc.

	for i in range(num_vars):	#mpi_here
		
		status = MPI.Status()
		recv_element = mpi_comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status) 		
		index = status.Get_tag()
		dest_proc = status.Get_source()
		error_reduced[index] = recv_element
		if error_reduced[index] < min_error:
			min_error_index = index 
			min_error = error_reduced[index]
			increase_list = get_group_byIndex(index,dependency_graph) #get the group for reference
			min_error_cost = len(increase_list)
		elif error_reduced[index] == min_error:
			#check for cost, lower cost = lower in increase precision
			increase_list = get_group_byIndex(index,dependency_graph) #get the group for reference
			if len(increase_list) < min_error_cost:
				min_error_index = index 
				min_error = error_reduced[index]			
				min_error_cost = len(increase_list)		

		if num_elements_sent < num_vars: #send more to available proc
			mpi_comm.send(num_elements_sent, dest=dest_proc, tag=1)
			#~ print "send from %d  to %d data %d"%(0,dest_proc,num_elements_sent)
			num_elements_sent += 1
		else:
			mpi_comm.send(0, dest=dest_proc, tag=0) #signal finish proc.		
		

	if min_error == current_error: #infinite loop detected
		min_error_index = num_vars+1 #increase all vars to break tie		
		break_tie_conf_array = []
		for item in config_array:
			break_tie_conf_array.append(item+1)
		write_conf(conf_file,config_array)
                min_error = run_program(program)

		
	print 'min error index ' + str(min_error_index)
	final_increase_list = get_group_byIndex(min_error_index,dependency_graph)
	for index in final_increase_list:
		config_array[index] += 1
		
	print error_reduced, min_error
	print config_array
	min_error = mpi_comm.bcast(min_error, root=0)
	config_array = mpi_comm.bcast(config_array, root=0)
	return config_array, min_error




def update_error_worker(conf_file, num_vars,config_array,program,dependency_graph ):
#TODO: update error vector based on the increase of precision of vars
	min_error_index = 0
	min_error =  1000000 #some abitrary big value for error comparision
	min_error_j=0
	min_error_cost=1000000
	send_back_error = 0.0 
	working_index = 0
	status = MPI.Status()
	working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG, status=status) 
	#~ print "worker recv from %d  to %d data %d  Tag %d"%(0,mpi_rank,working_index,status.Get_tag())
	
	while(status.Get_tag() > 0):	
		increase_list = get_group_byIndex(working_index,dependency_graph)
		#~ print 'cal error ' 
		#~ print increase_list
		#for j in range(1,3): # 1 2
		for index in increase_list:
			config_array[index] += 1
		
		write_conf(conf_file,config_array)
		send_back_error = run_program(program)
		
		for index in increase_list:
			config_array[index] -= 1
		
		
		mpi_comm.send(send_back_error, dest=0, tag=working_index)		
		working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
		
		
	min_error = mpi_comm.bcast(min_error, root=0)
	config_array = mpi_comm.bcast(config_array, root=0)
	return config_array, min_error

def isolated_var_analysis_master(conf_file,program):
	original_array = read_conf(conf_file)
	result_array = [53]*len(original_array)
	num_elements_sent = 0
	recv_element = 0
	for i in range(mpi_size-1):
		if num_elements_sent<len(original_array):
			mpi_comm.send(i, dest=i+1, tag=1)
			num_elements_sent += 1
		else:
			mpi_comm.send(0, dest=i+1, tag=0) #signal finish proc.

	
	for i in range(len(original_array)):	#mpi_here
		
		status = MPI.Status()
		recv_element = mpi_comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status) 
		
		index = status.Get_tag()
		dest_proc = status.Get_source()
		result_array[index] = recv_element
		#~ print "recv from %d  to %d data %d"%(dest_proc,0,recv_element)
		if num_elements_sent < len(original_array): #send more to available proc
			mpi_comm.send(num_elements_sent, dest=dest_proc, tag=1)
			#~ print "send from %d  to %d data %d"%(0,dest_proc,num_elements_sent)
			num_elements_sent += 1
		else:
			mpi_comm.send(0, dest=dest_proc, tag=0) #signal finish proc.
			
	return result_array

def isolated_var_analysis_worker(conf_file,program):
	
	original_array = read_conf(conf_file)
	result_array = [53]*len(original_array)
	working_index = 0
	status = MPI.Status()
	working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG, status=status) 
	#~ print "worker recv from %d  to %d data %d  Tag %d"%(0,mpi_rank,working_index,status.Get_tag())
	
	while(status.Get_tag() > 0):
		precision_array = [53]*len(original_array)
		write_conf(conf_file,precision_array)
		boundary = [2,54,28]
		while ((boundary[UPPER_BOUND] - boundary[LOWER_BOUND]) != 1):
			precision_array[working_index] = boundary[AVERAGE];
			write_conf(conf_file,precision_array)
			if (run_program(program) <= error_rate):
				boundary[UPPER_BOUND] = boundary[AVERAGE]
			else:
				boundary[LOWER_BOUND] = boundary[AVERAGE]	
			boundary[AVERAGE] = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND])/2
		if boundary[UPPER_BOUND] < lower_precision_bound:
			boundary[UPPER_BOUND] = lower_precision_bound
		send_back_result = boundary[UPPER_BOUND]
		#~ print "worker send from %d  to %d data %d  Tag %d"%(mpi_rank,0,send_back_result,working_index)
		mpi_comm.send(send_back_result, dest=0, tag=working_index)
		
		working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
		

#~ def greedy_search_master(conf_file,program):

	
	
def greedy_search_master(conf_file, program):
#TODO: search from min_conf, increase each vars a time so that the error_Reduced is maximum	
	global target_result
	global current_error
	global total_num_var
	global error_reduced #for debugging purpose
	dependency_graph = build_dependency_path('dependency_graph.txt')
	
	#target_result = read_target(target_file)
	if os.path.exists('log.txt'):
		os.remove('log.txt')	
	print "isolated_var_analysis ---------" 
	mpi_comm.Barrier() 
	
	min_conf = isolated_var_analysis_master(conf_file,program)
	mpi_comm.Barrier()
	
	error_reduced = [0.00]*len(min_conf)
	result_precision = [53]*len(min_conf)
	current_conf = list(min_conf)
	total_num_var = len(min_conf)
	print 'min_conf found ------------'
	print min_conf 
	
	min_conf = mpi_comm.bcast(min_conf, root=0)
	
	write_conf(conf_file,min_conf)
	current_error = run_program(program)
	while (current_error>error_rate):
		current_conf, current_error = update_error_master(conf_file,len(min_conf),current_conf,program,dependency_graph)
		#update_cost(precision_array)	
		
		write_log(current_conf, -1 , [str(current_error)])
		mpi_comm.Barrier()
		#barrier here
		
		#print 'write log '
	
	print "step2 finished "
		
	final_result = refine_result (conf_file, len(min_conf),current_conf,program)
	
	write_log(final_result,-2, ['------Final result-------'])
	
#~ #	write_conf(conf_file, original_array)		

def greedy_search_worker(conf_file, program):
#TODO: search from min_conf, increase each vars a time so that the error_Reduced is maximum	
	global target_result
	global current_error
	global error_reduced #for debugging purpose
	global total_num_var
	print "worker launched %s"%(mpi_name)
	min_conf = []
	current_conf = []
	dependency_graph = build_dependency_path('dependency_graph.txt')
	mpi_comm.Barrier() 
	isolated_var_analysis_worker(conf_file, program)
	mpi_comm.Barrier()
	
	min_conf = mpi_comm.bcast(min_conf, root=0)
	current_conf = min_conf
	total_num_var = len(min_conf)
	write_conf(conf_file,min_conf)
	current_error = run_program(program)
	while (current_error>error_rate):
		current_conf, current_error = update_error_worker(conf_file,len(min_conf),current_conf,program,dependency_graph)
		mpi_comm.Barrier()	
		
	
	#~ print "master %s"%(new_program_path)
	#~ #target_result = read_target(target_file)
	#~ if os.path.exists('log.txt'):
		#~ os.remove('log.txt')	
	#~ print "isolated_var_analysis ---------" 
	#~ min_conf = isolated_var_analysis(conf_file,program)
	#~ error_reduced = [0.00]*len(min_conf)
	#~ result_precision = [53]*len(min_conf)
	#~ current_conf = list(min_conf)
	#~ print 'min_conf found ------------'
	#~ print min_conf 
	#~ write_conf(conf_file,min_conf)
	#~ current_error = run_program(program)
	#~ while (current_error>error_rate):
		#~ current_conf, current_error = update_error(conf_file,len(min_conf),current_conf,program,dependency_graph)
		#~ #update_cost(precision_array)
		#~ write_log(current_conf, -1 , [str(current_error)])
		#~ #print 'write log '
	#~ final_result = refine_result (conf_file, len(min_conf),current_conf,program)
	#~ write_log(final_result,-2, ['------Final result-------'])
#~ #	write_conf(conf_file, original_array)	

	
def run_program(program):
#	output = subprocess.Popen(['sh', 'run_lbm_mpfr.sh'], stdout=subprocess.PIPE).communicate()[0]
	output = subprocess.Popen([program, ''], stdout=subprocess.PIPE).communicate()[0]
	return float(output)
	#~ floating_result = [float(output)]
	#~ return check_output(floating_result,target_result)

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


#done
def get_group_byIndex(current_index,dependency_graph):
#TODO: Return a group of indexes of vars associated with current_index as a result of dependency_graph  
## all indices will need to be reduced by 1. as index 0 is reserved for all tempvars 
        result = []
        if (current_index >= total_num_var): #specific case, return all vars as a group
                result = range(total_num_var)
        else:
                result.append(current_index)
                if dependency_graph.has_key(str(current_index)):
                        for item in dependency_graph.get(str(current_index)):
                                result.append(int(item))
        return result
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
#	print reverse_graph_dict
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
	program = './run_fft.sh'
	config_file = 'config_file.txt'
	binary_file = 'fft_mpfr'
	if mpi_size == 1:
		return
	new_program_path = 'mpi_data_' + str(mpi_rank) + program.replace('./','/')  
	new_config_file = 'mpi_data_' + str(mpi_rank) + '/' + config_file
	shutil.rmtree(os.path.dirname(new_program_path),ignore_errors=True)
	os.makedirs(os.path.dirname(new_program_path))
	shutil.copy(config_file,os.path.dirname(new_program_path))
	shutil.copy('run_fft.sh',os.path.dirname(new_program_path))
	shutil.copy(binary_file,os.path.dirname(new_program_path))
	
	mpi_comm.Barrier() 
	if mpi_rank == 0: #master
		greedy_search_master(new_config_file, new_program_path)
	else:
		greedy_search_worker(new_config_file, new_program_path)
		
		#build_dependency_path('dependency_graph.txt')
			 
if __name__ == "__main__":
   main(sys.argv[1:])
