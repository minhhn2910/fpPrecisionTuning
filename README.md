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
