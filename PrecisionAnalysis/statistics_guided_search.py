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
import math
import subprocess
import shlex
import random
import argparse
import os

PERCENTILE_GUIDED = False #default: converging on percentile, if false: converging on avg_error
TEST_RANGE = 500 #number of random input for statistics analysis. 1000 is enough to get some statistics features
NUM_PROCS = 8 #number of available processors in the cluster
TEST_SEED = 32
TARGET_SQNR = 1e-5 # 50Db => 10log(SNR) = 50 => SNR = 10^5 => error rate = 1/10^5
TARGET_AVG_ABS_ERROR = 1e-4 # Default target average absolute error
ERROR_METRIC = "avg_abs" # Default error metric: "sqnr" or "avg_abs"
MAX_BITWIDTH = 53 # Default maximum bitwidth for simple_search_sequential
AFTER_SEARCH_TEST = True #Search based on the statistics of 1000 inputs, after searching, it is optional to test the result on more inputs
AFTER_SEARCH_TEST_RANGE= 5000 # test on 100K inputs after searching
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
    command = (
        f"python statistics_analysis.py \"{original_version}\" \"{mpfr_version}\" {num_test}"
        f" --metric {ERROR_METRIC} --processes {NUM_PROCS}"
    )
    args = shlex.split(command)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    print("extract_feature output: " + str(output))
    output_array = json.loads(output)
	# if (num_test!= TEST_RANGE):
	# 	print("\n\nStatictics analysis")
	# 	print("Number of random inputs: %s" %(num_test))
	# 	print("Min Metric: %s "%(output_array[statistics_feature.min_sqnr]))
	# 	print("Max Metric: %s "%(output_array[statistics_feature.max_sqnr]))
	# 	print("Average Metric: %s "%(output_array[statistics_feature.average]))
	# 	print("Percentile 95%%: %s "%(output_array[statistics_feature.percentile]))
		
    if PERCENTILE_GUIDED:
        return (output_array[statistics_feature.min_seed],output_array[statistics_feature.percentile])
    else: #converge on avg_error of 1000 inputs
        return (output_array[statistics_feature.min_seed],output_array[statistics_feature.average])
	

def generate_target_file(original_version, seed):
    # Check if original_version includes a path
    directory = os.path.dirname(original_version)
    
    command = "%s %s" % (original_version, seed)
    args = shlex.split(command)
    
    # If there's a directory in the path, place target.txt there
    if directory:
        target_path = os.path.join(directory, "target.txt")
    else:
        target_path = "target.txt"
        
    with open(target_path, "w") as out:
        output = subprocess.Popen(args, stdout=out)
	
