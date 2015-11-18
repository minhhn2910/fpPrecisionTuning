#!/usr/bin/python
import sys
import random
import subprocess
import os
import os.path
#import ast
import json

configurations = []
permutations = []

def parse_result(result_path):
	global configurations
	global permutations
	with open(result_path) as result_file:	
		for line in result_file:
			str_array = line.split(':')
		#	print line
		#	print 
			
			if len(str_array) >=2:
				if "Loop" in str_array[0]:
					if "Final result" in str_array[2]:
						continue
					str_array[2].replace(' ','')
#					permutation_array = ast.literal_eval(str_array[2])
					permutation_array = json.loads(str_array[2])
					permutations.append(permutation_array)
					#print permutation_array
				if "Result" in str_array[0]:
					str_array[1].replace(' ','')
					#result = ast.literal_eval(str_array[1])
					result = json.loads(str_array[1])
					configurations.append(result)
					#print result
	post_processing()


def post_processing():
	global configurations
	global permutations
	costs = []
	frequency =[]
	minimum_cost = 10000
	minimum_configurations = []
	minimum_permutations = []
	for i in range(len(permutations)):
		temp = sum(configurations[i])
		if temp < minimum_cost:
			minimum_cost = temp
			#delete result list
			minimum_configurations = [] 
			minimum_permutations = []
			minimum_configurations.append(configurations[i])
			minimum_permutations.append(permutations[i])
		elif temp == minimum_cost:
			#append to result
			minimum_configurations.append(configurations[i])
			minimum_permutations.append(permutations[i])
		if temp in costs:
			frequency[costs.index(temp)]= frequency[costs.index(temp)] + 1
		else:
			costs.append(temp)
			frequency.append(1)

	print 'cost vector(sum of precisions): %s'	%(costs)
	print 'number of different costs : %s'%(len(costs))
	print 'frequency of the above cost vector: %s' %(frequency)
	print 'total local minimum configurations: ' + str(sum(frequency))	
	print 'minimum results :'
	for item in  minimum_configurations:
		print item
	print 'minimum visiting orders'
	for item in  minimum_permutations:
		print item
	
	statistic(costs, frequency)

def statistic(costs,frequency):
	print '--------------percentage presentation-----------'
	sum_all = sum(frequency)
	dict_percentage = {}
	percentage = []
	for i in range(len(frequency)):
		percentage.append(frequency[i]*100.0/float(sum_all))
		dict_percentage[costs[i]] = percentage[i]
		
		#print '%s  : %2.f '%(costs[i], percentage[i])
	top10 = 0.00
	top20 = 0.00
	i = 0
	for key in sorted(dict_percentage):		
		i = i+1
		if i <=10:
			top10 = top10 + dict_percentage[key]
		if i<=20:
			top20 = top20 + dict_percentage[key]
		print '%s  : %.2f '%(key, dict_percentage[key])
	print 'total percentage %.2f ' %(sum(percentage))
	print 'percentage of top 10 (sum = 228 -> 237) : %.2f'%(top10)
	print 'percentage of top 20 (sum = 228 -> 247) : %.2f'%(top20)
def main(argv):
	if len(argv) !=1 :
		print 'usage ./parse_result.py result.txt'
	else:
		parse_result(argv[0])



if __name__ == "__main__":
   main(sys.argv[1:])
