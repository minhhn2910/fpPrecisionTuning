Usage of c2mpfr tool :
```./c2mpfr.py [source file] [ignore_tempvar_flag]
```
e.g.
```./c2mpfr.py test.c
```
convert test.c into mpfr version, treating all temporary variables as 1 variable (sharing 1 precision)
```./c2mpfr.py test.c ignore
```
convert test.c into mpfr version, treating all temporary variables as double precision variables (their existence won't affect the final precision result of other variables. Their precision can be derived from precisions of other variables as well)
