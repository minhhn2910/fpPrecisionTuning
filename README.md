# Floating point precision tuning using mpfr library and distributed search algorithm.
This project comprises 2 main tools: C2mpfr and DistributedSearch, both implemented in python.
## C2mpfr
  Convert the original program written in C into the new version using MPFR library for arbitrary precision arithmetic.
## DistributedSearch
  Comprises the distributed algorithm using mpi to find the near-optimal precision for each floating-point variable of the given program.
  The searching script then will be used in the refining process to make the final output satisfy some given statistical features e.g. Average error over an input domain must be less than \epsilon. 
