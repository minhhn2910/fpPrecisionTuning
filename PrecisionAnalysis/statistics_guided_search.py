#!/usr/bin/python

""" Python version of statistics guided search. Assume that the program outputs directly to stdout
Written by Minh Ho
(c) Copyright, All Rights Reserved. NO WARRANTY.
This algorithm makes use of 2 files, greedy_search_mpi.py and statistics_analysis.py
I didn't include the two files here and use their functions because they are executable for their own purpose 
 + greedy_search_mpi.py analyses the presision of 1 input on a certain error threshold
 + statistics_analysis.py performs a statistical analysis, i.e. average and percentile, variance, ... when applying a precicions vector to a number of random inputs (default 1000)
To make the scipts more portable, They will be executed here, the output will be processed accordingly.
"""
import sys
import json
import subprocess
import shlex
import random

PERCENTILE_GUIDED = False #default: converging on percentile, if false: converging on avg_error
TEST_RANGE = 1000 #number of random input for statistics analysis. 1000 is enough to get some statistics features
NUM_PROCS = 8 #number of available processors in the cluster
TEST_SEED = 32
TARGET_SQNR = 50 #
AFTER_SEARCH_TEST = True #Search based on the statistics of 1000 inputs, after searching, it is optional to test the result on more inputs
AFTER_SEARCH_TEST_RANGE= 100000 # test on 100K inputs after searching
config_file = "config_file.txt" #default, c2mpfr tool also generates this file

class statistics_feature:
	min_seed = 0 
	min_sqnr = 1
	max_seed = 2
	max_sqnr = 3
	average = 4
	percentile = 5


def write_conf(precision_array):
    conf_string = ''
    for i in precision_array:
        conf_string += str(i) + ','
    with open(config_file, 'w') as write_file:
        write_file.write(conf_string)

def extract_feature(original_version,mpfr_version,num_test=TEST_RANGE):
	#" mpirun -np #numProcs ./statistics_analysis.py float_ver mpfr_ver range"	
	command = "mpirun -np %s ./statistics_analysis.py %s %s %s"%(NUM_PROCS,original_version,mpfr_version,num_test)
	args = shlex.split(command)
	output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
	output_array = json.loads(output)
	if (num_test!= TEST_RANGE):
		print("\n\nStatictics analysis")
		print("Number of random inputs: %s" %(num_test))
		print("Min SQNR: %s "%(output_array[statistics_feature.min_sqnr]))
		print("Max SQNR: %s "%(output_array[statistics_feature.max_sqnr]))
		print("Average SQNR: %s "%(output_array[statistics_feature.average]))
		print("Percentile 95%%: %s "%(output_array[statistics_feature.percentile]))
		
	if PERCENTILE_GUIDED:
		return (output_array[statistics_feature.min_seed],output_array[statistics_feature.percentile])
	else: #converge on avg_error of 1000 inputs
		return (output_array[statistics_feature.min_seed],output_array[statistics_feature.average])
	

def generate_target_file(original_version, seed):
	command = "./%s %s"%(original_version, seed)
	args = shlex.split(command)
	with open("target.txt","w") as out:
		output = subprocess.Popen(args,stdout=out)	
	
def feature_guided_search(original_version, mpfr_version):
	previous_sqnr = 0 
	current_precision_vector = []
	combined_precision_vector = [] 
	current_sqnr = 0
	#step 1 : pick a random input :
	rand_input = TEST_SEED
	#step 2 : search on the input :
	while (current_sqnr < TARGET_SQNR):
		generate_target_file(original_version, rand_input)
		print("\n ---------------------------------")
		print("search on 1 input %s " %(rand_input))
		#" mpirun -np #numProcs ./greedy_search_mpi.py seed_number program""
		command = "mpirun -np %s ./greedy_search_mpi.py %s %s"%(NUM_PROCS, rand_input,mpfr_version )
		args = shlex.split(command)
		output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
		current_precision_vector = json.loads(output)
		print("current precision: "  + str(current_precision_vector))
		if len(combined_precision_vector) == 0:
			combined_precision_vector = current_precision_vector
		else:
			combined_precision_vector = list(map(max, zip(combined_precision_vector,current_precision_vector)))
		print("combined precision: " + str(combined_precision_vector))
		write_conf(combined_precision_vector)
		print("extracting feature on %s inputs"%(TEST_RANGE))
		# test the current_precision on 1000 inputs, get new rand_input = min_seed
		(rand_input, current_sqnr) = extract_feature(original_version,mpfr_version)
		print("current SQNR " + str(current_sqnr))
		if (previous_sqnr == current_sqnr) and (current_sqnr < TARGET_SQNR):
			#loop, need sthing to break tie
			print("loop detected, try with other rand_input")
			rand_input = random.randrange(TEST_RANGE)
		previous_sqnr = current_sqnr
		
	print("\n ----------Final result ---------")
	print(str(combined_precision_vector))
	if AFTER_SEARCH_TEST : 
		print("\n\n Extracting features again on %s input"%(AFTER_SEARCH_TEST_RANGE))
		extract_feature(original_version,mpfr_version,AFTER_SEARCH_TEST_RANGE)
		
def main(argv):
	if (len(argv) != 2):
		print("Usage: ./statistics_guided_search.py original_version mpfr_version")
		sys.exit()
	feature_guided_search(argv[0], argv[1])
if __name__ == '__main__':
    main(sys.argv[1:])	
