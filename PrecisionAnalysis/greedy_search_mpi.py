#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Python simplified version of greedy search. Assume that the program outputs directly to stdout
Written by Minh Ho
(c) Copyright, All Rights Reserved. NO WARRANTY.
"""

import sys
import subprocess
import shutil
import os
import os.path
import argparse
from mpi4py import MPI
LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2
DEBUG = False

# Add these global variables for configuration
ERROR_METRIC = "sqnr"  # Default metric is SQNR
MAX_BITWIDTH = 53      # Default maximum bitwidth

SEED_NUMBER = 10   #use for random input generator of some program.

# number of variables

total_num_var = 0

# basic info

mpi_comm = MPI.COMM_WORLD
mpi_rank = MPI.COMM_WORLD.Get_rank()
mpi_size = MPI.COMM_WORLD.Get_size()
mpi_name = MPI.Get_processor_name()

# stop condition for the last step

stop_condition = True

target_result = []

error_rate = 1e-5  # 50dB SNR =>  error rate 10-5

ZERO_error_rate = 1e-8

current_error = 0.00

error_reduced = []  # contains the reduced amount of errors when increasing each var

# updated = []

# for simplicity, define target here

lower_precision_bound = 2  # Changed from 4 to 2 to match multiprocessing version

minimum_cost = 1000000  # some abitrary big value for cost comparision


# minimum_configurations = [] #result of minimum precisions configurations

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
            # print("Failed to parse output string")
            continue

    return list_target


def update_error_master(
    conf_file,
    num_vars,
    config_array,
    program,
    dependency_graph,
    ):

# TODO: update error vector based on the increase of precision of vars

    global error_reduced
    min_error_index = 0
    min_error = 1000000  # some abitrary big value for error comparision
    min_error_j = 0
    min_error_cost = 1000000

    num_elements_sent = 0
    recv_element = 0.00

    for i in range(mpi_size - 1):
        # print("send from %d to %d data %d"%(0,i+1,i))
        if num_elements_sent < num_vars:
            mpi_comm.send(i, dest=i + 1, tag=1)
            num_elements_sent += 1
        else:
            mpi_comm.send(0, dest=i + 1, tag=0)  # signal finish proc.

    for i in range(num_vars):  # mpi_here
        status = MPI.Status()
        recv_element = mpi_comm.recv(source=MPI.ANY_SOURCE,
                tag=MPI.ANY_TAG, status=status)
        index = status.Get_tag()
        dest_proc = status.Get_source()
        error_reduced[index] = recv_element
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

        if num_elements_sent < num_vars:  # send more to available proc
            mpi_comm.send(num_elements_sent, dest=dest_proc, tag=1)
            # print("send from %d to %d data %d"%(0,dest_proc,num_elements_sent))
            num_elements_sent += 1
        else:
            mpi_comm.send(0, dest=dest_proc, tag=0)  # signal finish proc.........

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
    min_error = mpi_comm.bcast(min_error, root=0)
    config_array = mpi_comm.bcast(config_array, root=0)
    return (config_array, min_error)


def update_error_worker(
    conf_file,
    num_vars,
    config_array,
    program,
    dependency_graph,
    ):

# TODO: update error vector based on the increase of precision of vars

    min_error_index = 0
    min_error = 1000000  # some abitrary big value for error comparision
    min_error_j = 0
    min_error_cost = 1000000
    send_back_error = 0.00
    working_index = 0
    status = MPI.Status()
    working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG,
                                  status=status)

    # print("worker recv from %d to %d data %d Tag %d"%(0,mpi_rank,working_index,status.Get_tag()))

    while status.Get_tag() > 0:
        increase_list = get_group_byIndex(working_index,
                dependency_graph)

        # print('cal error ')
        # print(increase_list)
        # for j in range(1,3): # 1 2

        for index in increase_list:
            config_array[index] += 1

        write_conf(conf_file, config_array)
        send_back_error = run_program(program)

        for index in increase_list:
            config_array[index] -= 1

        mpi_comm.send(send_back_error, dest=0, tag=working_index)
        working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG,
                status=status)

    min_error = mpi_comm.bcast(min_error, root=0)
    config_array = mpi_comm.bcast(config_array, root=0)
    return (config_array, min_error)


def isolated_var_analysis_master(conf_file, program):
    original_array = read_conf(conf_file)
    result_array = [MAX_BITWIDTH] * len(original_array)  # Use MAX_BITWIDTH instead of hardcoded 24
    num_elements_sent = 0
    recv_element = 0

    for i in range(mpi_size - 1):
        if num_elements_sent < len(original_array):
            mpi_comm.send(i, dest=i + 1, tag=1)
            num_elements_sent += 1
        else:
            mpi_comm.send(0, dest=i + 1, tag=0)  # signal finish proc.

    for i in range(len(original_array)):  # mpi_here

        status = MPI.Status()
        recv_element = mpi_comm.recv(source=MPI.ANY_SOURCE,
                tag=MPI.ANY_TAG, status=status)

        index = status.Get_tag()
        dest_proc = status.Get_source()
        result_array[index] = recv_element

        # ~ print "recv from %d  to %d data %d"%(dest_proc,0,recv_element)

        if num_elements_sent < len(original_array):  # send more to available proc
            mpi_comm.send(num_elements_sent, dest=dest_proc, tag=1)

            # ~ print "send from %d  to %d data %d"%(0,dest_proc,num_elements_sent)

            num_elements_sent += 1
        else:
            mpi_comm.send(0, dest=dest_proc, tag=0)  # signal finish proc.

    return result_array


def isolated_var_analysis_worker(conf_file, program):

    original_array = read_conf(conf_file)
    result_array = [53] * len(original_array)
    working_index = 0
    status = MPI.Status()
    working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG,
                                  status=status)

    # print("worker recv from %d to %d data %d Tag %d"%(0,mpi_rank,working_index,status.Get_tag()))

    while status.Get_tag() > 0:
        precision_array = [MAX_BITWIDTH] * len(original_array)  # Use MAX_BITWIDTH instead of hardcoded 24
        write_conf(conf_file, precision_array)
        boundary = [2, MAX_BITWIDTH, (2 + MAX_BITWIDTH) // 2]  # Use MAX_BITWIDTH instead of 24
        while boundary[UPPER_BOUND] - boundary[LOWER_BOUND] != 1:
            precision_array[working_index] = boundary[AVERAGE]
            write_conf(conf_file, precision_array)
            if run_program(program) <= error_rate:
                boundary[UPPER_BOUND] = boundary[AVERAGE]
            else:
                boundary[LOWER_BOUND] = boundary[AVERAGE]
            boundary[AVERAGE] = (boundary[UPPER_BOUND]
                                 + boundary[LOWER_BOUND]) // 2
        if boundary[UPPER_BOUND] < lower_precision_bound:
            boundary[UPPER_BOUND] = lower_precision_bound
        send_back_result = boundary[UPPER_BOUND]

        # print("worker send from %d to %d data %d Tag %d"%(mpi_rank,0,send_back_result,working_index))

        mpi_comm.send(send_back_result, dest=0, tag=working_index)

        working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG,
                status=status)


# ~ def greedy_search_master(conf_file,program):

def refine_1st_master(
    current_conf,
    min_conf,
    conf_file,
    program,
    ):
    result_array = [24] * len(current_conf)
    num_elements_sent = 0
    recv_element = 0
    for i in range(mpi_size - 1):
        if num_elements_sent < len(current_conf):
            mpi_comm.send(i, dest=i + 1, tag=1)
            num_elements_sent += 1
        else:
            mpi_comm.send(0, dest=i + 1, tag=0)  # signal finish proc.

    for i in range(len(current_conf)):  # mpi_here

        status = MPI.Status()
        recv_element = mpi_comm.recv(source=MPI.ANY_SOURCE,
                tag=MPI.ANY_TAG, status=status)

        index = status.Get_tag()
        dest_proc = status.Get_source()
        result_array[index] = recv_element

                # ~ print "recv from %d  to %d data %d"%(dest_proc,0,recv_element)

        if num_elements_sent < len(current_conf):  # send more to available proc
            mpi_comm.send(num_elements_sent, dest=dest_proc, tag=1)

                        # ~ print "send from %d  to %d data %d"%(0,dest_proc,num_elements_sent)

            num_elements_sent += 1
        else:
            mpi_comm.send(0, dest=dest_proc, tag=0)  # signal finish proc.

    return result_array


def refine_1st_worker(
    current_conf,
    min_conf,
    conf_file,
    program,
    ):

    working_index = 0
    status = MPI.Status()
    working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG,
                                  status=status)

        # ~ print "worker recv from %d  to %d data %d  Tag %d"%(0,mpi_rank,working_index,status.Get_tag())

    while status.Get_tag() > 0:
        precision_array = list(current_conf)
        write_conf(conf_file, precision_array)
        boundary = [min_conf[working_index] - 1,
                    current_conf[working_index],
                    (current_conf[working_index]
                    + min_conf[working_index]) // 2]
        while boundary[UPPER_BOUND] - boundary[LOWER_BOUND] != 1:
            precision_array[working_index] = boundary[AVERAGE]
            write_conf(conf_file, precision_array)
            if run_program(program) <= error_rate:
                boundary[UPPER_BOUND] = boundary[AVERAGE]
            else:
                boundary[LOWER_BOUND] = boundary[AVERAGE]
            boundary[AVERAGE] = (boundary[UPPER_BOUND]
                                 + boundary[LOWER_BOUND]) // 2
        if boundary[UPPER_BOUND] < lower_precision_bound:
            boundary[UPPER_BOUND] = lower_precision_bound
        send_back_result = boundary[UPPER_BOUND]

                # ~ print "worker send from %d  to %d data %d  Tag %d"%(mpi_rank,0,send_back_result,working_index)

        mpi_comm.send(send_back_result, dest=0, tag=working_index)

        working_index = mpi_comm.recv(source=0, tag=MPI.ANY_TAG,
                status=status)


def greedy_search_master(conf_file, program, target_file):

# TODO: search from min_conf, increase each vars a time so that the error_Reduced is maximum....

    global target_result
    global current_error
    global error_reduced  # for debugging purpose
    global total_num_var
    dependency_graph = build_dependency_path('dependency_graph.txt')

    target_result = read_target(target_file)
    target_result = mpi_comm.bcast(target_result, root=0)
    if DEBUG:
        print(target_result)
    if os.path.exists('log.txt'):
        os.remove('log.txt')
    if DEBUG:
        print('isolated_var_analysis ---------')
    mpi_comm.Barrier()

    min_conf = isolated_var_analysis_master(conf_file, program)

    # pass min_conf, save time
# ....min_conf = [5, 6, 15, 7, 18, 4, 4, 10, 15, 4, 4, 4, 16, 4, 4, 4, 16, 4, 4, 4, 4, 4, 8, 4, 9, 9, 10, 9, 11, 30]
    # pass min_conf of step 2
    # min_conf =

    mpi_comm.Barrier()

    error_reduced = [0.00] * len(min_conf)
    result_precision = [24] * len(min_conf)
    current_conf = list(min_conf)
    total_num_var = len(min_conf)
    if DEBUG:
        print('min_conf found ------------')
        print(min_conf)
    min_conf = mpi_comm.bcast(min_conf, root=0)

    write_conf(conf_file, min_conf)
    current_error = run_program(program)
    while current_error > error_rate:
        (current_conf, current_error) = update_error_master(conf_file,
                len(min_conf), current_conf, program, dependency_graph)

        # update_cost(precision_array)....

        write_log(current_conf, -1, [str(current_error)])
        mpi_comm.Barrier()

        # barrier here

        # print('write log ')

        if DEBUG:
            print('step2 finished ')

    global stop_condition
    stop_condition = False

    previous_satisfied_conf = []  # keep track of the last conf_ to validate the stop condition
    while not stop_condition:

###################################

        min_conf = refine_1st_master(current_conf, min_conf, conf_file,
                program)
        if DEBUG:
            print('######################')
            print('refine 1pass ' + str(min_conf))

        error_reduced = [0.00] * len(min_conf)
        result_precision = [24] * len(min_conf)
        current_conf = list(min_conf)
        total_num_var = len(min_conf)
        min_conf = mpi_comm.bcast(min_conf, root=0)

        write_conf(conf_file, min_conf)
        current_error = run_program(program)

#                if current_error<= error_rate:
#                        break

        while current_error > error_rate:
            (current_conf, current_error) = \
                update_error_master(conf_file, len(min_conf),
                                    current_conf, program,
                                    dependency_graph)

                # update_cost(precision_array)

            write_log(current_conf, -1, [str(current_error)])
            mpi_comm.Barrier()

                # barrier here
                # barrier here

        if sum(current_conf) == sum(previous_satisfied_conf):  # stop condition.
            stop_condition = True
            if DEBUG:
                print('current error ' + str(current_error))

        previous_satisfied_conf = list(current_conf)  # update the last conf

        stop_condition = mpi_comm.bcast(stop_condition, root=0)
        if DEBUG:
            print('refine 2v pass ' + str(current_conf))

        # ############################################333

        if DEBUG:
            print('end of searching ')

  #      print "trying to refine result "
# ....current_conf = refine_result (conf_file, len(min_conf),current_conf,program)
    print(str(current_conf))
    write_log(current_conf, -2, ['------Final result-------'])


# ~ #....write_conf(conf_file, original_array)........

def greedy_search_worker(conf_file, program):

# TODO: search from min_conf, increase each vars a time so that the error_Reduced is maximum....

    global target_result
    global current_error
    global total_num_var
    global error_reduced  # for debugging purpose
    if DEBUG:
        print('worker launched %s' % mpi_name)
    min_conf = []
    current_conf = []
    dependency_graph = build_dependency_path('dependency_graph.txt')
    target_result = mpi_comm.bcast(target_result, root=0)
    mpi_comm.Barrier()
    isolated_var_analysis_worker(conf_file, program)
    mpi_comm.Barrier()
    min_conf = mpi_comm.bcast(min_conf, root=0)
    current_conf = min_conf
    total_num_var = len(min_conf)
    write_conf(conf_file, min_conf)
    current_error = run_program(program)
    while current_error > error_rate:
        (current_conf, current_error) = update_error_worker(conf_file,
                len(min_conf), current_conf, program, dependency_graph)
        mpi_comm.Barrier()

    global stop_condition
    stop_condition = False
    while not stop_condition:

        # ##############################

        refine_1st_worker(current_conf, min_conf, conf_file, program)

        min_conf = mpi_comm.bcast(min_conf, root=0)
        current_conf = min_conf
        total_num_var = len(min_conf)
        write_conf(conf_file, min_conf)
        current_error = run_program(program)

 #               if current_error <= error_rate:
 #                       break

        while current_error > error_rate:
            (current_conf, current_error) = \
                update_error_worker(conf_file, len(min_conf),
                                    current_conf, program,
                                    dependency_graph)
            mpi_comm.Barrier()

                # #########################################

        stop_condition = mpi_comm.bcast(stop_condition, root=0)


def run_program(program):

# ....output = subprocess.Popen(['sh', 'run_lbm_mpfr.sh'], stdout=subprocess.PIPE).communicate()[0]

    output = subprocess.Popen([program, '%s'%(SEED_NUMBER)],
                              stdout=subprocess.PIPE).communicate()[0]

    # return float(output)

    floating_result = parse_output(output)

    # ~ floating_result = [float(output)]

    return check_output(floating_result, target_result)


def check_output(floating_result, target_result):
    # Updated to support different error metrics
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
            line.replace(' ', '')

            # remove unexpected space

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
            line.replace(' ', '')

            # remove unexpected space

            array = line.split(',')
            for target in array:
                try:
                    if len(target) > 0 and target != '\n':
                        list_target.append(float(target))
                except:
                    print('Failed to parse target file')
    return list_target


# done

def get_group_byIndex(current_index, dependency_graph):

# TODO: Return a group of indexes of vars associated with current_index as a result of dependency_graph....
## all indices will need to be reduced by 1. as index 0 is reserved for all tempvars

    result = []
    if current_index >= total_num_var:  # specific case, return all vars as a group
        result = range(total_num_var)
    else:
        result.append(current_index)
        if dependency_graph.has_key(str(current_index)):
            for item in dependency_graph.get(str(current_index)):
                result.append(int(item))
    return result


# Done

def build_dependency_path(graph_file):

    # TODO: read the graph file in format : destination <--- list of vars that dest depends on
    # for each var, construct a path, trace from that var until we find no reachable vars.
    # to prevent infinite loop, must add a group = all vars

    graph_nodes = []
    reverse_graph_dict = {}
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

                # else = end of path
        # remove key in new_node_list if it has

        if key in new_node_list:
            new_node_list.remove(key)
        reverse_graph_dict[key] = new_node_list

# ....print reverse_graph_dict

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
    global MAX_BITWIDTH

    parser = argparse.ArgumentParser(description="MPI version of greedy search for precision analysis")
    
    # Required arguments
    parser.add_argument("seed_number", type=int, help="Seed number for random input generator")
    parser.add_argument("program", help="Program name (without .sh extension)")
    
    # Optional arguments
    parser.add_argument("--metric", choices=["sqnr", "avg_abs"], default="sqnr",
                       help="Error metric to use (sqnr or avg_abs)")
    parser.add_argument("--error", type=float, default=1e-5,
                       help="Error rate threshold (default: 1e-5)")
    parser.add_argument("--max-bitwidth", type=int, default=53,
                       help="Maximum bitwidth to consider in the search (default: 53)")
    
    args = parser.parse_args(argv)
    
    # Set global variables based on arguments
    SEED_NUMBER = args.seed_number
    program = './' + args.program + '.sh'
    config_file = 'config_file.txt'
    binary_file = args.program
    target_file = 'target.txt'
    
    # Set parameters from command line
    ERROR_METRIC = args.metric
    error_rate = args.error
    MAX_BITWIDTH = args.max_bitwidth
    
    if mpi_size == 1:
        print("Error: This program requires multiple MPI processes")
        return
    
    # Print configuration information on rank 0
    if mpi_rank == 0:
        print("-"*80)
        print("MPI Parallel Precision Analysis")
        print("Program: ", binary_file)
        print("MPI Size: ", mpi_size)
        print("Error rate: ", error_rate)
        print("Error metric: ", ERROR_METRIC)
        print("Max bitwidth: ", MAX_BITWIDTH)
        print("-"*80)
    
    new_program_path = 'mpi_data_' + str(mpi_rank) \
        + program.replace('./', '/')
    new_config_file = 'mpi_data_' + str(mpi_rank) + '/' + config_file
    shutil.rmtree(os.path.dirname(new_program_path), ignore_errors=True)
    os.makedirs(os.path.dirname(new_program_path))
    shutil.copy(config_file, os.path.dirname(new_program_path))
    shutil.copy(argv[1] + '.sh', os.path.dirname(new_program_path))
    shutil.copy(binary_file, os.path.dirname(new_program_path))

    mpi_comm.Barrier()
    if mpi_rank == 0:  # master
        greedy_search_master(new_config_file, new_program_path,
                             target_file)
    else:
        greedy_search_worker(new_config_file, new_program_path)


        # build_dependency_path('dependency_graph.txt')

if __name__ == '__main__':
    main(sys.argv[1:])
