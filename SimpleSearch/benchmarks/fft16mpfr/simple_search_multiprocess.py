#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Python simplified version of greedy search. Assume that the program outputs directly to stdout.
This version is a blackbox sequential search for simple programs to synthesize on FPGA
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
import tempfile # Added for temporary directories
#from mpi4py import MPI
LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2
DEBUG = False

# Add this global variable for multiprocessing
NUM_PROCESSES = max(1, mp.cpu_count() - 1)  # Use all but one CPU

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

# updated = []

# for simplicity, define target here

lower_precision_bound = 2

minimum_cost = 1000000  # some abitrary big value for cost comparision


# minimum_configurations = [] #result of minimum precisions configurations

# Add this new global variable near the other globals
ERROR_METRIC = "avg_abs"  # Default metric is average absolute error
MAX_BITWIDTH = 53      # Default maximum bitwidth

# Store absolute paths for worker processes
# These will be set in functions that prepare for multiprocessing
_ABS_PROGRAM_PATH = None
_ABS_BINARY_PATH = None
_ABS_TARGET_PATH = None

def _run_program_in_worker(local_script_name, seed_num, current_target_result, current_error_metric):
    """
    Helper function to run the program within a worker's isolated directory.
    Uses passed-in target_result and error_metric instead of global.
    """
    # Execute the local copy of the script
    # The script itself will cd to its own directory, where config_file.txt and target.txt (copied) are
    process = subprocess.Popen(
        ['./' + local_script_name, '%s' % seed_num],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, # Capture stderr for debugging
        cwd="." # Ensure it runs in the current (worker's temp) directory
    )
    output, err = process.communicate()

    if process.returncode != 0:
        print(f"Worker error: Script {local_script_name} failed. stderr: {err.decode('utf-8')}")
        # Handle error appropriately, e.g., return a high error value or raise exception
        return float('inf') # Or some other indicator of failure

    output = output.decode('utf-8')
    floating_result = parse_output(output)
    # Pass target_result and error_metric directly to check_output
    return check_output_worker(floating_result, current_target_result, current_error_metric)

def check_output_worker(floating_result, target_res, error_metric_val):
    """
    A version of check_output that takes target_result and error_metric as arguments.
    """
    if len(floating_result) != len(target_res):
        print('Error : floating result has length: %s while target_result has length: %s' \
            % (len(floating_result), len(target_res)))
        print(floating_result)
        return float('inf') # Indicate a significant error

    if error_metric_val.lower() == "avg_abs":
        abs_error_sum = 0.00
        for i in range(len(floating_result)):
            abs_error_sum += abs(floating_result[i] - target_res[i])
        if len(floating_result) == 0: return float('inf')
        return abs_error_sum / len(floating_result)
    else:  # Default: "sqnr"
        signal_sqr = 0.00
        error_sqr = 0.00
        for i in range(len(floating_result)):
            signal_sqr += target_res[i] ** 2
            error_sqr += (floating_result[i] - target_res[i]) ** 2

        sqnr = 0.00
        if error_sqr != 0.00:
            sqnr = signal_sqr / error_sqr
        if sqnr != 0:
            return 1.0 / sqnr
        else:
            # Return a large error if error_sqr is 0 but signal_sqr is not (perfect match implies large SQNR, small 1/SQNR)
            # If both are zero, it's tricky. If signal is zero, any non-zero output is infinite error.
            # If error_sqr is zero, it means perfect match. 1/SQNR should be very small.
            # The original code returns 0.00 if sqnr is 0. This means infinite error.
            # If error_sqr is 0 (perfect match), sqnr is infinite, 1/sqnr is 0.
            # If error_sqr is non-zero and signal_sqr is 0, sqnr is 0, 1/sqnr is large (handled by 0.00 return).
            # This part seems okay: if sqnr is 0 (due to error_sqr being large or signal_sqr being 0 and error_sqr > 0),
            # it returns 0.00, which is treated as a large error by the calling logic (error > error_rate).
            # If error_sqr is 0.00 (perfect match), then sqnr is inf, 1.0/sqnr is 0.
            if error_sqr == 0.00 and signal_sqr == 0.00: # Both zero, perfect match for zero signal
                 return 0.00 # Smallest error
            elif error_sqr == 0.00 and signal_sqr != 0.00: # Perfect match for non-zero signal
                 return ZERO_error_rate / 10 # Return a very small error, smaller than ZERO_error_rate
            else: # error_sqr > 0
                 return float('inf') # Large error if SQNR is zero due to issues


