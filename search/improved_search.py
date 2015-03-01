LOWER_BOUND = 0
UPPER_BOUND = 1
AVERAGE = 2

targets = range(4,64)
for target in targets:
	count =0
	boundary = [4,64,32]
	while (boundary[AVERAGE] != target):
		count = count + 1 
		if (boundary[AVERAGE] > target):
			boundary[UPPER_BOUND] = boundary[AVERAGE]
		elif (boundary[AVERAGE] < target):
			boundary[LOWER_BOUND] = boundary[AVERAGE]	
		boundary[AVERAGE] = (boundary[UPPER_BOUND] + boundary[LOWER_BOUND])/2
		if (boundary[UPPER_BOUND] - boundary[LOWER_BOUND]) == 1:
			if boundary[UPPER_BOUND] == target:
				boundary[AVERAGE] = boundary[UPPER_BOUND] 
			if boundary[LOWER_BOUND] == target:
				boundary[AVERAGE] = boundary[LOWER_BOUND] 
			break
	print "found "
	print boundary
	print ('target %s  times %s  '%(target,count))
