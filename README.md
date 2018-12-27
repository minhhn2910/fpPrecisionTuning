# Floating point precision tuning using mpfr library and distributed search algorithm.
This project comprises 2 main tools: C2mpfr and DistributedSearch, both implemented in python.
There is no restriction on version of python. But this repo works best (tested) on Python 2.6 & 2.7
## C2mpfr
  Convert the original program written in C into the new version using MPFR library for arbitrary precision arithmetic.
  Go to c2mpfr/examples/README.md for information regarding using this tool.
## DistributedSearch
  Comprises the distributed algorithm using mpi to find the near-optimal precision for each floating-point variable of the given program.
  The searching script then will be used in the refining process to make the final output satisfy some given statistical features e.g. Average error over an input domain must be less than \epsilon.
  Go to PrecisionAnalysis/README.md for information regarding using this set of scripts.
## Publication

  Ho, N.M., Manogaran, E., Wong, W.F. and Anoosheh, A., 2017, January. Efficient floating point precision tuning for approximate computing. In Design Automation Conference (ASP-DAC), 2017 22nd Asia and South Pacific (pp. 63-68). IEEE.

## What's new
 2019: I updated the search algorithm to be used for general purpose without dependency to the c2mpfr tool. I also included some small programs converted to mpfr for testing of the search algorithm.
  
**Under SimpleSearch/ , there are two more versions:**

  * Parallel without the need for dependency_graph.txt

  * Sequential 1 click run. This is a very simple and useful version for small programs/bechmarks used for FPGA synthesis. Dependency is only python 2.x-3.x  

  * The two versions are included in each subfolder for each benchmark and are ready to run.