def _worker_isolated_var_analysis(args_tuple):
    """
    Worker function for isolated_var_analysis.
    Each worker operates in its own temporary directory.
    """
    (
        working_index, num_total_vars,
        abs_program_path, abs_binary_path, abs_target_path,
        current_max_bitwidth, current_error_rate, current_lower_precision_bound,
        current_seed_number, current_target_result, current_error_metric
    ) = args_tuple

    worker_temp_dir = tempfile.mkdtemp(prefix=f"iso_worker_{working_index}_")
    original_cwd = os.getcwd()
    
    try:
        os.chdir(worker_temp_dir)

        # Copy necessary files to the worker's temporary directory
        local_program_script_name = os.path.basename(abs_program_path)
        local_binary_name = os.path.basename(abs_binary_path)

        shutil.copy(abs_program_path, local_program_script_name)
        os.chmod(local_program_script_name, 0o755) # Ensure script is executable
        shutil.copy(abs_binary_path, local_binary_name)
        shutil.copy(abs_target_path, "target.txt") # Assumed name by the script/binary

        # Worker's local version of write_conf
        def local_write_conf_to_cwd(arr):
            write_conf('config_file.txt', arr) # Writes to worker_temp_dir/config_file.txt

        # Core logic for this working_index
        # This precision_array is specific to this task, varying only one bitwidth
        precision_config_for_task = [current_max_bitwidth] * num_total_vars
        
        # Binary search for the precision of the current variable
        boundary = [2, current_max_bitwidth, (2 + current_max_bitwidth) // 2]
        
        # Initial full precision array for this task (only working_index will change)
        # The original code has a write_conf(conf_file, precision_array) before the loop over i
        # and then precision_array = [MAX_BITWIDTH] * len(original_array) inside the loop over i.
        # This means each task starts with MAX_BITWIDTH for all variables, then tunes one.

        while boundary[UPPER_BOUND] - boundary[LOWER_BOUND] > 1: # Adjusted condition for typical binary search
            precision_config_for_task[working_index] = boundary[AVERAGE]
            local_write_conf_to_cwd(precision_config_for_task)
            
            # Use the worker-specific run_program and check_output
            error_val = _run_program_in_worker(local_program_script_name, current_seed_number, current_target_result, current_error_metric)

            if error_val <= current_error_rate:
                boundary[UPPER_BOUND] = boundary[AVERAGE]
            else:
                boundary[LOWER_BOUND] = boundary[AVERAGE]
            
            # Ensure average calculation doesn't lead to infinite loop if bounds are adjacent
            if boundary[UPPER_BOUND] - boundary[LOWER_BOUND] <= 1:
                break
            boundary[AVERAGE] = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND]) // 2
        
        # The result is typically the upper bound if it met the criteria, or lower bound + 1
        final_precision = boundary[UPPER_BOUND]
        # Re-check the chosen upper_bound if it wasn't the last one tested
        precision_config_for_task[working_index] = final_precision
        local_write_conf_to_cwd(precision_config_for_task)
        error_val_at_final_precision = _run_program_in_worker(local_program_script_name, current_seed_number, current_target_result, current_error_metric)

        if error_val_at_final_precision > current_error_rate:
            # If upper_bound fails, it means we need one more bit, but only if it's not already max
            # This case should ideally be handled by the binary search logic ending on a valid UPPER_BOUND
            # or LOWER_BOUND being the highest precision that failed.
            # If UPPER_BOUND is the result of the binary search, it should be the lowest that passed.
            # If all failed, UPPER_BOUND would remain MAX_BITWIDTH.
            # If the loop condition is `while hi - lo != 1`, then `hi` is the lowest passing.
            # If `hi` fails, then `lo + 1` (which is `hi`) is the one.
            # Let's assume boundary[UPPER_BOUND] is the correct one from the loop.
            # If it still fails, it implies something is wrong or no precision works.
            # The original code does not have this re-check, it just takes boundary[UPPER_BOUND].
            pass


        if final_precision < current_lower_precision_bound:
            final_precision = current_lower_precision_bound
            
        return final_precision

    except Exception as e:
        print(f"Error in worker for index {working_index}: {e}")
        # Return a value indicating failure, e.g., MAX_BITWIDTH, so it doesn't break the flow
        # but signals that this path might not be optimizable or had an issue.
        return current_max_bitwidth 
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(worker_temp_dir)

