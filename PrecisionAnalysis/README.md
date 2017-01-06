## Requirements:
1. Python 2.6 or 2.7
2. A working version of mpi installed 
3. mpi4py [Download and install guide](http://mpi4py.readthedocs.io/en/stable/install.html)

***

##Usage: 

###greedy_search_mpi.py

./greedy_search_mpi.py is used to search for required precision (without randomizing inputs & statistics guided refining process).

You can modify the variable `error_rate` at the beginning of the code to change the expected output quality. 

`chmod +x ./greedy_search_mpi.py`

run `mpirun -np 1 ./greedy_search_mpi.py` to see usage

mpirun -np [number_of_threads] ./search.py [seed_number] [program_name]

example: run the script with 4 threads, 1 master and 3 workers, searching on the program name test_mpfr.

`mpirun -np 4 ./search.py 123 test_mpfr`

Seed_number is unused for regular programs.
It will be used and this script will be automatically called when we are running statistics guided refining process (statistics_guided_search.py). (seed_number) will be passed to the program to generate random inputs.

###statistics_guided_search.py

You can modify TARGET_SQNR to change the expected SQNR. Other variable at the beginning of the code can also changed, please refer to the comments in the code for more information

`chmod +x ./statistics_guided_search.py`

`./statistics_guided_search.py original_version mpfr_version`

example: run the precision tuning tool with statistics guided refinement process, float or double version = test_program. mpfr version = test_mpfr:

`./statistics_guided_search.py test_program test_mpfr`

***

##Important

This guide may not be completed and easy to setup on your machine. In any case, please don't hesitate to open issues here or contact me at minhhn2910(at)gmail.com for support.
