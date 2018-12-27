The two searching scripts are provided in each subfolder containing each benchmark.

You can run them directly using the `run.sh` and `run_mpi.sh` scripts. `run.sh` uses the sequential version of the search without dependency on mpi

To run the script, you need the mpfr version up and working. The binary files in each sub directory is compiled using `-lmpfr`, you can do the same on your machine. 

e.g. `./fft_mpfr.sh 123` will run the fft version with mantissa precision given in `config_file.txt` and a random seed of 123. the random seed must match the seed used to generate `target.txt` result version in float.

Summary, to run the example from scratch, dct.c for example:

**Step 1:** 

compile the original program to dct_float : `gcc dct.c -o dct_float`

**Step 2:**

generate the reference output : `./dct_float 123 > target.txt` , with 123 is the random seed used in `srand()` for generating inputs. In dct example we use fixed input so this number doesnt matter. It is included for compability in fft, iir and other benchmarks where we need to generate input randomly

**Step 3:**

Copy target.txt to the folder containing mpfr version. compile the mpfr version : `cd dct_mpfr ; gcc converted2mpfr.c -o dct_mpfr -lmpfr`

**Step 4:** 

run the search : `./run.sh` for sequential search or `./run_mpi.sh` for parallel search. Wait for a while, output  mantissa bitwidth will be printed out to stdout