def _worker_refine_1st(args_tuple):
    """
    Worker function for refine_1st.
    Each worker operates in its own temporary directory.
    """
    (
        working_index,
        initial_precision_for_var, # current_conf[working_index]
        min_precision_for_var,     # min_conf[working_index]
        base_config_array_list,    # list(current_conf) for context
        # Paths and execution parameters
        abs_program_path, abs_binary_path, abs_target_path,
        current_seed_number, current_target_result_data, current_error_metric_str,
        current_error_rate_val, current_lower_precision_bound_val, num_total_vars_for_worker
    ) = args_tuple

    worker_temp_dir = tempfile.mkdtemp(prefix=f"ref1_worker_{working_index}_")
    original_cwd = os.getcwd()

    try:
        os.chdir(worker_temp_dir)

        local_program_script_name = os.path.basename(abs_program_path)
        local_binary_name = os.path.basename(abs_binary_path)

        shutil.copy(abs_program_path, local_program_script_name)
        os.chmod(local_program_script_name, 0o755)
        shutil.copy(abs_binary_path, local_binary_name)
        shutil.copy(abs_target_path, "target.txt")

        def local_write_conf_to_cwd(arr):
            write_conf('config_file.txt', arr)

        precision_array_for_task = list(base_config_array_list) # Worker's copy

        # Binary search logic from refine_1st for precision_array_for_task[working_index]
        boundary = [
            min_precision_for_var - 1, # LOWER_BOUND
            initial_precision_for_var, # UPPER_BOUND
            (initial_precision_for_var + min_precision_for_var) // 2 # AVERAGE
        ]
        
        # Original loop condition: while boundary[UPPER_BOUND] - boundary[LOWER_BOUND] != 1:
        # This loop continues as long as there's more than one step between upper and lower.
        # It stops when upper_bound = lower_bound + 1.
        while boundary[UPPER_BOUND] - boundary[LOWER_BOUND] != 1:
            # Prevent getting stuck if average doesn't change lower_bound
            if boundary[AVERAGE] <= boundary[LOWER_BOUND] and boundary[AVERAGE] < boundary[UPPER_BOUND]:
                 boundary[AVERAGE] = boundary[LOWER_BOUND] + 1 # Force progress if possible
            
            # If average calculation makes it equal to upper bound, and lower is different,
            # it means we might be stuck if lower bound doesn't move.
            # However, the primary check is if bounds are not adjacent.
            if boundary[AVERAGE] >= boundary[UPPER_BOUND] and boundary[AVERAGE] > boundary[LOWER_BOUND]:
                boundary[AVERAGE] = boundary[UPPER_BOUND] -1 # Force progress if possible

            if boundary[AVERAGE] <= boundary[LOWER_BOUND] or boundary[AVERAGE] >= boundary[UPPER_BOUND] : # bounds crossed or avg is out of range
                 if boundary[UPPER_BOUND] > boundary[LOWER_BOUND] +1 : # if there is still space
                     # reset average to middle carefully
                     boundary[AVERAGE] = boundary[LOWER_BOUND] + (boundary[UPPER_BOUND] - boundary[LOWER_BOUND]) // 2
                     if boundary[AVERAGE] <= boundary[LOWER_BOUND]: # if middle is still low, nudge up
                         boundary[AVERAGE] = boundary[LOWER_BOUND] + 1
                 else: # no space left or bounds are problematic
                     break


            precision_array_for_task[working_index] = boundary[AVERAGE]
            local_write_conf_to_cwd(precision_array_for_task)
            
            error_val = _run_program_in_worker(
                local_program_script_name, current_seed_number,
                current_target_result_data, current_error_metric_str
            )

            if error_val <= current_error_rate_val:
                boundary[UPPER_BOUND] = boundary[AVERAGE]
            else:
                boundary[LOWER_BOUND] = boundary[AVERAGE]
            
            # Recalculate average for next iteration
            # Ensure average calculation doesn't lead to infinite loop if bounds are adjacent
            if boundary[UPPER_BOUND] - boundary[LOWER_BOUND] <= 1:
                break
            
            new_average = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND]) // 2
            boundary[AVERAGE] = new_average
        
        send_back_result = boundary[UPPER_BOUND]

        if send_back_result < current_lower_precision_bound_val:
            send_back_result = current_lower_precision_bound_val
        
        return send_back_result

    except Exception as e:
        print(f"Error in worker for refine_1st index {working_index}: {type(e).__name__} {e}")
        return initial_precision_for_var # Fallback to non-optimized value for this var
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(worker_temp_dir)

