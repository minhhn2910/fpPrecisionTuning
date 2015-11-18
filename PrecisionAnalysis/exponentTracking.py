#!/usr/bin/python
import sys
import subprocess
import numpy as np
from functools import partial
def parse_output(line):
	list_target = []
	array = line.replace(' ', '').replace('\n', '').split(',')
	for target in array:
		try:
			if len(target) > 0 and target != '\n':
				list_target.append(int(target))
		except:
			continue
	return list_target
	
def main(argv):
	if len(argv) != 2:
		print "usage ./exponentTracking.py number_of_inputs progname"
	program = './' + argv[1]
	num_testcases = int(argv[0])
	result = []
	for i in range(num_testcases):
		output = parse_output(subprocess.Popen([program, '%s'%(i)],stdout=subprocess.PIPE).communicate()[0])
		result.append(output)
	
	# np.percentile(sqnr_vector, PERCENTILE_VALUE)
	mapfunc20p = partial(np.percentile, q = 95)
	mapfunc80p = partial(np.percentile, q = 5)
	
	#print zip (*result)[0]
	#print zip(*result)
	print "5%% percentile " + str(map(int,map(mapfunc20p,zip(*result))))
	print "95%% percentile " + str(map(int,map(mapfunc80p,zip(*result))))
	print "min avg exponent " + str(map(min,zip(*result)))
	print "max avg exponent " + str(map(max,zip(*result)))
#SQNR_pecentile = np.percentile(sqnr_vector, PERCENTILE_VALUE)	
if __name__ == '__main__':
    main(sys.argv[1:])	