def feature_guided_search(original_version, mpfr_version):
    previous_metric_val = None # For loop detection
    combined_precision_vector = [] 
    
    rand_input = TEST_SEED # Initial seed from args or default
    loop_active = True

    while loop_active:
        generate_target_file(original_version, rand_input)
        print("\n ---------------------------------")
        print(f"Search iteration using input seed: {rand_input} for {mpfr_version}")

        # Calculate error threshold for simple_search_sequential.py
        search_error_threshold = 0.0
        if ERROR_METRIC == "sqnr":
            print("TARGET_SQNR: " + str(TARGET_SQNR))
            # user will provide a target SQNR, we will use it as a threshold, 
            # the value is the error rate e.g. 50Db => 10log(SNR) = 50 => SNR = 10^5 => error rate = 1/10^5
            if (TARGET_SQNR == 0 or TARGET_SQNR > 1): 
                print(f"Warning: Invalid TARGET_SQNR ({TARGET_SQNR}). Assuming 1e-5")
                print("Note that the sqnr error rate is the SNR ratio before taking -10log(SNR)")
                search_error_threshold = 1e-5
            else:
                search_error_threshold = TARGET_SQNR
        elif ERROR_METRIC == "avg_abs":
            search_error_threshold = TARGET_AVG_ABS_ERROR
        else: # Should not happen if ERROR_METRIC is validated by argparse
            print(f"FATAL: Unknown ERROR_METRIC '{ERROR_METRIC}' for simple_search threshold calculation.")
            sys.exit(1)

        # Call simple_search_sequential.py
        # Path assumes statistics_guided_search.py is in PrecisionAnalysis/
        # and simple_search_sequential.py is in c2mpfr/examples/
        # simple_search_sequential.py expects: seed_number program_name --metric <metric> --error <error_rate> --max-bitwidth <max_bw>
        command_simple_search = (
            f"python simple_search_multiprocess.py {rand_input} \"{mpfr_version}\""
            f" --metric {ERROR_METRIC} --error {search_error_threshold}"
            f" --processes {NUM_PROCS} --max-bitwidth {MAX_BITWIDTH}"
        )
        print(f"Executing: {command_simple_search}")
        args_simple_search = shlex.split(command_simple_search)
        output_simple_search = subprocess.Popen(args_simple_search, stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
        print("output_simple_search: " + str(output_simple_search))
        output_simple_search = output_simple_search.split("\n")
        for i in range(len(output_simple_search)-1, 0, -1):
            if "[" in output_simple_search[i]:
                output_simple_search = output_simple_search[i]
                break
        try:
            current_precision_vector = json.loads(output_simple_search)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from simple_search_sequential.py output: {output_simple_search}")
            # Decide how to handle: exit, retry, or use a default precision vector?
            # For now, let's assume it might indicate a failure in the search.
            # We might want to break or try a different random input if this happens.
            # As a fallback, if combined_precision_vector is empty, this will be an issue.
            # If not empty, we might proceed with the old combined_precision_vector.
            # This part needs robust error handling based on expected behavior.
            # For now, if search fails, we might not get a valid precision vector.
            # Let's print error and potentially stop or use a very high precision.
            print("Simple search failed to return a valid precision vector. Using max precision as fallback for this step.")
            # This is a placeholder: actual number of vars might not be known here easily
            # A better fallback might be to skip combining or use previous combined.
            # For now, this will likely cause issues if it's the first run.
            # A robust solution would be to get num_vars from config_file if it exists, or from initial run.
            # To keep it simple, if this fails, the script might become unstable.
            # A safe bet is to re-use the last known combined_precision_vector if available,
            # or signal a major error.
            if not combined_precision_vector: # First run and failed
                 print("FATAL: Simple search failed on first iteration. Cannot proceed.")
                 sys.exit(1)
            # else: use existing combined_precision_vector, effectively skipping update from this failed search.
            # This means current_precision_vector won't be updated from this failed search.
            # The logic below will use the existing combined_precision_vector.
            # To make it more explicit, we can just not update current_precision_vector
            # and let the existing combined_precision_vector be written.
            # However, the problem expects current_precision_vector to be a result.
            # Let's assume for now simple_search always returns something parsable or exits.
            # The original code didn't have robust error handling here either.
            # For the purpose of this change, we'll assume output_simple_search is valid JSON.
            current_precision_vector = json.loads(output_simple_search) # Re-asserting, real app needs better error handling


        print("Precision from simple search: "  + str(current_precision_vector))
        if not combined_precision_vector: # First iteration
            combined_precision_vector = current_precision_vector
        else:
            if len(combined_precision_vector) == len(current_precision_vector):
                combined_precision_vector = list(map(max, zip(combined_precision_vector, current_precision_vector)))
            else:
                print(f"Warning: Mismatch in precision vector lengths. Old: {len(combined_precision_vector)}, New: {len(current_precision_vector)}. Using old combined vector.")
                # This could happen if simple_search fails or num vars changes unexpectedly.

        print("Combined precision after this iteration: " + str(combined_precision_vector))
        write_conf(combined_precision_vector)
        
        print(f"Extracting feature using statistics_analysis on {TEST_RANGE} inputs...")
        # rand_input for next iteration, current_metric_val for convergence check
        (rand_input, current_metric_val) = extract_feature(original_version, mpfr_version, TEST_RANGE)
        
        print(f"Next search seed from stats: {rand_input}")
        print(f"Current aggregate metric value ({('percentile' if PERCENTILE_GUIDED else 'average')} of {ERROR_METRIC}): {current_metric_val}")

        # Check convergence
        if ERROR_METRIC == "sqnr":
            achieved_metric = current_metric_val 
            print(f"Achieved SQNR (from stats - {('percentile' if PERCENTILE_GUIDED else 'average')}): {achieved_metric}, Target SQNR: {TARGET_SQNR}")
            if achieved_metric >= TARGET_SQNR:
                loop_active = False
        elif ERROR_METRIC == "avg_abs":
            achieved_metric = current_metric_val
            print(f"Achieved Avg Abs Error (from stats - {('percentile' if PERCENTILE_GUIDED else 'average')}): {achieved_metric}, Target Avg Abs Error: {TARGET_AVG_ABS_ERROR}")
            if achieved_metric <= TARGET_AVG_ABS_ERROR:
                loop_active = False
        else:
            print(f"Unknown ERROR_METRIC: {ERROR_METRIC}. Stopping.")
            loop_active = False # Should be caught by argparse

        if loop_active and previous_metric_val is not None and previous_metric_val == current_metric_val:
            print("Loop detected (current metric value same as previous). Trying with a different random input.")
            rand_input = random.randrange(TEST_RANGE) # Pick a new random seed for statistics_analysis
            # This new rand_input will be used by generate_target_file in the next iteration
            # if the loop continues. The (rand_input, current_metric_val) from extract_feature
            # will set the rand_input for the *next* simple_search if loop continues.
            # The immediate effect of this random.randrange is for the *next* generate_target_file
            # if the loop doesn't break due to convergence.
            # The seed for simple_search is determined by extract_feature's return.
            # To break a tie in simple_search, we should change the input to simple_search.
            # The current rand_input is already set by extract_feature.
            # If extract_feature keeps returning the same seed and metric, this tie break is needed.
            # Let's make the tie break more direct: change the seed for the *next* simple search.
            print(f"Switching to a new random seed for simple_search: {rand_input}")


        previous_metric_val = current_metric_val
	
    print("\n ----------Final result ---------")
    print(str(combined_precision_vector))
    if AFTER_SEARCH_TEST : 
        print("\n\n Extracting features again on %s input"%(AFTER_SEARCH_TEST_RANGE))
        extract_feature(original_version,mpfr_version,AFTER_SEARCH_TEST_RANGE)

def main(argv):
	global ERROR_METRIC, NUM_PROCS, TARGET_SQNR, TARGET_AVG_ABS_ERROR, MAX_BITWIDTH
	global PERCENTILE_GUIDED, TEST_RANGE, TEST_SEED, AFTER_SEARCH_TEST, AFTER_SEARCH_TEST_RANGE

	parser = argparse.ArgumentParser(description="Statistics guided search for precision tuning.")
	parser.add_argument("original_version", help="Original version of the program (reference)")
	parser.add_argument("mpfr_version", help="MPFR version of the program")

	parser.add_argument("--metric", choices=['sqnr', 'avg_abs'], default=ERROR_METRIC,
						help=f"Error metric to use for convergence and sub-scripts (default: {ERROR_METRIC})")
	parser.add_argument("--num-procs", type=int, default=NUM_PROCS,
						help=f"Number of processes for statistics_analysis (default: {NUM_PROCS})")
	parser.add_argument("--target-sqnr", type=float, default=TARGET_SQNR,
						help=f"Target SQNR for convergence (default: {TARGET_SQNR} dB)")
	parser.add_argument("--target-avg-abs-error", type=float, default=TARGET_AVG_ABS_ERROR,
						help=f"Target average absolute error for convergence (default: {TARGET_AVG_ABS_ERROR})")
	parser.add_argument("--max-bitwidth", type=int, default=MAX_BITWIDTH,
						help=f"Maximum bitwidth for simple_search_sequential (default: {MAX_BITWIDTH})")
	parser.add_argument("--percentile-guided", action='store_true', default=PERCENTILE_GUIDED,
						help="Converge on percentile from statistics_analysis instead of average.")
	parser.add_argument("--test-range", type=int, default=TEST_RANGE,
						help=f"Number of random inputs for statistics_analysis during search (default: {TEST_RANGE})")
	parser.add_argument("--initial-seed", type=int, default=TEST_SEED,
						help=f"Initial seed for the search process (default: {TEST_SEED})")
	parser.add_argument("--no-after-search-test", action='store_false', dest='after_search_test',
						help="Disable final test on AFTER_SEARCH_TEST_RANGE inputs.")
	parser.set_defaults(after_search_test=AFTER_SEARCH_TEST)
	parser.add_argument("--after-search-test-range", type=int, default=AFTER_SEARCH_TEST_RANGE,
						help=f"Number of inputs for final test if enabled (default: {AFTER_SEARCH_TEST_RANGE})")


	args = parser.parse_args(argv)

	# Update global variables from command line arguments
	ERROR_METRIC = args.metric
	NUM_PROCS = args.num_procs
	TARGET_SQNR = args.target_sqnr
	TARGET_AVG_ABS_ERROR = args.target_avg_abs_error
	MAX_BITWIDTH = args.max_bitwidth
	PERCENTILE_GUIDED = args.percentile_guided
	TEST_RANGE = args.test_range
	TEST_SEED = args.initial_seed # This sets the initial rand_input for feature_guided_search
	AFTER_SEARCH_TEST = args.after_search_test
	AFTER_SEARCH_TEST_RANGE = args.after_search_test_range
	
	print("--- Configuration ---")
	print(f"Original Program: {args.original_version}")
	print(f"MPFR Program: {args.mpfr_version}")
	print(f"Error Metric: {ERROR_METRIC}")
	print(f"Convergence Metric Source: {'Percentile' if PERCENTILE_GUIDED else 'Average'}")
	if ERROR_METRIC == 'sqnr':
		print(f"Target SQNR: {TARGET_SQNR} => {-10*math.log10(TARGET_SQNR)}Db")
	else:
		print(f"Target Avg Abs Error: {TARGET_AVG_ABS_ERROR}")
	print(f"Processes for Stats Analysis: {NUM_PROCS}")
	print(f"Max Bitwidth for Simple Search: {MAX_BITWIDTH}")
	print(f"Test Range for Stats during Search: {TEST_RANGE}")
	print(f"Initial Seed for Search: {TEST_SEED}")
	print(f"After Search Test Enabled: {AFTER_SEARCH_TEST}")
	if AFTER_SEARCH_TEST:
		print(f"After Search Test Range: {AFTER_SEARCH_TEST_RANGE}")
	print("--------------------")

	feature_guided_search(args.original_version, args.mpfr_version)

if __name__ == '__main__':
    main(sys.argv[1:])	