def _worker_update_error_eval(args_tuple):
    """
    Worker function for the first loop in update_error.
    Calculates error for a modified configuration.
    """
    (
        working_index,
        base_config_array_list, # Original config_array for this update_error call
        dependency_graph_data,
        current_total_num_var_val,
        # Paths and execution parameters
        abs_program_path, abs_binary_path, abs_target_path,
        current_seed_number, current_target_result_data, current_error_metric_str
    ) = args_tuple

    worker_temp_dir = tempfile.mkdtemp(prefix=f"updErr_worker_{working_index}_")
    original_cwd = os.getcwd()

    try:
        os.chdir(worker_temp_dir)

        local_program_script_name = os.path.basename(abs_program_path)
        local_binary_name = os.path.basename(abs_binary_path)

        shutil.copy(abs_program_path, local_program_script_name)
        os.chmod(local_program_script_name, 0o755)
        shutil.copy(abs_binary_path, local_binary_name)
        shutil.copy(abs_target_path, "target.txt")

        def local_write_conf_to_cwd(arr):
            write_conf('config_file.txt', arr)

        iter_config_array = list(base_config_array_list) # Worker's copy
        
        # Use the modified get_group_byIndex
        increase_list = get_group_byIndex(working_index, dependency_graph_data, current_total_num_var_val)

        for index_to_inc in increase_list:
            if 0 <= index_to_inc < len(iter_config_array): # Boundary check
                iter_config_array[index_to_inc] += 1
            else:
                # This case should ideally not happen if get_group_byIndex is correct
                print(f"Warning: index {index_to_inc} out of bounds for config_array in worker {working_index}")


        local_write_conf_to_cwd(iter_config_array)
        
        error_val = _run_program_in_worker(
            local_program_script_name, current_seed_number,
            current_target_result_data, current_error_metric_str
        )
        return error_val

    except Exception as e:
        print(f"Error in worker for update_error_eval index {working_index}: {e}")
        return float('inf') # Return a high error on failure
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(worker_temp_dir)

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
    line.replace(' ', '')
    line.replace('\n', '')

        # remove unexpected space

    array = line.split(',')

#       print array

    for target in array:
        try:
            if len(target) > 0 and target != '\n':
                list_target.append(float(target))
        except:

                        # print "Failed to parse output string"

            continue

#               print list_target

    return list_target


def update_error(
    conf_file,
    num_vars,
    config_array,
    program,
    dependency_graph,
    ):

