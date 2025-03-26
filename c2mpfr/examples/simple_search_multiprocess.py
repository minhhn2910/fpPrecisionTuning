#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Python simplified version of greedy search. Assume that the program outputs directly to stdout.
This version uses Python multiprocessing for parallel search of programs to synthesize on FPGA
Written by Minh Ho (minhhn2910(at)gmail.com)
(c) Copyright, All Rights Reserved. NO WARRANTY.
"""

import sys
import subprocess
import shutil
import os
import os.path
import argparse
import multiprocessing as mp
from multiprocessing import Manager
from functools import partial

LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2
DEBUG = False

SEED_NUMBER = 10   #use for random input generator of some program.

# number of variables
total_num_var = 0

# basic info
dependency_graph = {}

# stop condition for the last step
stop_condition = True

target_result = []

error_rate = 1e-03 # 50dB SNR =>  error rate 10-5

ZERO_error_rate = 1e-6

current_error = 0.00

error_reduced = []  # contains the reduced amount of errors when increasing each var

# for simplicity, define target here
lower_precision_bound = 2

minimum_cost = 1000000  # some abitrary big value for cost comparision

# Add this new global variable near the other globals
ERROR_METRIC = "sqnr"  # Default metric is SQNR

def refine_result(
    conf_file,
    num_vars,
    config_array,
    program,
    ):
    for i in range(num_vars):  # mpi here
        if config_array[i] == 4:
            continue
        stop_error = False
        while not stop_error:
            config_array[i] -= 1
            write_conf(conf_file, config_array)
            current_error = run_program(program)
            if DEBUG:
                print(current_error)
                print(i)
            if current_error > error_rate:
                stop_error = True
                config_array[i] += 1
            if config_array[i] <= lower_precision_bound:
                stop_error = True

    print(config_array)
    return config_array


def parse_output(line):
    list_target = []
    if isinstance(line, bytes):
        line = line.decode('utf-8')
        
    line = line.replace(' ', '')
    line = line.replace('\n', '')

    # remove unexpected space
    array = line.split(',')

    for target in array:
        try:
            if len(target) > 0 and target != '\n':
                list_target.append(float(target))
        except:
            # print "Failed to parse output string"
            continue

    return list_target


# Worker function to process a single index
def process_index(idx, conf_file, config_array, program, dependency_graph, results_dict):
    increase_list = get_group_byIndex(idx, dependency_graph)
    
    # Make a copy of config_array to modify locally
    local_config = list(config_array)
    
    for index in increase_list:
        local_config[index] += 1

    write_conf(conf_file, local_config)
    error_result = run_program(program)

    # Store result in shared dictionary
    results_dict[idx] = error_result
    return


def update_error(
    conf_file,
    num_vars,
    config_array,
    program,
    dependency_graph,
    ):
    global error_reduced
    global current_error
    
    # Create a manager to share data between processes
    manager = Manager()
    results_dict = manager.dict()
    
    # Determine the number of processes to use (use all available cores or limit based on vars)
    num_processes = min(mp.cpu_count(), num_vars)
    
    # Create a pool of workers
    pool = mp.Pool(processes=num_processes)
    
    # Process each index in parallel
    process_func = partial(process_index, 
                          conf_file=conf_file, 
                          config_array=config_array, 
                          program=program, 
                          dependency_graph=dependency_graph, 
                          results_dict=results_dict)
    
    pool.map(process_func, range(num_vars))
    pool.close()
    pool.join()
    
    # Update error_reduced with results from processes
    for i in range(num_vars):
        error_reduced[i] = results_dict.get(i, current_error)
    
    # Find the best index to update
    min_error_index = 0
    min_error = 1000000  # some abitrary big value for error comparision
    min_error_cost = 1000000

    for i in range(num_vars):
        index = i
        if error_reduced[index] < min_error:
            min_error_index = index
            min_error = error_reduced[index]
            increase_list = get_group_byIndex(index, dependency_graph)  # get the group for reference
            min_error_cost = len(increase_list)
        elif error_reduced[index] == min_error:
            # check for cost, lower cost = lower in increase precision
            increase_list = get_group_byIndex(index, dependency_graph)  # get the group for reference
            if len(increase_list) < min_error_cost:
                min_error_index = index
                min_error = error_reduced[index]
                min_error_cost = len(increase_list)

    if min_error == current_error:  # infinite loop detected
        min_error_index = num_vars + 1  # increase all vars to break tie........
        break_tie_conf_array = []
        for item in config_array:
            break_tie_conf_array.append(item + 1)
        write_conf(conf_file, break_tie_conf_array)
        min_error = run_program(program)

    if DEBUG:
        print('min error index ' + str(min_error_index))
    final_increase_list = get_group_byIndex(min_error_index,
            dependency_graph)
    for index in final_increase_list:
        config_array[index] += 1
    if DEBUG:
        print(error_reduced, min_error)
        print(config_array)

    return (config_array, min_error)


# Worker function for isolated variable analysis
def isolated_var_worker(idx, conf_file, program, result_queue):
    precision_array = [24] * total_num_var
    boundary = [2, 24, 13]
    
    write_conf(conf_file, precision_array)
    while boundary[UPPER_BOUND] - boundary[LOWER_BOUND] != 1:
        precision_array[idx] = boundary[AVERAGE]
        write_conf(conf_file, precision_array)
        if run_program(program) <= error_rate:
            boundary[UPPER_BOUND] = boundary[AVERAGE]
        else:
            boundary[LOWER_BOUND] = boundary[AVERAGE]
        boundary[AVERAGE] = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND]) // 2
    
    if boundary[UPPER_BOUND] < lower_precision_bound:
        boundary[UPPER_BOUND] = lower_precision_bound
    
    # Return the result for this index
    result_queue.put((idx, boundary[UPPER_BOUND]))


def isolated_var_analysis(conf_file, program):
    global total_num_var
    
    original_array = read_conf(conf_file)
    total_num_var = len(original_array)
    result_array = [24] * total_num_var
    
    # Create a manager to share data between processes
    manager = Manager()
    result_queue = manager.Queue()
    
    # Create and start worker processes
    processes = []
    num_processes = min(mp.cpu_count(), total_num_var)
    
    # Create a pool of workers
    pool = mp.Pool(processes=num_processes)
    
    # Process each index in parallel
    worker_func = partial(isolated_var_worker, 
                         conf_file=conf_file, 
                         program=program, 
                         result_queue=result_queue)
    
    pool.map(worker_func, range(total_num_var))
    pool.close()
    pool.join()
    
    # Collect results
    while not result_queue.empty():
        idx, value = result_queue.get()
        result_array[idx] = value

    return result_array


# Worker function for refine_1st
def refine_1st_worker(idx, current_conf, min_conf, conf_file, program, result_queue):
    precision_array = list(current_conf)
    write_conf(conf_file, precision_array)
    boundary = [min_conf[idx] - 1,
                current_conf[idx],
                (current_conf[idx] + min_conf[idx]) // 2]
    
    while boundary[UPPER_BOUND] - boundary[LOWER_BOUND] != 1:
        precision_array[idx] = boundary[AVERAGE]
        write_conf(conf_file, precision_array)
        if run_program(program) <= error_rate:
            boundary[UPPER_BOUND] = boundary[AVERAGE]
        else:
            boundary[LOWER_BOUND] = boundary[AVERAGE]
        boundary[AVERAGE] = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND]) // 2
    
    if boundary[UPPER_BOUND] < lower_precision_bound:
        boundary[UPPER_BOUND] = lower_precision_bound
    
    # Return the result for this index
    result_queue.put((idx, boundary[UPPER_BOUND]))


def refine_1st(
    current_conf,
    min_conf,
    conf_file,
    program,
    ):
    result_array = [24] * len(current_conf)
    
    # Create a manager to share data between processes
    manager = Manager()
    result_queue = manager.Queue()
    
    # Create and start worker processes
    num_processes = min(mp.cpu_count(), len(current_conf))
    
    # Create a pool of workers
    pool = mp.Pool(processes=num_processes)
    
    # Process each index in parallel
    worker_func = partial(refine_1st_worker, 
                         current_conf=current_conf,
                         min_conf=min_conf,
                         conf_file=conf_file, 
                         program=program, 
                         result_queue=result_queue)
    
    pool.map(worker_func, range(len(current_conf)))
    pool.close()
    pool.join()
    
    # Collect results
    while not result_queue.empty():
        idx, value = result_queue.get()
        result_array[idx] = value

    return result_array


def greedy_search(conf_file, program, target_file):
    global target_result
    global current_error
    global error_reduced  # for debugging purpose
    global total_num_var

    # Create temp directories for each process to have its own copy
    base_dir = os.path.dirname(conf_file)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    target_result = read_target(target_file)

    if DEBUG:
        print(target_result)
    if os.path.exists('log.txt'):
        os.remove('log.txt')
    if DEBUG:
        print('isolated_var_analysis ---------')

    min_conf = isolated_var_analysis(conf_file, program)

    error_reduced = [0.00] * len(min_conf)
    result_precision = [24] * len(min_conf)
    current_conf = list(min_conf)
    total_num_var = len(min_conf)

    if DEBUG:
        print('min_conf found ------------')
        print(min_conf)

    write_conf(conf_file, min_conf)
    current_error = run_program(program)
    while current_error > error_rate:
        (current_conf, current_error) = update_error(conf_file,
                len(min_conf), current_conf, program, dependency_graph)

        write_log(current_conf, -1, [str(current_error)])

        if DEBUG:
            print('step2 finished ')

    global stop_condition
    stop_condition = False

    previous_satisfied_conf = []  # keep track of the last conf_ to validate the stop condition
    while not stop_condition:

        min_conf = refine_1st(current_conf, min_conf, conf_file,
                program)
        if DEBUG:
            print('######################')
            print('refine 1pass ' + str(min_conf))

        error_reduced = [0.00] * len(min_conf)
        result_precision = [24] * len(min_conf)
        current_conf = list(min_conf)
        total_num_var = len(min_conf)

        write_conf(conf_file, min_conf)
        current_error = run_program(program)

        while current_error > error_rate:
            (current_conf, current_error) = \
                update_error(conf_file, len(min_conf),
                                    current_conf, program,
                                    dependency_graph)

            write_log(current_conf, -1, [str(current_error)])

        if sum(current_conf) == sum(previous_satisfied_conf):  # stop condition.
            stop_condition = True
            if DEBUG:
                print('current error ' + str(current_error))

        previous_satisfied_conf = list(current_conf)  # update the last conf

        if DEBUG:
            print('refine 2v pass ' + str(current_conf))

    print(str(current_conf))
    write_log(current_conf, -2, ['------Final result-------'])


def run_program(program):
    output = subprocess.Popen([program, '%s'%(SEED_NUMBER)],
                              stdout=subprocess.PIPE).communicate()[0]
    
    # Convert bytes to string in Python 3
    output = output.decode('utf-8')

    floating_result = parse_output(output)

    return check_output(floating_result, target_result)


def check_output(floating_result, target_result):
    if len(floating_result) != len(target_result):
        print('Error : floating result has length: %s while target_result has length: %s' \
            % (len(floating_result), len(target_result)))
        print(floating_result)
        return 0.00
    
    # Use the global metric setting
    global ERROR_METRIC
    
    if ERROR_METRIC.lower() == "avg_abs":
        # Calculate average absolute error
        abs_error_sum = 0.00
        for i in range(len(floating_result)):
            abs_error_sum += abs(floating_result[i] - target_result[i])
        
        return abs_error_sum / len(floating_result)
    else:  # Default: "sqnr"
        # Original SQNR calculation
        signal_sqr = 0.00
        error_sqr = 0.00
        for i in range(len(floating_result)):
            signal_sqr += target_result[i] ** 2
            error_sqr += (floating_result[i] - target_result[i]) ** 2

        sqnr = 0.00
        if error_sqr != 0.00:
            sqnr = signal_sqr / error_sqr
        if sqnr != 0:
            return 1.0 / sqnr
        else:
            return 0.00


def write_log(precision_array, loop, permutation):
    with open('log.txt', 'a') as log_file:
        log_file.write('Loop ' + str(loop + 1) + ' : ')
        log_file.write('Permutation vector : ' + str(permutation) + '\n'
                       )
        log_file.write('Result : ' + str(precision_array) + '\n')
        log_file.write('------------------------------------\n')


def read_conf(conf_file_name):
    # format a1,a2,a3,...
    list_argument = []
    with open(conf_file_name) as conf_file:
        for line in conf_file:
            line = line.replace(' ', '')
            array = line.split(',')
            for argument in array:
                try:
                    if len(argument) > 0 and argument != '\n':
                        list_argument.append(int(argument))
                except:
                    print('Failed to parse conf file')
    return list_argument


def read_target(target_file):
    # format a1,a2,a3...
    list_target = []
    with open(target_file) as conf_file:
        for line in conf_file:
            line = line.replace(' ', '')

            # remove unexpected space
            array = line.split(',')
            for target in array:
                try:
                    if len(target) > 0 and target != '\n':
                        list_target.append(float(target))
                except:
                    print('Failed to parse target file')
    return list_target


def get_group_byIndex(current_index, dependency_graph):
    result = []
    if current_index >= total_num_var:  # specific case, return all vars as a group
        result = list(range(total_num_var))
    else:
        result.append(current_index)
        if str(current_index) in dependency_graph:
            for item in dependency_graph.get(str(current_index)):
                result.append(int(item))
    return result


def build_dependency_path(graph_file):
    graph_nodes = []
    reverse_graph_dict = {}
    
    if os.path.exists(graph_file):
        with open(graph_file) as data_lines:
            for line in data_lines:
                vars_array = line.replace('\n', '').split(' ')
                if len(vars_array) > 1:
                    dest_node = vars_array[0]
                    for item in vars_array[1:]:
                        if item in reverse_graph_dict:
                            current_list = reverse_graph_dict.get(item)
                            if dest_node not in current_list:
                                current_list.append(dest_node)
                        else:
                            current_list = []
                            current_list.append(dest_node)
                            reverse_graph_dict[item] = current_list
        
        for key in reverse_graph_dict.keys():
            node_list = reverse_graph_dict.get(key)
            new_node_list = list(node_list)
            stop_condition = False
            temp_node_list = list(node_list)
            traversing_node_list = temp_node_list
            while not stop_condition:
                # broad first traverse. the final result(s) is/are the node that doesnt appear on keys list
                temp_node_list = list(traversing_node_list)
                traversing_node_list = []
                for node in temp_node_list:
                    stop_condition = True
                    if node in reverse_graph_dict:
                        for item in reverse_graph_dict.get(node):
                            if item not in new_node_list:
                                stop_condition = False
                                new_node_list.append(item)
                                traversing_node_list.append(item)

            # remove key in new_node_list if it has
            if key in new_node_list:
                new_node_list.remove(key)
            reverse_graph_dict[key] = new_node_list
            
    return reverse_graph_dict


def write_conf(conf_file, original_array):
    conf_string = ''
    for i in original_array:
        conf_string += str(i) + ','
    with open(conf_file, 'w') as write_file:
        write_file.write(conf_string)


def main(argv):
    global SEED_NUMBER
    global ERROR_METRIC
    global error_rate
    global dependency_graph
    
    parser = argparse.ArgumentParser(description="Simplified version of greedy search for synthesizing FPGA programs")
    
    # Maintain backward compatibility with positional arguments
    parser.add_argument("seed_number", type=int, help="Seed number for random input generator")
    parser.add_argument("program", help="Program name (without .sh extension)")
    parser.add_argument("error_metric", nargs='?', default="sqnr", 
                       help="Error metric to use (sqnr or avg_abs)")
    
    # Add new optional arguments
    parser.add_argument("--metric", choices=["sqnr", "avg_abs"], 
                       help="Error metric to use (overrides positional argument)")
    parser.add_argument("--error", type=float, 
                       help="Error rate threshold (e.g., 2.5e-10)")
    
    args = parser.parse_args(argv)
    
    # Set global variables based on arguments
    SEED_NUMBER = args.seed_number
    program = './' + args.program + '.sh'
    config_file = 'config_file.txt'
    binary_file = args.program
    target_file = 'target.txt'
    
    # Check if the bash script exists, if not create it
    if not os.path.exists(program):
        print(f"Creating bash script {program} for {binary_file}")
        with open(program, 'w') as bash_file:
            bash_file.write('#!/bin/bash\n')
            bash_file.write('DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )\n')
            bash_file.write('cd $DIR\n')
            bash_file.write(f'./{binary_file} $1\n')
        
        # Make the bash script executable
        os.chmod(program, 0o755)
    
    # Error metric: command-line option takes precedence
    if args.metric:
        ERROR_METRIC = args.metric
    elif args.error_metric.lower() in ["sqnr", "avg_abs"]:
        ERROR_METRIC = args.error_metric.lower()
    else:
        print(f"Warning: Unknown error metric '{args.error_metric}'. Using default (sqnr).")
    
    # Error rate: if specified by user
    if args.error is not None:
        error_rate = args.error
        
    # Build dependency graph if exists
    dependency_graph = build_dependency_path('dependency_graph.txt')
    
    if __name__ == '__main__':
        # Set start method for multiprocessing (important for compatibility)
        try:
            mp.set_start_method('spawn')
        except RuntimeError:
            pass  # Already set
            
    greedy_search(config_file, program, target_file)

if __name__ == '__main__':
    main(sys.argv[1:]) 