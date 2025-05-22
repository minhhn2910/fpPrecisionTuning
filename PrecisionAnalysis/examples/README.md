## To run the search on provided example:

```
python statistics_guided_search.py examples/test examples/test_mpfr
```

## Usage Documentation

```
python statistics_guided_search.py --help
```

### Parameters:
- `ORIGINAL_PROGRAM`: Path to the original reference program
- `MPFR_PROGRAM`: Path to the MPFR version of the program

### Optional Arguments:
- `--metric {sqnr,avg_abs}`: Error metric to use (default: avg_abs)
- `--target-sqnr VALUE`: Target SQNR (default: 1e-5)
- `--target-avg-abs-error VALUE`: Target average absolute error (default: 1e-4)
- `--num-procs N`: Number of processes to use (default: 8)
- `--max-bitwidth N`: Maximum bitwidth for search (default: 53)
- `--percentile-guided`: Use worse 5% percentile error instead of average error as the final target of the search
- `--test-range N`: Number of random inputs for statistics during search (default: 500)
- `--initial-seed N`: Initial seed for search (default: 32)
- `--no-after-search-test`: Disable final testing
- `--after-search-test-range N`: Number of random inputs for final test (default: 5000)

### Example:
```
(SQNR 50Db) 
python statistics_guided_search.py examples/test examples/test_mpfr --metric sqnr --target-sqnr 1e-5 --num-procs 4

(Absolute error 5e-4, 8 parallel processes)
python statistics_guided_search.py examples/test examples/test_mpfr --metric avg_abs --target-avg-abs-error 5e-4 --num-procs 8
```