# TODO: update error vector based on the increase of precision of vars

    global error_reduced # This will be populated by worker results
    global current_error # This is the error *before* this update_error call
    # Ensure error_reduced is initialized correctly for num_vars
    if len(error_reduced) != num_vars:
        error_reduced = [0.00] * num_vars

    min_error_index = 0
    min_error = 1000000  # some abitrary big value for error comparision
    # min_error_j = 0 # This variable was unused
    min_error_cost = 1000000

    # num_elements_sent = 0 # Unused mpi variable
    # recv_element = 0.00 # Unused mpi variable

    # Parallelize this loop
    tasks_for_pool = []
    for i in range(num_vars):
        task_data = (
            i,
            list(config_array), # Pass a copy of the current config_array
            dependency_graph,   # Pass dependency_graph
            num_vars,           # Pass num_vars for get_group_byIndex logic
            _ABS_PROGRAM_PATH, _ABS_BINARY_PATH, _ABS_TARGET_PATH,
            SEED_NUMBER, target_result, ERROR_METRIC
        )
        tasks_for_pool.append(task_data)

    if DEBUG:
        print(f"Starting update_error calculation with {NUM_PROCESSES} processes for {num_vars} variables.")

    with mp.Pool(processes=NUM_PROCESSES) as pool:
        # Results will be ordered corresponding to tasks (i.e., working_index 0 to num_vars-1)
        calculated_errors = pool.map(_worker_update_error_eval, tasks_for_pool)
    
    for i in range(num_vars):
        error_reduced[i] = calculated_errors[i]
    # End of parallelized part for error calculation

    for i in range(num_vars):  # This loop is for finding the minimum, sequential and fast
        index = i
        if error_reduced[index] < min_error:
            min_error_index = index
            min_error = error_reduced[index]
            # Use modified get_group_byIndex, passing num_vars
            increase_list = get_group_byIndex(index, dependency_graph, num_vars)
            min_error_cost = len(increase_list)
        elif error_reduced[index] == min_error:
            increase_list = get_group_byIndex(index, dependency_graph, num_vars)
            if len(increase_list) < min_error_cost:
                min_error_index = index
                # min_error = error_reduced[index] # min_error is already this value
                min_error_cost = len(increase_list)

    # The `current_error` here refers to the error *before* this call to update_error.
    # The `min_error` found is the minimum error *after* one hypothetical increment.
    # The original logic compared `min_error` (an error from a hypothetical increment)
    # with `current_error` (error of the config *before* any increment in this function).
    # This comparison seems to be for detecting if no single increment reduces error.
    # Let's assume `current_error` is the global one reflecting the state before this function.
    
    # Check if the best hypothetical increment still results in the same error as the input configuration's error
    # This implies no single +1 step (as defined by get_group_byIndex) improved things.
    # Note: The global `current_error` should be the error of the `config_array` *before* this function.
    # The `min_error` is the error if we *were* to apply the best increment.
    
    # The original code had: if min_error == current_error:
    # This `current_error` is the global one, which is the error of the `config_array` passed to this function.
    # If the best possible single increment (leading to `min_error`) results in the same error value
    # as the original `config_array`, it means that increment didn't help.
    if min_error >= globals()['current_error']: # Access global current_error for comparison
        min_error_index = num_vars + 1  # Signal to increase all vars
        break_tie_conf_array = []
        for item_val in config_array: # Iterate over values of config_array
            break_tie_conf_array.append(item_val + 1)
        # This write_conf and run_program happens in the main process context
        write_conf(conf_file, break_tie_conf_array)
        min_error = run_program(program) # This updates min_error to the error of the "all +1" config
                                         # And config_array itself is NOT YET MODIFIED for this "all +1" case.
                                         # The modification happens below using final_increase_list.

    if DEBUG:
        print('min error index ' + str(min_error_index))
    
    # Get the final list of indices to increment based on min_error_index
    # (which might be num_vars + 1 for the "all increment" case)
    final_increase_list = get_group_byIndex(min_error_index, dependency_graph, num_vars)
    
    for index_to_inc in final_increase_list:
        if 0 <= index_to_inc < len(config_array): # Boundary check
             config_array[index_to_inc] += 1
        # If min_error_index was num_vars + 1, get_group_byIndex returns range(num_vars),
        # so all valid indices in config_array are incremented.

    if DEBUG:
        print(error_reduced, min_error)
        print(config_array)

    # The returned min_error should be the error of the *newly modified* config_array.
    # If the "all +1" path was taken, min_error was already updated by run_program.
    # If a regular path (single group increment) was taken, min_error is the error_reduced[min_error_index].
    # The function should return the config_array and its corresponding error.
    # The `min_error` variable holds the correct error for the returned `config_array`.
    return (config_array, min_error)


