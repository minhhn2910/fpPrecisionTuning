#!/usr/bin/python
import sys
import subprocess
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
	#print zip (*result)	
	print "min avg exponent" + str(map(min,zip(*result)))
	print "max avg exponent" + str(map(max,zip(*result)))

if __name__ == '__main__':
    main(sys.argv[1:])	
