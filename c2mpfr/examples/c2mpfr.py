#!/usr/bin/python
#------------------------------------------------------------------------------
# pycparser: c-to-c.py
#
# Example of using pycparser.c_generator, serving as a simplistic translator
# from C to AST and back to C.
#
# Copyright (C) 2008-2012, Eli Bendersky
# License: BSD
#------------------------------------------------------------------------------
from __future__ import print_function
import sys

# This is not required if you've installed pycparser into
# your site-packages/ with setup.py
#
sys.path.extend(['.', '..'])

from pycparser import parse_file, c_parser, c_generator

init_readconfig = '''
int init_readconfig() {

  // For reading precision contents of config_file into array
   FILE *myFile;
     myFile = fopen("config_file.txt", "r");
 
        if (myFile == NULL) {
					printf("Error Reading File\\n");
                exit (0);
                }
 
        int s;
        for (s = 0; s < LEN; s++) {
            fscanf(myFile, "%d,", &config_vals[s]);
                          }

        fclose(myFile);
        init_mpfr();
        return 0;             
}
'''

init_readconfig_notempvar = '''
int init_readconfig() {

  // For reading precision contents of config_file into array
   FILE *myFile;
     myFile = fopen("config_file.txt", "r");
 
        if (myFile == NULL) {
					printf("Error Reading File\\n");
                exit (0);
                }
 
        int s;
        for (s = 0; s < LEN-1; s++) {
            fscanf(myFile, "%d,", &config_vals[s+1]);
                          }
		config_vals[0] = 53; //all temp_vars are 53 bits in mantissa
        fclose(myFile);
        init_mpfr();
        return 0;             
}
'''
def write_config (num_vars, value):
	f = open('config_file.txt', 'w')
	out_string = '%s,'%(value)*num_vars + '\n'
	f.write(out_string);
	
def get_headers(filename): #get the original list of headers .h file in source file. Use to reconstruct the code for compilablility
    headers_list = []
    with open(filename,'r') as f:
        lines = f.readlines()
        for line in lines:
            if '#include' in line:
                headers_list.append(line)
    return headers_list
    
def translate_to_c(filename, ignore_temp_var=False):
    ast = parse_file(filename, use_cpp=True,
            cpp_path='gcc',
            cpp_args=['-E', r'-I/home/minh/github/c2mpfr/utils/fake_libc_include'])
    generator = c_generator.CGenerator()
    init_mpfr_list = []
    mpfr_vars_decl = []
    eliminate_mpfr_init = []
    num_vars = 1
    #can write to file instead of printing
    #output = open('TRANS_OUT.txt', 'w')
    #output.write(generator.visit(ast))
    output = open('temp_output', 'w')
	#print(generator.visit(ast))
    output.write(generator.visit(ast))
    output.close()
    with open('temp_output') as f:
        lines = f.readlines()
        for line in lines:
            if 'mpfr_t' in line :
                mpfr_vars_decl.append(line)
            elif 'mpfr_init2' in line:
                init_mpfr_list.append(line)
                if 'config_vals' in line and 'config_vals[0]' not in line :
                    num_vars = num_vars + 1;
            else:
                if '\\' in line:
                    line.replace('\\','\\\\')
                if line != ';\n':
					eliminate_mpfr_init.append(line)
	if ignore_temp_var:
		write_config(num_vars-1, 53)
	else:
		write_config(num_vars,53)
		
	
	
    final_output = open('converted2mpfr.c', 'w')	
    for line in get_headers(filename):
        final_output.write(line)
    final_output.write('#include <mpfr.h>\n')
    final_output.write('#define LEN %s \n '%(num_vars))
    final_output.write('int config_vals[LEN];\n')
    final_output.write(''.join(mpfr_vars_decl))
    final_output.write('int init_mpfr() { \n')
    final_output.write(''.join(init_mpfr_list))
    final_output.write('}\n')
    if not ignore_temp_var :
        final_output.write(init_readconfig + '\n')
    else:
        final_output.write(init_readconfig_notempvar + '\n')
    #write the remaining part
    final_output.write(''.join(eliminate_mpfr_init))
    final_output.write('//end of conversion, hopefully it will work :)')
    final_output.close()
    #generator.visit(ast)

    #prints the dependency table
    print('\n\n' + str(generator.mpfr_vars))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    #zz_test_translate()
    if len(sys.argv) ==2:
        translate_to_c(sys.argv[1])
    elif len(sys.argv) ==3:
        translate_to_c(sys.argv[1], True)
    else:
        print ("usage ./C2C.py filename [ignore_temp_var *all tempvars = 53bits mantissa]")
        
   #translate_to_c("c_files/Test.c")
    #else:
        #print("Please provide a filename as argument")