def isolated_var_analysis(conf_file, program):
    original_array = read_conf(conf_file) # Read initial configuration
    num_vars = len(original_array)
    result_array = [MAX_BITWIDTH] * num_vars

    # Determine absolute paths for script, binary, and target.txt ONCE.
    # These are needed by workers to copy files.
    # `program` is like './prog.sh'.
    # `target.txt` is assumed to be in the same directory as the script.
    global _ABS_PROGRAM_PATH, _ABS_BINARY_PATH, _ABS_TARGET_PATH
    _ABS_PROGRAM_PATH = os.path.abspath(program)
    script_dir = os.path.dirname(_ABS_PROGRAM_PATH)
    binary_name_from_program = os.path.basename(program).replace('.sh', '')
    _ABS_BINARY_PATH = os.path.join(script_dir, binary_name_from_program)
    _ABS_TARGET_PATH = os.path.join(script_dir, "target.txt") # Assumes target.txt is with the script

    if not os.path.exists(_ABS_PROGRAM_PATH):
        print(f"Error: Program script not found at {_ABS_PROGRAM_PATH}")
        return result_array # or raise error
    if not os.path.exists(_ABS_BINARY_PATH):
        print(f"Error: Binary not found at {_ABS_BINARY_PATH}")
        return result_array # or raise error
    if not os.path.exists(_ABS_TARGET_PATH):
        print(f"Error: Target file not found at {_ABS_TARGET_PATH}")
        return result_array # or raise error

    # Prepare arguments for each task
    # Each task tuple: (working_index, num_total_vars,
    #                   abs_program_path, abs_binary_path, abs_target_path,
    #                   MAX_BITWIDTH, error_rate, lower_precision_bound,
    #                   SEED_NUMBER, target_result (data), ERROR_METRIC (string))
    tasks_for_pool = []
    for i in range(num_vars):
        task_data = (
            i, num_vars,
            _ABS_PROGRAM_PATH, _ABS_BINARY_PATH, _ABS_TARGET_PATH,
            MAX_BITWIDTH, error_rate, lower_precision_bound,
            SEED_NUMBER, target_result, ERROR_METRIC # Pass global data directly
        )
        tasks_for_pool.append(task_data)

    if DEBUG:
        print(f"Starting isolated_var_analysis with {NUM_PROCESSES} processes for {num_vars} variables.")

    with mp.Pool(processes=NUM_PROCESSES) as pool:
        # pool.map ensures results are ordered corresponding to tasks
        list_of_results_for_each_var = pool.map(_worker_isolated_var_analysis, tasks_for_pool)
    
    result_array = list(list_of_results_for_each_var)

    print("-"*80)
    print("Isolated var analysis result: ", result_array)
    print("-"*80)
    return result_array


def refine_1st(
    current_conf,
    min_conf,
    conf_file, # conf_file is mostly for context, workers use their own
    program,   # program script name
    ):
    # result_array = [MAX_BITWIDTH] * len(current_conf) # Initialize with a default
    # num_elements_sent = 0 # MPI related, unused
    # recv_element = 0 # MPI related, unused
    num_vars = len(current_conf)
    result_array = [0] * num_vars # Initialize appropriately

    tasks_for_pool = []
    for i in range(num_vars):
        task_data = (
            i, # working_index
            current_conf[i],
            min_conf[i],
            list(current_conf), # Pass a copy of the whole current_conf for context
            _ABS_PROGRAM_PATH, _ABS_BINARY_PATH, _ABS_TARGET_PATH,
            SEED_NUMBER, target_result, ERROR_METRIC,
            error_rate, lower_precision_bound, num_vars # Pass num_vars for worker, if needed
        )
        tasks_for_pool.append(task_data)

    if DEBUG:
        print(f"Starting refine_1st with {NUM_PROCESSES} processes for {num_vars} variables.")

    with mp.Pool(processes=NUM_PROCESSES) as pool:
        list_of_results = pool.map(_worker_refine_1st, tasks_for_pool)
    
    result_array = list(list_of_results)

    print("-"*80)
    print("Refine 1st result: ", result_array)
    print("-"*80)
    return result_array

def greedy_search(conf_file, program, target_file):

    global target_result
    global current_error
    global error_reduced  # for debugging purpose
    global total_num_var
    target_result = read_target(target_file)
    print("-"*80)
    print("Program: ", program)
    print("Target result: ", target_result)
    print("Error rate: ", error_rate)
    print("Error metric: ", ERROR_METRIC)
    print("Max bitwidth: ", MAX_BITWIDTH)
    print("Number of processes: ", NUM_PROCESSES)
    print("-"*80)
    if DEBUG:
        print(target_result)
    if os.path.exists('log.txt'):
        os.remove('log.txt')
    if DEBUG:
        print('isolated_var_analysis ---------')

    min_conf = isolated_var_analysis(conf_file, program)
    
    error_reduced = [0.00] * len(min_conf)
    result_precision = [MAX_BITWIDTH] * len(min_conf)
    current_conf = list(min_conf)
    total_num_var = len(min_conf)
        # Check if all items in min_conf are MAX_BITWIDTH
    if all(precision == MAX_BITWIDTH for precision in min_conf):
        print("-"*80)
        print("All variables require maximum precision. No optimization possible.")
        print("Exiting program.")
        print("-"*80)
        sys.exit(0)
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

###################################

        min_conf = refine_1st(current_conf, min_conf, conf_file,
                program)
        if DEBUG:
            print('######################')
            print('refine 1pass ' + str(min_conf))

        error_reduced = [0.00] * len(min_conf)
        result_precision = [MAX_BITWIDTH] * len(min_conf)
        current_conf = list(min_conf)
        total_num_var = len(min_conf)
        #min_conf = mpi_comm.bcast(min_conf, root=0)

        write_conf(conf_file, min_conf)
        current_error = run_program(program)

#                if current_error<= error_rate:
#                        break

        while current_error > error_rate:
            (current_conf, current_error) = \
                update_error(conf_file, len(min_conf),
                                    current_conf, program,
                                    dependency_graph)

                # update_cost(precision_array)

            write_log(current_conf, -1, [str(current_error)])
            #mpi_comm.Barrier()

                # barrier here
                # barrier here

        if sum(current_conf) == sum(previous_satisfied_conf):  # stop condition.
            stop_condition = True
            if DEBUG:
                print('current error ' + str(current_error))

        previous_satisfied_conf = list(current_conf)  # update the last conf

        #stop_condition = mpi_comm.bcast(stop_condition, root=0)
        if DEBUG:
            print('refine 2v pass ' + str(current_conf))

        # ############################################333

        if DEBUG:
            print('end of searching ')

  #      print "trying to refine result "
# ....current_conf = refine_result (conf_file, len(min_conf),current_conf,program)
    print(str(current_conf))
    write_log(current_conf, -2, ['------Final result-------'])


def run_program(program):

# ....output = subprocess.Popen(['sh', 'run_lbm_mpfr.sh'], stdout=subprocess.PIPE).communicate()[0]

    output = subprocess.Popen([program, '%s'%(SEED_NUMBER)],
                              stdout=subprocess.PIPE).communicate()[0]
    
    # Convert bytes to string in Python 3
    output = output.decode('utf-8')

    # return float(output)

    floating_result = parse_output(output)
    # check_output now uses global target_result and global ERROR_METRIC
    return check_output(floating_result, target_result)


def check_output(floating_result, target_result_data): # Modified to accept target_result_data
    # Use the global metric setting
    global ERROR_METRIC # ERROR_METRIC is fine as global here for the main thread's calls
                       # Workers will use the one passed to them or a worker-specific check_output

    if len(floating_result) != len(target_result_data): # Use passed target_result_data
        print('Error : floating result has length: %s while target_result has length: %s' \
            % (len(floating_result), len(target_result_data)))
        print(floating_result)
        return float('inf') # Indicate a significant error
    
    current_metric = ERROR_METRIC # Use the global for non-worker calls
    
    if current_metric.lower() == "avg_abs":
        # Calculate average absolute error
        abs_error_sum = 0.00
        for i in range(len(floating_result)):
            abs_error_sum += abs(floating_result[i] - target_result_data[i]) # Use passed target_result_data
        if len(floating_result) == 0: return float('inf')
        return abs_error_sum / len(floating_result)
    else:  # Default: "sqnr"
        # Original SQNR calculation
        signal_sqr = 0.00
        error_sqr = 0.00
        for i in range(len(floating_result)):
            signal_sqr += target_result_data[i] ** 2 # Use passed target_result_data
            error_sqr += (floating_result[i] - target_result_data[i]) ** 2 # Use passed target_result_data

        sqnr = 0.00
        if error_sqr != 0.00:
            sqnr = signal_sqr / error_sqr
        
        if sqnr != 0:
            return 1.0 / sqnr
        else:
            # Consistent with worker version for perfect match
            if error_sqr == 0.00 and signal_sqr == 0.00: 
                 return 0.00 
            elif error_sqr == 0.00 and signal_sqr != 0.00: 
                 return ZERO_error_rate / 10 
            else: 
                 return float('inf')


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

def get_group_byIndex(current_index, dependency_graph, num_vars_for_group): # Added num_vars_for_group
    result = []
    if current_index >= num_vars_for_group:  # specific case, return all vars as a group
        result = list(range(num_vars_for_group))
    else:
        result.append(current_index)
        if str(current_index) in dependency_graph:
            for item in dependency_graph.get(str(current_index)):
                result.append(int(item))
    return result


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
    global NUM_PROCESSES
    
    parser = argparse.ArgumentParser(description="Simplified version of greedy search for synthesizing FPGA programs")
    
    # Maintain backward compatibility with positional arguments
    parser.add_argument("seed_number", type=int, help="Seed number for random input generator")
    parser.add_argument("program", help="Program name (with or without path, without .sh extension)")
    parser.add_argument("error_metric", nargs='?', default="sqnr", 
                       help="Error metric to use (sqnr or avg_abs)")
    
    # Add new optional arguments
    parser.add_argument("--metric", choices=["sqnr", "avg_abs"], 
                       help="Error metric to use (overrides positional argument)")
    parser.add_argument("--error", type=float, 
                       help="Error rate threshold (e.g., 2.5e-10)")
    parser.add_argument("--max-bitwidth", type=int, default=53,
                       help="Maximum bitwidth to consider in the search (default: 53)")
    parser.add_argument("--processes", type=int, default=NUM_PROCESSES,
                       help=f"Number of processes to use (default: {NUM_PROCESSES})")
    
    args = parser.parse_args(argv)
    
    # Set global variables based on arguments
    SEED_NUMBER = args.seed_number
    
    # Handle paths in the program argument
    program_path = os.path.dirname(args.program)
    program_base = os.path.basename(args.program)
    
    if program_path:
        # If program has a path component, use that directory for all files
        config_file = os.path.join(program_path, 'config_file.txt')
        target_file = os.path.join(program_path, 'target.txt')
        binary_file = program_base
        program = os.path.join(program_path, program_base + '.sh')
    else:
        # Original behavior for when no path is provided
        config_file = 'config_file.txt'
        target_file = 'target.txt'
        binary_file = args.program
        program = './' + args.program + '.sh'
    
    # Set max bitwidth from command line
    MAX_BITWIDTH = args.max_bitwidth
    
    # Set number of processes
    NUM_PROCESSES = args.processes
    
    # Check if the bash script exists, if not create it
    if not os.path.exists(program):
        # Ensure directory exists for program
        program_dir = os.path.dirname(program)
        if program_dir and not os.path.exists(program_dir):
            os.makedirs(program_dir, exist_ok=True)
            
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
    
    greedy_search(config_file, program, target_file)

if __name__ == '__main__':
    main(sys.argv[1:])
