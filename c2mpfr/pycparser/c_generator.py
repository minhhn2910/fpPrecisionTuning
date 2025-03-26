#------------------------------------------------------------------------------
# pycparser: c_generator.py
#
# C code generator from pycparser AST nodes.
#
# Copyright (C) 2008-2015, Eli Bendersky
# License: BSD
#------------------------------------------------------------------------------
from . import c_ast
from pprint import pprint

class CGenerator(object):
    """ Uses the same visitor pattern as c_ast.NodeVisitor, but modified to
        return a value from each visit method, using string accumulation in
        generic_visit.
    """
    floating_point_types = ['float','double']
    tensors_list_float = [] #store only arrays, matrices pointers have float or double type.
    tensors_list_float_2d = [] # store only 2d array, for ease of processing 2d array ref.
    temp_variable_stack = []
    output_stack = []   #store intermediate expressions to compute a statement
    array_ref_output_stack = [] #store expressions to extract value from arrays, used to introduce temp mpfr vars for tensors.
    var_type_dict = {} #dictionary stores pairs of {var_name|var_type}
    type_def_float = [] #list of new type that defined as float hmmm... macro problem
    func_list = {} #list of function names
    func_arguments = []
    func_call_flag = False #assert when calling a function use mpfr vars (need to be converted back to float))
    interupted_flag = False
    current_function=''
    is_function_parameter = False
    #TODO: note down dependency list of vars
    lhs_mpfr = False #left hand side is mpfr var/ use this to track and build dependency graph
    current_lhs = ''
    parsing_lhs = False
    dependency_graph = {}
    vars_to_index_dict = {}

    def __init__(self):
        self.output = ''
        # Statements start with indentation of self.indent_level spaces, using
        # the _make_indent method
        #
        self.indent_level = 0
        ##
        self.dummy_number = 1  #For multi-arithmetic ops requiring dummy vars
        self.prec_number = 1   #current index in the precision list
        #the first var [0] is for all temp_vars of mpfr

        #Keep track of our converted variables for typechecking and dependencies
        self.mpfr_vars = dict()

    def add_dependency(self, lhs, rhs):
        if lhs == rhs:
            return
        new_lhs = self.vars_to_index_dict[lhs]
        new_rhs = self.vars_to_index_dict[rhs]
        #print('call ' + lhs + ' ' +rhs)
        if new_lhs in self.dependency_graph: #key exists, add new item to current list
            current_list = self.dependency_graph.get(new_lhs)
            if new_rhs not in current_list:
                current_list.append(new_rhs)
        else: #doesn't have that key, add new list
            current_list = [] #create blank list
            current_list.append(new_rhs)
            self.dependency_graph[new_lhs] = current_list
        print("add dependency " + lhs + " " + str(new_lhs) + " " + rhs + " " + str(new_rhs))

    def _make_indent(self):
        return ' ' * self.indent_level

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        print(method)
        return getattr(self, method, self.generic_visit)(node)

    def generic_visit(self, node):
        #~ print('generic:', type(node))
        if node is None:
            return ''
        else:
            return ''.join(self.visit(c) for c_name, c in node.children())

    def visit_Constant(self, n):
        return n.value

    def visit_ID(self, n):
#        return n.name
        temp_string = n.name +'_'+self.current_function
        #print('temp_string ' + temp_string)
        if self.isMPFR(temp_string):
            if self.func_call_flag == True:
                if self.lhs_mpfr == True and self.current_lhs != '':
                    self.add_dependency(self.current_lhs,temp_string)
                return "mpfr_get_d(%s, MPFR_RNDZ)" % ( temp_string)
            else:
                return temp_string
        else:
            return n.name

    def visit_Pragma(self, n):
        ret = '#pragma'
        if n.string:
            ret += ' ' + n.string
        return ret

    def visit_ArrayRef(self, n):
#        arrref = self._parenthesize_unless_simple(n.name)
#        return arrref + '[' + self.visit(n.subscript) + ']'
        #remember outside flag value
        temp_interupted_flag = self.interupted_flag
        self.interupted_flag= True
        arrref = self._parenthesize_unless_simple(n.name)
        refVisitedString = self.visit(n.subscript)
        self.interupted_flag = temp_interupted_flag
        is_array_ref, num_dimension, array_name = self.parse_arrayref(n)
        no_mpfr_output = arrref + '[' + refVisitedString  + ']'
        #print(str(n.name.__class__))
        #pprint(dir(n.name))
        print(no_mpfr_output)
        print(self.tensors_list_float_2d)
        print(array_name)
        if ((num_dimension == 1 and ( not array_name.replace('_mpfr','').replace('_'+self.current_function,'') in self.tensors_list_float_2d)) or (num_dimension == 2) ) and is_array_ref and (not self.parsing_lhs) and (not self.func_call_flag) :
            print("is instance")
            #print(array_name)
            extract_string = ";\n mpfr_set_d(%s,%s,MPFR_RNDZ);\n"%(array_name,no_mpfr_output)
            self.array_ref_output_stack.append(extract_string)
            return array_name
        else:
            return no_mpfr_output

    def visit_StructRef(self, n):
        sref = self._parenthesize_unless_simple(n.name)
        return sref + n.type + self.visit(n.field)

#    def visit_FuncCall(self, n):
#        fref = self._parenthesize_unless_simple(n.name)
#        return fref + '(' + self.visit(n.args) + ')'
    def visit_FuncCall(self, n):
        temp_flag= self.interupted_flag
        if n.name.name == 'malloc' or n.name.name == '':
            self.interupted_flag = True

        self.func_call_flag = True #get double value back from mpfr. may need further work here to detect sqrt .... type
        fref = self._parenthesize_unless_simple(n.name)
        visit_args_result = self.visit(n.args)
        self.func_call_flag = False
        self.interupted_flag = temp_flag
        return fref + '(' + visit_args_result + ')'


    def visit_UnaryOp(self, n):
        operand = self._parenthesize_unless_simple(n.expr)
        ## for i++ i-- only
        if not self.interupted_flag:
            if self.isMPFR(operand):
                if n.op == 'p++':
                    return 'mpfr_add_si(%s, %s, 1, MPFR_RNDZ)' % (operand, operand)
                elif n.op == 'p--':
                    return 'mpfr_sub_si(%s, %s, 1, MPFR_RNDZ)' % (operand, operand)
        ##
        if n.op == 'p++':
            return '%s++' % operand
        elif n.op == 'p--':
            return '%s--' % operand
        if n.op == 'sizeof':
            # Always parenthesize the argument of sizeof since it can be a name.
            return 'sizeof(%s)' % self.visit(n.expr)
        else:
            return '%s%s' % (n.op, operand)

    def is_int_String(self,string_val):
        try:
            int(string_val)
            return True
        except ValueError:
            return False
    def is_float_String(self, string_val):
        try:
            float(string_val)
            return True
        except ValueError:
            return False

    def get_type (self,var_string):
        modified_var_string  = var_string.replace('+','').replace('-','') #handle unaryop

        if self.isMPFR(modified_var_string):
            return 'mpfr'
        else :
            if modified_var_string in self.var_type_dict:
                temp_type = self.var_type_dict[modified_var_string][0]
                if temp_type in self.type_def_float:
                    return 'float'
                else:
                    return temp_type
            elif self.is_int_String(modified_var_string):
                return 'long'
            elif self.is_float_String(modified_var_string):
                return 'float'
            else:
                return 'undefined'
    def create_new_var(self):
        #todo : enable config precision here
        return_string = []
        new_var = self.generate_dummy_var()

        self.mpfr_vars[new_var]=[]
        self.temp_variable_stack.append(new_var)
        return_string.append('\n%smpfr_t %s;\n' %(self._make_indent()*2,new_var))
        return_string.append('%smpfr_init2 (%s, config_vals[0]);\n'%(self._make_indent()*2,new_var))
        return return_string

    def process_array_ref(self,left_node, right_node,lval_str, rval_str):
        left_string = lval_str
        right_string = rval_str
        print(left_string + " " + right_string)
        if "->" not in left_string: #struct ref
            if isinstance(left_node,c_ast.UnaryOp):
                left_node = left_node.expr
            #p#print((vars(left_node)))
            ##print('left instance id ' + str( isinstance(left_node,c_ast.ArrayRef)))
            if  isinstance(left_node,c_ast.ArrayRef):
                if left_string.count('[')==1: #catch 1D array:
                    left_string =left_node.name.name
                elif left_string.count('[')==2: #catch 2D array:
                    left_string = left_node.name.name.name
        if "->" not in right_string:
            if isinstance(right_node,c_ast.UnaryOp):
                right_node = right_node.expr
            ##print('right instance id ' + str( isinstance(right_node,c_ast.ArrayRef)))
            if  isinstance(right_node,c_ast.ArrayRef):
                if right_string.count('[')==1:#catch 1D array:
                    right_string =right_node.name.name
                elif right_string.count('[')==2: #catch 2D array
                    right_string =right_node.name.name.name

        return left_string,right_string

    def visit_BinaryOp(self, n):
        #~ lval_str = self._parenthesize_if(n.left,
                            #~ lambda d: not self._is_simple_node(d))
        #~ rval_str = self._parenthesize_if(n.right,
                            #~ lambda d: not self._is_simple_node(d))
        #~ return '%s %s %s' % (lval_str, n.op, rval_str)
        #`pprint(dir(n))
        lval_str = self._parenthesize_if(n.left, lambda d: not self._is_simple_node(d))
        rval_str = self._parenthesize_if(n.right, lambda d: not self._is_simple_node(d))
        retStr = None
        ##

        #~ Append_ouput= ""
        #print('-----')
        print('debug binaryop')
        print('left ' + lval_str + ' right ' +rval_str)
        #print( ' interupted flag ' + str(self.interupted_flag))
        #print('-----')
        #print('left simple ' + str(self._is_simple_node(n.left)))
        ##print(isinstance(n.left,c_ast.UnaryOp))
        #print('right simple ' + str(self._is_simple_node(n.right)))
        ##print(isinstance(n.right,c_ast.UnaryOp))
        #p#print(vars(n.right))
        print(self.interupted_flag)
        if self.interupted_flag == False:
            #preprocess array ref intermediate expressions
            num_array_ref = 0
            list_temp_output = []
            if lval_str.replace('_mpfr','').replace('_'+self.current_function,'') in self.tensors_list_float:
                num_array_ref += 1
            if rval_str.replace('_mpfr','').replace('_'+self.current_function,'')  in self.tensors_list_float:
                num_array_ref += 1
            if (num_array_ref == 2) and (lval_str == rval_str): #special case, need to introduce intermediate var here.
                list_temp_output.append(self.array_ref_output_stack.pop())
                list_temp_output.extend(self.create_new_var())
                rval_str = self.temp_variable_stack[-1]
                list_temp_output.append(self._make_indent()*2 + "mpfr_set(%s, %s, MPFR_RNDZ);\n" % (rval_str, lval_str))
                list_temp_output.append(self.array_ref_output_stack.pop())
            else:
                while (num_array_ref > 0):
                    list_temp_output.append(self.array_ref_output_stack.pop())
                    num_array_ref -= 1
            #end preprocessing
            if (isinstance(n.left,c_ast.Constant) and isinstance(n.right,c_ast.Constant)): #this case to reduce number of temp var ex 1.0 + 2.0 = 1 constant
                return '%s %s %s' % (lval_str, n.op, rval_str)
                #~ list_temp_output = []
                list_temp_output.extend(self.create_new_var())
                retStr = self.temp_variable_stack[-1]
                constant_str = '%s %s %s' % (lval_str, n.op, rval_str)
                list_temp_output.append(self._make_indent()*2+"mpfr_set_d(%s, %s, MPFR_RNDZ);\n" % (retStr, constant_str))
                self.output_stack.extend(list_temp_output)
            elif n.op in '<=>==':
                print("comparator, 2 nodes")

                return_string = self.MPFR_Operation(None, n.op, lval_str, rval_str,'mpfr','mpfr')

                if return_string !=None:
                    return_string += "\n//original  " + '%s %s %s' % (lval_str, n.op, rval_str) + "\n"
                    return return_string
                    #print(return_string)
                    #print(self.output_stack)
            elif ((self._is_simple_node(n.right) or isinstance(n.right,c_ast.UnaryOp))and (self._is_simple_node(n.left) or isinstance(n.left,c_ast.UnaryOp)) ):
                if n.op not in '<=>==': #it sucks here, need to handle %

                    #print('-----')
                    print('both simple node')
                    print('left ' + lval_str + ' right ' +rval_str)
                # remove this condition/ proccess all kinds of expression    if self.isMPFR(lval_str) or self.isMPFR(rval_str):
                    #left_string,right_string = self.process_array_ref(n.left, n.right,lval_str, rval_str)
                    left_string = lval_str
                    right_string = rval_str
                    typeleft = self.get_type(left_string)
                    typeright = self.get_type(right_string)

                    #~ list_temp_output = []

                    #p#print((vars(n.left.name)))
                    op1 = lval_str
                    op2 = rval_str
                    #if type
                    #be careful with append vs extend confusion in python list
                    #print(self.var_type_dict)
                    #print(self.type_def_float)
                    if  (left_string in self.var_type_dict and (typeleft == 'float' or typeleft =='double')):# or (n.op =='%' and type_left != 'mpfr'):
                        list_temp_output.extend(self.create_new_var())
                        op1 = self.temp_variable_stack[-1]
                        list_temp_output.append(self._make_indent()*2+"mpfr_set_d(%s, %s, MPFR_RNDZ);\n" % (op1, lval_str))
                    if (right_string in self.var_type_dict and (typeright == 'float' or typeright =='double') ):# or (n.op =='%' and type_right != 'mpfr'):
                        list_temp_output.extend(self.create_new_var())
                        op2 = self.temp_variable_stack[-1]
                        list_temp_output.append(self._make_indent()*2 + "mpfr_set_d(%s, %s, MPFR_RNDZ);\n" % (op2, rval_str) )

                    typeleft = self.get_type(op1)
                    typeright = self.get_type(op2)

                    #print('op1 ' + op1)
                    #print('op2 ' + op2)
                    #print('simple left string ' + left_string)
                    #print('simple right_string ' + right_string)
                    #print('type left' + typeleft)
                    #print('type right ' + typeright)
                    #create new temp var to save intermediate result
                    list_temp_output.extend(self.create_new_var())
                    retStr = self.temp_variable_stack[-1]
                    #print("check newvar " + lval_str + '-----' + rval_str)
                    return_string = self.MPFR_Operation(self.temp_variable_stack[-1], n.op, op1, op2,typeleft,typeright)
                    if return_string !=None:
                        list_temp_output.append("%s%s%s"%(self._make_indent()*2,return_string, ';\n' ))
                    else:
                        retStr = '%s %s %s' % (lval_str, n.op, rval_str) #simplenode (long + int)
                    self.output_stack.extend(list_temp_output)
                    #not simple node anymore, it's return from accumulate temporary variables
                    print(self.output_stack)
                #else:#assume binary comparator is for two mpfr_t vars/ Otherwise, debug later
                    #working here

            else:
                print("else binary op")
                left_string,right_string = self.process_array_ref(n.left, n.right,lval_str, rval_str)

                typeleft = self.get_type(left_string)
                typeright = self.get_type(right_string)

                if typeleft == 'mpfr' or typeright=='mpfr' or (typeleft == 'float' or typeleft =='double') or (typeright == 'float' or typeright =='double'):


                    #~ list_temp_output = []

                    #p#print((vars(n.left.name)))
                    op1 = lval_str
                    op2= rval_str
                    #if type


                    if  (left_string in self.var_type_dict and (typeleft == 'float' or typeleft =='double')): #or (n.op =='%' and typeleft != 'mpfr'):
                        list_temp_output.extend(self.create_new_var())
                        op1 = self.temp_variable_stack[-1]
                        list_temp_output.append(self._make_indent()*2+"mpfr_set_d(%s, %s, MPFR_RNDZ);\n" % (op1, lval_str))
                    if (right_string in self.var_type_dict and (typeright == 'float' or typeright =='double') ):# or (n.op =='%' and typeright != 'mpfr'):
                        list_temp_output.extend(self.create_new_var())
                        op2 = self.temp_variable_stack[-1]
                        list_temp_output.append(self._make_indent()*2 + "mpfr_set_d(%s, %s, MPFR_RNDZ);\n" % (op2, rval_str) )

                    typeleft = self.get_type(op1)
                    typeright = self.get_type(op2)

                    #print('type left' + typeleft)
                    #print('type right ' + typeright)
                    #print('else left string ' + left_string)
                    #print('else right_string ' + right_string)
                    #create new temp var to save intermediate result
                    #After processing, if neither is mpfr, then return (because it's series of constants or unknown type)
                    if typeleft!='mpfr' and typeright!='mpfr':
                       return '%s %s %s' % (lval_str, n.op, rval_str)


                    list_temp_output.extend(self.create_new_var())
                    #new_var just create in the stack
                    retStr = self.temp_variable_stack[-1]

                    #print("check newvar " + lval_str + '-----' + rval_str)
                    return_string = self.MPFR_Operation(self.temp_variable_stack[-1], n.op, op1, op2,typeleft,typeright)
                    if return_string !=None:
                        list_temp_output.append("%s%s%s"%(self._make_indent()*2,return_string, ';\n' ))
                    for item_temp in list_temp_output:
                        if item_temp not in self.output_stack:
                            self.output_stack.append(item_temp)

        return '%s %s %s' % (lval_str, n.op, rval_str) if (retStr == None) else retStr

    def parse_arrayref(self, node):
        #parse array, return mpfr temp var for an array if node is arrayRef
        is_array_ref = False
        num_dimension = 0
        array_name = "None"
        if isinstance(node, c_ast.ArrayRef):
            #print("array ref assignment lhs")
            #pprint(dir(node.name))
            #print(str(node.show.__class__))
            #print(str(node.coord))
            temp_array_name = ''
            if isinstance(node.name, c_ast.ArrayRef):
                print("2d array ref")
                print(node.name.name.name)
                num_dimension = 2
                temp_array_name = node.name.name.name
                #return (True,2,node.name.name.name)
            elif isinstance(node.name, c_ast.ID):
                print("1d array ref")
                print(node.name.name)
                num_dimension = 1
                temp_array_name = node.name.name
               #return (True,1,node.name.name)
            #check the current function, make sure array_name will be isMPFR
            if self.current_function!= '' and self.isMPFR(temp_array_name + '_' + self.current_function + '_mpfr'):
                array_name = temp_array_name + '_' + self.current_function + '_mpfr'
                is_array_ref = True
            elif self.isMPFR(temp_array_name + '_mpfr'):
                array_name = temp_array_name + '_mpfr'
                is_array_ref = True
        return (is_array_ref,num_dimension,array_name)

    def visit_Assignment(self, n):
#        rval_str = self._parenthesize_if(
#                            n.rvalue,
#                            lambda n: isinstance(n, c_ast.Assignment))
#        return '%s %s %s' % (self.visit(n.lvalue), n.op, rval_str)
		#print(n.lvalue.subscript.value)
        is_array_ref, num_dimension, array_name = self.parse_arrayref(n.lvalue)
        lval_str = "None"
        #~ print(str(is_array_ref) + " " + str(num_dimension) + " " + array_name)
        self.parsing_lhs = True
        temp_lval_str = self.visit(n.lvalue)
        self.parsing_lhs = False
        if is_array_ref:
            lval_str = array_name
        else:
            lval_str = temp_lval_str
        #~ print(str(is_array_ref) + " " + str(num_dimension) + " " + array_name)
        if (self.isMPFR(lval_str) and 'temp_var_' not in lval_str):
            self.lhs_mpfr = True
            self.current_lhs = lval_str
        rval_str = self._parenthesize_if(
                            n.rvalue,
                            lambda n: isinstance(n, c_ast.Assignment))
       # self.interupted_flag = False
        out_string = ""
        #~ print("debug_assigment -- left " + lval_str + "  right   "+rval_str  + "  ops  " +n.op)
        if len(self.array_ref_output_stack) !=0 :
            out_string+='//array_ref_output_stack != null from parsing right hand side, dump all itermediate operations here\n'
            for item in self.array_ref_output_stack:
                out_string+= item
            self.array_ref_output_stack =[]

        self.lhs_mpfr = False
        self.current_lhs = ''
        if self.isMPFR(lval_str) and self.isMPFR(rval_str):
            #todo: only if rval_str = temp variable [just push in stack] so need to do tricks, otherwise, do mpfrset here
            if n.op == '=':
                #little trick here, replace the last line with lval
                    ##
                if len(self.temp_variable_stack) !=0 and  rval_str == self.temp_variable_stack[-1]:

                    for item in self.output_stack[:-3]:
                        #print(item)
                        out_string += item
                    out_string += self.output_stack[len(self.output_stack)-1].replace(rval_str,lval_str)
                    self.output_stack = []
                    self.temp_variable_stack.pop()
                    self.dummy_number= self.dummy_number-1

                    #return out_string #delete ;\n
                else:
                    out_string += "mpfr_set(%s, %s, MPFR_RNDZ)" % (lval_str, rval_str)

            else:
                #~ out_string = ""
                for item in self.output_stack:
                    out_string += item
                #print(" += ops ")
                out_string += self._make_indent() +self.MPFR_Operation(lval_str, n.op[0], lval_str, rval_str, 'mpfr', 'mpfr')
                self.output_stack = []
                #return out_string
            #~ elif n.op == '-=':
                #~ out_string = ""
                #~ for item in self.output_stack:
                    #~ out_string += item
                #~ out_string += self.MPFR_Operation(lval_str, '-', lval_str, rval_str, 'mpfr', 'mpfr')
                #~ self.output_stack = []
                #~ return out_string[:-2]
            #~ elif n.op == '*=':
                #~ out_string = ""
                #~ for item in self.output_stack:
                    #~ out_string += item
                #~ out_string += self.MPFR_Operation(lval_str, '*', lval_str, rval_str, 'mpfr', 'mpfr')
                #~ self.output_stack = []
                #~ return out_string[:-2]
            #~ elif n.op == '/=':
                #~ out_string = ""
                #~ for item in self.output_stack:
                    #~ out_string += item
                #~ out_string += self.MPFR_Operation(lval_str, '/', lval_str, rval_str, 'mpfr', 'mpfr')
                #~ self.output_stack = []
                #~ return out_string[:-2]
            if is_array_ref :
                out_string += ";\n" + self._make_indent() + "%s = mpfr_get_d(%s, MPFR_RNDZ)" %(temp_lval_str,lval_str)
            return out_string
        elif self.isMPFR(lval_str) and (not self.isMPFR(rval_str)):
            if n.op == '=':
                stype='_d'
                out_string +=  "mpfr_set"+stype+"(%s, %s, MPFR_RNDZ)" % (lval_str, rval_str)
            else:
                #todo introduce new variable = right hand side
                #assigne op to that value

                new_var = self.generate_dummy_var()
                self.mpfr_vars[new_var]=[]
                return_string = ''
                return_string+= self._make_indent() *2 + 'mpfr_t %s ;\n'%(new_var)
                return_string+= self._make_indent() *2 + 'mpfr_init2 (%s, config_vals[0]);\n'%(new_var)
                return_string+= self._make_indent() *2 + 'mpfr_set_d(%s, %s, MPFR_RNDZ);\n' % (new_var, rval_str)
                return_string+= self._make_indent() *2 + self.MPFR_Operation(lval_str, n.op[0], lval_str, rval_str, 'mpfr', 'mpfr')
                return_string +=';\n'#to make sure no error here, redundant semicolons may appear
                out_string +=  return_string
            if is_array_ref :
                out_string += ";\n" + self._make_indent() + "%s = mpfr_get_d(%s, MPFR_RNDZ)" %(temp_lval_str,lval_str)
            return out_string

        elif (not self.isMPFR(lval_str)) and  self.isMPFR(rval_str):
            ##doesn't control left hand side is float or long, int now, just float
            pre_output = ''
            for item in self.output_stack:
                pre_output += item

            self.output_stack=[]

            right_output = "mpfr_get_d(%s, MPFR_RNDZ)" % ( rval_str)
            return pre_output + '\n' + '%s %s %s' %(lval_str, n.op, right_output)

        elif (not self.isMPFR(lval_str)) and (not self.isMPFR(rval_str)):
            #print(' n.op != = or not self.isMPFR(lval_str)')
            return '%s %s %s' % (lval_str, n.op, rval_str)
        #return '%s %s %s %s' % (out_string,lval_str, n.op, rval_str)
        retStr = self.MPFR_Helper(lval_str, rval_str)
        return '%s %s %s %s' % (out_string, lval_str, n.op, rval_str) if (retStr == None) else  '%s %s'%(out_string,retStr)
        ##

    def visit_IdentifierType(self, n):
        return ' '.join(n.names)

    def _visit_expr(self, n):
        if isinstance(n, c_ast.InitList):
            return '{' + self.visit(n) + '}'
        elif isinstance(n, c_ast.ExprList):
            return '(' + self.visit(n) + ')'
        else:
            return self.visit(n)



    ## New function for generating MPFR setter and arithmetic ops
    def MPFR_Helper(self, left_name, right_side):
        if not self.isMPFR(left_name):
            return None

        depnd = True if left_name in self.mpfr_vars else False

        right_str = right_side.replace(" ","").replace('(','').replace(')','')
        operators = '[+\-*/]'
        opds = re.split(operators, right_str)

        #non-variables can be set as a whole, i.e. mpfr_set_d(x, 13.3 + 8881.11111, MPFR_RNDZ)
        allNums = True
        for opd in opds:
            if not self.isNum(opd):
                allNums = False
        if allNums and left_name in self.mpfr_vars:
            return "mpfr_set_d(%s, %s, MPFR_RNDZ)" % (left_name, right_side)

        if len(opds) == 2:
            op = re.search(operators, right_str).group()
            #add to dependency list
            if depnd and opds[0] in self.mpfr_vars and opds[0] != left_name:
                self.mpfr_vars[left_name].append(opds[0])
            if depnd and opds[1] in self.mpfr_vars and opds[1] != left_name:
                self.mpfr_vars[left_name].append(opds[1])

            return self.MPFR_Operation(left_name, op, opds[0], opds[1],'mpfr', 'mpfr')

        add = right_str.find('+')
        sub = right_str.find('-')
        mul = right_str.find('*')
        div = right_str.find('/')
        if (add == -1 and sub == -1) and (mul != -1 or div != -1): #only */
            pass
        #elif (add != -1 or sub != -1) and (mul == -1 and div == -1):
            #pass
        else:   #can't work with mixed order of operations
            return None

        search = re.search(operators, right_str)
        op = search.group() if (search is not None) else None
        opds = right_str.split(op, 1)

        dummy = self.generate_dummy_var()
        #add to dependency list
        if depnd and opds[0] in self.mpfr_vars and opds[0] != left_name:
            self.mpfr_vars[left_name].append(opds[0])
        self.mpfr_vars[dummy] = []
        self.mpfr_vars[left_name].append(dummy)

        topStr = "mpfr_t %s;\n" % dummy + self._make_indent() + "mpfr_init2(%s, %s)" % (dummy, self.generate_precision())
        bottomStr = self.MPFR_Operation(left_name, op, opds[0], dummy,'mpfr', 'mpfr')
        midStr = self.MPFR_Helper(dummy, opds[1])
        if topStr is not None and bottomStr is not None and midStr is not None:
            indent = self._make_indent()
            return topStr + ";\n" + indent + midStr + ";\n" + indent + bottomStr

    def MPFR_Operation(self, dest, op, opd1, opd2, type1, type2):##
        if type1!='mpfr' and type2!='mpfr': #long and int, annoying types
            return None
        if dest != None:
            result_string = ''
            #string is immutable, so copy to another version
            my_op = op
            my_opd1 = opd1
            my_opd2 = opd2
            #my_type1 = type1 not used
            #my_type2 = type2
            #fix unary op like uz + (+ux-uy)
            if type1 == 'mpfr':
                #dependency proccessing:
                if self.lhs_mpfr == True and self.current_lhs!='' and 'temp_var_' not in opd1 :
                    self.add_dependency(self.current_lhs,opd1.replace('+','').replace('-','').replace('(','').replace(')',''))
                if '+' in opd1:
                    my_opd1 = opd1.replace('+','')
                   # my_type1 = self.get_type (my_opd1) #get type again, it might be wrong outside

                if '-' in opd1:#new tempvar + neg
                    my_opd1 = opd1.replace('-','')
                    list_temp_output = []
                    list_temp_output.extend(self.create_new_var())
                    new_var = self.temp_variable_stack[-1]
                    for item in list_temp_output:
                        result_string += item
                    result_string += 'mpfr_neg (%s, %s, MPFR_RNDZ);\n'%(new_var,my_opd1)
                    my_opd1 = new_var
            if type2 == 'mpfr':
                if self.lhs_mpfr == True and self.current_lhs!='' and 'temp_var_' not in opd2 :
                    self.add_dependency(self.current_lhs,opd2.replace('+','').replace('-','').replace('(','').replace(')',''))
                if '+' in opd2:
                    my_opd2 = opd2.replace('+','')
                    #type2 = self.get_type (opd2)
                if '-' in opd2:
                    my_opd2 = opd2.replace('-','')
                    #type2 = self.get_type (opd2)
                    if op == '+':
                        my_op = '-'
                    if op == '-':
                        my_op = '+'
            #print('op1 op  op2  type1 typ2   %s  %s  %s   %s   %s '%(my_opd1,my_op,my_opd2,type1, type2))
            #further uz *-uy ? grammatically wrong
            if op == '+':
                if(type1 != 'mpfr'):
                    #reverse the order of op1 and op2 so it can satisfy the mpfr API, 1 st op is mpfr_t
                    if 'unsigned' in type1:
                        return result_string + 'mpfr_add_ui(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                    elif 'long' in type1 or 'int' in type1 or 'short' in type1:
                        return result_string + 'mpfr_add_si(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                    elif 'float' in type1 or 'double' in type1 :
                        return result_string +'mpfr_add_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                    else:
                        #print('error , cannot get data type info of '+ type1)
                        return result_string +'mpfr_add_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                elif(type2 != 'mpfr'):
                    #no need to reverse, the 1st op is mpfr_t already
                    if 'unsigned' in type2:
                        return result_string +'mpfr_add_ui(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'long' in type2 or 'int' in type2 or 'short' in type2:
                        return result_string +'mpfr_add_si(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'float' in type2 or 'double' in type2:
                        return result_string +'mpfr_add_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    else:
                        #print('error , cannot get data type info of '+ type2)
                        return result_string +'mpfr_add_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)

                else:
                    return result_string +'mpfr_add(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
            elif op == '-':
                if(type1 != 'mpfr'):
                    if 'unsigned' in type1:
                        return result_string +'mpfr_ui_sub(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'long' in type1 or 'int' in type1 or 'short' in type1:
                        return result_string +'mpfr_si_sub(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'float' in type1 or 'double' in type1:
                        return result_string +'mpfr_d_sub(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    else:
                        #print('error , cannot get data type info of '+ type1)
                        return result_string +'mpfr_d_sub(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                elif(type2 != 'mpfr'):
                    if 'unsigned' in type2:
                        return result_string +'mpfr_sub_ui(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'long' in type2 or 'int' in type2 or 'short' in type2:
                        return result_string +'mpfr_sub_si(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'float' in type2 or 'double' in type2:
                        return result_string +'mpfr_sub_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    else:
                        #print('error , cannot get data type info of '+ type2)
                        return result_string +'mpfr_sub_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)

                else:
                    return result_string +'mpfr_sub(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
            elif op == '*':
                if(type1 != 'mpfr'):
                    #reverse the order of op1 and op2 so it can satisfy the mpfr API, 1 st op is mpfr_t
                    if 'unsigned' in type1:
                        return result_string +'mpfr_mul_ui(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                    elif 'long' in type1 or 'int' in type1 or 'short' in type1:
                        return result_string +'mpfr_mul_si(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                    elif 'float' in type1 or 'double' in type1:
                        return result_string +'mpfr_mul_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                    else:
                        #print('error , cannot get data type info of '+ type1)
                        return result_string +'mpfr_mul_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd2, my_opd1)
                elif(type2 != 'mpfr'):
                    #no need to reverse, the 1st op is mpfr_t already
                    if 'unsigned' in type2:
                        return result_string +'mpfr_mul_ui(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'long' in type2 or 'int' in type2 or 'short' in type2:
                        return result_string +'mpfr_mul_si(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'float' in type2 or 'double' in type2:
                        return result_string +'mpfr_mul_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    else:
                        #print('error , cannot get data type info of '+ type2)
                        return result_string +'mpfr_mul_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                else:
                    return result_string +'mpfr_mul(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
            elif op == '/':
                if(type1 != 'mpfr'):
                    if 'unsigned' in type1:
                        return result_string +'mpfr_ui_div(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'long' in type1 or 'int' in type1 or 'short' in type1:
                        return result_string +'mpfr_si_div(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'float' in type1 or 'double' in type1:
                        return result_string +'mpfr_d_div(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    else:
                        #print('error , cannot get data type info of '+ type1)
                        return result_string +'mpfr_d_div(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                elif(type2 != 'mpfr'):
                    if 'unsigned' in type2:
                        return result_string +'mpfr_div_ui(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'long' in type2 or 'int' in type2 or 'short' in type2:
                        return result_string +'mpfr_div_si(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    elif 'float' in type2 or 'double' in type2:
                        return result_string +'mpfr_div_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                    else:
                        #print('error , cannot get data type info of '+ type2)
                        return result_string +'mpfr_div_d(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
                else:
                    return result_string +'mpfr_div(%s, %s, %s, MPFR_RNDZ)' % (dest, my_opd1, my_opd2)
            elif op == '%':
                    return result_string + 'mpfr_fmod(%s, %s, %s, MPFR_RNDZ)'%(dest, my_opd1, my_opd2)
        elif (self.isMPFR(opd1) and self.isMPFR(opd2)):
            #self.output_stack.append
            return '(mpfr_cmp(%s,%s) %s 0)'%(opd1,opd2, op)
            #~ if op == '==':
                #~ return 'mpfr_equal_p(%s, %s)' % (opd1, opd2)
            #~ elif op == '>':
                #~ return 'mpfr_greater_p(%s, %s)' % (opd1, opd2)
            #~ elif op == '<':
                #~ return 'mpfr_less_p(%s, %s)' % (opd1, opd2)
            #~ elif op == '<=' or op == '=<':
                #~ return 'mpfr_lessequal_p(%s, %s)' % (opd1, opd2)
            #~ elif op == '>=' or op == '=>':
                #~ return 'mpfr_greaterequal_p(%s, %s)' % (opd1, opd2)
        elif (self.isMPFR(opd1) and (not self.isMPFR(opd2))):
            return '(mpfr_cmp_d(%s,%s) %s 0)'%(opd1,opd2, op)
        elif (not self.isMPFR(opd1) and self.isMPFR(opd2)):
            if '<' in op:
                return '(mpfr_cmp_d(%s,%s) %s 0)'%(opd2,opd1, op.replace('<','>')) #reverse ops
            else:
                return '(mpfr_cmp_d(%s,%s) %s 0)'%(opd2,opd1, op.replace('>','<'))
        return None

    def generate_dummy_var(self):##
        dummy_var = "temp_var_" + str(self.dummy_number)
        self.dummy_number += 1
        return dummy_var

    def generate_precision(self):##
        prec_var = str(self.prec_number)
        #self.config_file.write(str(prec_len) + ',')
        self.prec_number += 1
        return 'config_vals[' + prec_var + ']'

    def isMPFR(self, varName):##
        varName = varName.replace('(','').replace(')','')
        return (varName in self.mpfr_vars)

    def isNegative(self, value):##
        return value.startswith('-')

    def isNum(self, string):##
        try:
            p = float(string)
            return True
        except ValueError:
            return False

    #def visit_Decl(self, n, no_type=False):
        # no_type is used when a Decl is part of a DeclList, where the type is
        # explicitly only for the first declaration in a list.
        #
     #   s = n.name if no_type else self._generate_decl(n)
     #   if n.bitsize: s += ' : ' + self.visit(n.bitsize)
     #   if n.init:
     #       s += ' = ' + self._visit_expr(n.init)
     #   return s

    def init_mpfr_var(self, new_var_name):
        #return 2 statements to initialize mpfr variable var_name
        s = 'mpfr_t %s;\n' % new_var_name
        self.vars_to_index_dict[new_var_name] = str(self.prec_number-1)
        s += self._make_indent() + 'mpfr_init2(%s, %s);\n' % (new_var_name, self.generate_precision())
        self.mpfr_vars[new_var_name] = []

        return s

    def visit_Decl(self, n, no_type=False):
        # no_type is used when a Decl is part of a DeclList, where the type is
        # explicitly only for the first delaration in a list.

        ## if it's a floating point number
        ##
        #~ pprint(vars(n))
        if  (isinstance(n.type, c_ast.FuncDecl)):
            print("---------check")

        substring = None
        if  self.is_function_parameter:
            if isinstance(n.type, c_ast.TypeDecl) and hasattr(n.type.type, 'names'):
                if bool(set(n.type.type.names) & set(['double','float'])):
                    if self.current_function!='':
                        new_var_name = '%s_%s'%(n.type.declname,self.current_function) #rename mpfr vars to var_funcname ; affects 4 lines below
                    else:
                        new_var_name = n.type.declname
                    s = self.init_mpfr_var(new_var_name)
                    s += ';\n mpfr_set_d(%s,%s,MPFR_RNDZ);\n'%(new_var_name,n.type.declname)
                    self.output_stack.append(s)
            #~ self.func_arguments.append(n.type.type.names);

        if isinstance(n.type, c_ast.TypeDecl) and hasattr(n.type.type, 'names') and (not self.is_function_parameter):# and self.current_function!='':
            if bool(set(n.type.type.names) & set(['double','float'])):
                if self.current_function!='':
                    new_var_name = '%s_%s'%(n.type.declname,self.current_function) #rename mpfr vars to var_funcname ; affects 4 lines below
                else:
                    new_var_name = n.type.declname
                s = self.init_mpfr_var(new_var_name)

                if not n.init:
                    return s

                s += ';\n' + self._make_indent()
                rhs = self.visit(n.init)
                out_string = ''

                if len(self.temp_variable_stack) !=0 and rhs == self.temp_variable_stack[-1]:
                    #undo the temp_var
                    #
                    for item in self.output_stack[:-3]:
                        #print(item)
                        out_string += item
                    out_string += self.output_stack[len(self.output_stack)-1].replace(rhs,new_var_name)
                    self.output_stack = []
                    for item in out_string[:-2]: #delete ;\n
                        s += item
                    self.output_stack =[]
                    self.temp_variable_stack.pop()
                    self.dummy_number= self.dummy_number-1
                    return s
                elif self.isMPFR(rhs):
                    substring = "mpfr_set(%s, %s, MPFR_RNDZ)" % (new_var_name, rhs)
                    return s
                elif len(self.output_stack) !=0 :
                    for item in self.output_stack:
                        s+= item
                    self.output_stack =[]
                    return s
                if self._is_simple_node(n.init) or self.isNegative(rhs):
                    stype = ''
                    if self.isNum(rhs):
                        stype = '_d'
                    substring = "mpfr_set"+stype+"(%s, %s, MPFR_RNDZ)" % (new_var_name, rhs)
                #~ else:
                    #~ substring = self.MPFR_Helper(n.name, rhs)

                if (substring != None):
                    return s + substring
                else:
                    return s + "%s = %s" % (n.name, rhs)
        ##todo: if declarations in inside function declare, put it into another list for further ignore in assigment .
        #handle 1D array
        is_tensor_float = False
        if isinstance(n.type, c_ast.PtrDecl) or isinstance(n.type, c_ast.ArrayDecl):
            #pprint((dir(n.type.type.type))i)
            if isinstance(n.type.type.type, c_ast.IdentifierType):
                #1D array
                #print(str(n.type.type.type.names))
                if n.type.type.type.names[0] in self.floating_point_types :
                    self.tensors_list_float.append(str(n.name))
                    is_tensor_float = True
            elif isinstance(n.type.type.type.type, c_ast.IdentifierType):
                #2d array
                print(str(n.type.type.type.type.names))
                print(self.floating_point_types)
                if n.type.type.type.type.names[0] in self.floating_point_types:
                    self.tensors_list_float.append(str(n.name))
                    self.tensors_list_float_2d.append(str(n.name))
                    is_tensor_float = True
            else:
                #more than 2 dimensions, currently not supported
                pass
            #print(str(n.type.type.type.__class__))
            #pprint((dir(n)))
            #print(str(n);)
            #~ print(self.tensors_list_float)
            #print(str(n.name))
        if isinstance(n.type, c_ast.Struct):
            return ""

        #~ if isinstance(n.type, c_ast.PtrDecl):
            #~ if isinstance(n.type.type, c_ast.TypeDecl):
                #~ self.var_type_dict [n.type.type.declname] = n.type.type.type.names
            #~ #handle 2D array #hope not to deal with it :(
        #~ if isinstance(n.type, c_ast.PtrDecl):
            #~ if isinstance(n.type.type, c_ast.PtrDecl):
                #~ if isinstance(n.type.type.type, c_ast.TypeDecl):
                    #~ self.var_type_dict [n.type.type.type.declname] = n.type.type.type.type.names
            #~ if isinstance(n.type, c_ast.TypeDecl) and hasattr(n.type.type, 'names'):
                #~ self.var_type_dict [n.type.declname] = n.type.type.names

        s = n.name if no_type else self._generate_decl(n)
        if n.bitsize: s += ' : ' + self.visit(n.bitsize)
        if n.init:
            if isinstance(n.init, c_ast.InitList):
                s += ' = {' + self.visit(n.init) + '}'
            elif isinstance(n.init, c_ast.ExprList):
                s += ' = (' + self.visit(n.init) + ')'
            else:
                s += ' = %s;\n' % (self.visit(n.init))
        if is_tensor_float: #add temp var for array holding flaoting point numbers:
            new_temp_var = ''
            if self.current_function!='':
                new_temp_var = self.tensors_list_float[len(self.tensors_list_float)-1] + '_'+ self.current_function +'_mpfr'
            else:
                new_temp_var = self.tensors_list_float[len(self.tensors_list_float)-1] + '_mpfr'
            tensor_init_string = self.init_mpfr_var(new_temp_var)
            if not self.is_function_parameter:
                s += ';\n' + tensor_init_string
            else:
                self.output_stack.append(tensor_init_string)
        return s

    def visit_Typedef(self, n):
        temp_flag = self.interupted_flag
        #print('typedef ')
        try:
            #if ( n.type.type.type.names[0] == 'float' or n.type.type.type.names[0] == 'double'):
            if (n.type.type.type.names[0] in self.floating_point_types):
                self.type_def_float.append(n.type.type.declname)
        except:
            pass
        #p#print(vars(n.type.type))
        self.interupted_flag = True
        s = ''
        if n.storage: s += ' '.join(n.storage) + ' '
        s += self._generate_type(n.type)
        self.interupted_flag = temp_flag
        #return s
        return '' #no type defs to be included in the generated code. We need to include the original headers again for readability
        #we aim to 100% automatic conversion that can be compiled without modification. This is necessary because of the use of fake headers in pycparser

    def visit_Cast(self, n):
        s = '(' + self._generate_type(n.to_type) + ')'
        return s + ' ' + self._parenthesize_unless_simple(n.expr)

    def visit_ExprList(self, n):
        visited_subexprs = []
        for expr in n.exprs:
            visited_subexprs.append(self._visit_expr(expr))
        return ', '.join(visited_subexprs)

    def visit_InitList(self, n):
        visited_subexprs = []
        for expr in n.exprs:
            visited_subexprs.append(self._visit_expr(expr))
        return ', '.join(visited_subexprs)

    def visit_Enum(self, n):
        s = 'enum'
        if n.name: s += ' ' + n.name
        if n.values:
            s += ' {'
            for i, enumerator in enumerate(n.values.enumerators):
                s += enumerator.name
                if enumerator.value:
                    s += ' = ' + self.visit(enumerator.value)
                if i != len(n.values.enumerators) - 1:
                    s += ', '
            s += '}'
        return s

    def visit_FuncDef(self, n):
        #print("visit funcdef")
                #Function parameters, do not proccess mpfr
        #p#print(n.decl.type.type.type.names) #function_type
        #p#print(n.decl.type.type.declname) #function_name
        try:
            self.func_list[n.decl.type.type.declname] = n.decl.type.type.type.names[0] #usual return type, do not handle specific coding style
            self.current_function = n.decl.type.type.declname
        except:
            pass
        #p#print(vars(n.decl.type.args.params[0].type.type.names)) #function_ arguments
        #~ #print(n.decl.type.args.params[0].type.type.names)
        #~ #print(n.decl.type.args.params[0].type.declname)
        # p#print(vars(n.decl.type.args.params[0].type))

        self.is_function_parameter = True
        decl = self.visit(n.decl)
        print(" func def "+decl)
        self.is_function_parameter = False
        self.indent_level = 0
        body = self.visit(n.body)
        pre_body = ""
        if len(self.output_stack) !=0 :
            pre_body+='//output_stack != null from visiting function declare, dump all itermediate operations here\n'
            for item in self.output_stack:
                pre_body+= item
            self.output_stack =[]

        if n.param_decls:
            knrdecls = ';\n'.join(self.visit(p) for p in n.param_decls)
            if self.current_function == 'main':
                return decl + '\n' + knrdecls + ';\n' + '{\n init_readconfig();\n' + pre_body  + body.replace('{\n','',1) + '\n'
            else:
                return decl + '\n' + knrdecls + ';\n' + pre_body+ body + '\n'
        else:
            if self.current_function == 'main':
                return decl + '\n' +'{\n init_readconfig();\n' + pre_body + body.replace('{\n','',1) + '\n'
            else:
                return decl + '\n' + pre_body + body + '\n'

    def visit_FileAST(self, n):
        #~ s = ''
        #~ for ext in n.ext:
            #~ if isinstance(ext, c_ast.FuncDef):
                #~ s += self.visit(ext)
            #~ elif isinstance(ext, c_ast.Pragma):
                #~ s += self.visit(ext) + '\n'
            #~ else:
                #~ s += self.visit(ext) + ';\n'
        #~ return s
        s = ''
        for ext in n.ext:
            if isinstance(ext, c_ast.FuncDef):
                s += self.visit(ext)
            elif isinstance(ext, c_ast.Pragma):
                s += '' # ignore pragma self.visit(ext) + '\n'
            else:
                s += self.visit(ext) + ';\n'
        #program end here, note down the dependency graph
            output = open('dependency_graph.txt', 'w')
            #print(generator.visit(ast))
            for item in self.dependency_graph.keys():
                output.write(item)
                for element in self.dependency_graph.get(item):
                    output.write(' '+element)
                output.write('\n')
                #output.write(str(self.dependency_graph.get(item))+'\n')
            output.close()
        return s

    def visit_Compound(self, n):
        s = self._make_indent() + '{\n'
        self.indent_level += 2
        if n.block_items:
            s += ''.join(self._generate_stmt(stmt) for stmt in n.block_items)
        self.indent_level -= 2
        s += self._make_indent() + '}\n'
        return s

    def visit_EmptyStatement(self, n):
        return ';'

    def visit_ParamList(self, n):
        self.is_function_parameter = True
        result = ', '.join(self.visit(param) for param in n.params)
        self.is_function_parameter = False
        return result

    def visit_Return(self, n):
        return_type = ''
        if self.current_function!='':
            return_type = self.func_list[self.current_function]
        s=''
        if n.expr:
            return_string = self.visit(n.expr)
            if len(self.output_stack) !=0 :
                s+='//output_stack != null, dump all itermediate operations here\n'
                for item in self.output_stack:
                    s+= item
                self.output_stack =[]
            s += 'return '
            if self.isMPFR(return_string):
                if 'int' in return_type or 'long' in return_type:
                    s += "mpfr_get_si(%s, MPFR_RNDZ)" % ( return_string)
                else:
                    s += "mpfr_get_d(%s, MPFR_RNDZ)" % ( return_string)
            else:
                s += return_string
   #     self.current_function =''
        #clear func_arguments avoid duplicates
        self.func_arguments = []
        return s + ';'


    def visit_Break(self, n):
        return 'break;'

    def visit_Continue(self, n):
        return 'continue;'

    def visit_TernaryOp(self, n):
        s = self._visit_expr(n.cond) + ' ? '
        s += self._visit_expr(n.iftrue) + ' : '
        s += self._visit_expr(n.iffalse)
        return s

    def visit_If(self, n):
        temp_interupted_flag = self.interupted_flag

        s = ''
        prefix = ''
        return_string = ''
        #self.interupted_flag = True
        #if n.cond: s += self.visit(n.cond)
        if n.cond:
            #print(n.cond)
            #p#print((vars(n.cond.left)))
            ##print(isinstance(n.cond,c_ast.BinaryOp))
            if isinstance(n.cond,c_ast.BinaryOp):
                if n.cond.op not in '<=>==' :
                    #print('check')
                    self.interupted_flag = True

            return_string = self.visit(n.cond)

            if len(self.output_stack) !=0:

                #return_string = ""
                for item in self.output_stack:
                    prefix += item

                self.output_stack = []
            #s+= return_string
            self.interupted_flag = False
        s += prefix
        s +=  'if ('
        s += return_string
        s += ')\n'
        s += self._generate_stmt(n.iftrue, add_indent=True)
        if n.iffalse:
            s += self._make_indent() + 'else\n'
            s += self._generate_stmt(n.iffalse, add_indent=True)

        if isinstance(n.cond,c_ast.BinaryOp):
            if n.cond.op not in '<=>==' :
                self.interupted_flag = False
        self.interupted_flag = temp_interupted_flag
        return s

    def visit_For(self, n):
        temp_flag = self.interupted_flag
        s = 'for ('
        self.interupted_flag = True; #strict grammar, cannot modify or inject mpfr here
        if n.init: s += self.visit(n.init)
        s += ';'
        if n.cond: s += ' ' + self.visit(n.cond)
        s += ';'
        if n.next: s += ' ' + self.visit(n.next)
        self.interupted_flag = False;
        s += '){\n'
        #make sure correct behaviour of single statement for. Add backets

        self.interupted_flag = temp_flag

        s += self._generate_stmt(n.stmt, add_indent=True)
        s += '\n'+ self._make_indent()+self._make_indent()+'}\n'
        return s

    def visit_While(self, n):
        s = 'while ('
        if n.cond: #s += self.visit(n.cond)
            return_string = self.visit(n.cond)
            if len(self.output_stack) !=0:
                return_string = ""
                for item in self.output_stack:
                    return_string += item
                s+= return_string
                self.output_stack = []
        s += ')\n'
        s += self._generate_stmt(n.stmt, add_indent=True)
        return s

    def visit_DoWhile(self, n):
        s = 'do\n'
        s += self._generate_stmt(n.stmt, add_indent=True)
        s += self._make_indent() + 'while ('
        if n.cond: #s += self.visit(n.cond)
            return_string = self.visit(n.cond)
            if len(self.output_stack) !=0:
                return_string = ""
                for item in self.output_stack:
                    return_string += item
                s+= return_string
                self.output_stack = []
        s += ');'
        return s

    def visit_Switch(self, n):
        s = 'switch (' + self.visit(n.cond) + ')\n'
        s += self._generate_stmt(n.stmt, add_indent=True)
        return s

    def visit_Case(self, n):
        s = 'case ' + self.visit(n.expr) + ':\n'
        for stmt in n.stmts:
            s += self._generate_stmt(stmt, add_indent=True)
        return s

    def visit_Default(self, n):
        s = 'default:\n'
        for stmt in n.stmts:
            s += self._generate_stmt(stmt, add_indent=True)
        return s

    def visit_Label(self, n):
        return n.name + ':\n' + self._generate_stmt(n.stmt)

    def visit_Goto(self, n):
        return 'goto ' + n.name + ';'

    def visit_EllipsisParam(self, n):
        return '...'

    def visit_Struct(self, n):
        return self._generate_struct_union(n, 'struct')

    def visit_Typename(self, n):
        return self._generate_type(n.type)

    def visit_Union(self, n):
        return self._generate_struct_union(n, 'union')

    def visit_NamedInitializer(self, n):
        s = ''
        for name in n.name:
            if isinstance(name, c_ast.ID):
                s += '.' + name.name
            elif isinstance(name, c_ast.Constant):
                s += '[' + name.value + ']'
        s += ' = ' + self._visit_expr(n.expr)
        return s

    def visit_FuncDecl(self, n):
        return self._generate_type(n)

    def _generate_struct_union(self, n, name):
        """ Generates code for structs and unions. name should be either
            'struct' or union.
        """
        s = name + ' ' + (n.name or '')
        if n.decls:
            s += '\n'
            s += self._make_indent()
            self.indent_level += 2
            s += '{\n'
            for decl in n.decls:
                s += self._generate_stmt(decl)
            self.indent_level -= 2
            s += self._make_indent() + '}'
        return s

    def _generate_stmt(self, n, add_indent=False):
        """ Generation from a statement node. This method exists as a wrapper
            for individual visit_* methods to handle different treatment of
            some statements in this context.
        """
        typ = type(n)
        if add_indent: self.indent_level += 2
        indent = self._make_indent()
        if add_indent: self.indent_level -= 2

        if typ in (
                c_ast.Decl, c_ast.Assignment, c_ast.Cast, c_ast.UnaryOp,
                c_ast.BinaryOp, c_ast.TernaryOp, c_ast.FuncCall, c_ast.ArrayRef,
                c_ast.StructRef, c_ast.Constant, c_ast.ID, c_ast.Typedef,
                c_ast.ExprList):
            # These can also appear in an expression context so no semicolon
            # is added to them automatically
            #
            return indent + self.visit(n) + ';\n'
        elif typ in (c_ast.Compound,):
            # No extra indentation required before the opening brace of a
            # compound - because it consists of multiple lines it has to
            # compute its own indentation.
            #
            return self.visit(n)
        else:
            return indent + self.visit(n) + '\n'

    def _generate_decl(self, n):
        """ Generation from a Decl node.
        """
        s = ''
        if n.funcspec: s = ' '.join(n.funcspec) + ' '
        if n.storage: s += ' '.join(n.storage) + ' '
        s += self._generate_type(n.type)
        return s

    def _generate_type(self, n, modifiers=[]):
        """ Recursive generation from a type node. n is the type node.
            modifiers collects the PtrDecl, ArrayDecl and FuncDecl modifiers
            encountered on the way down to a TypeDecl, to allow proper
            generation from it.
        """
        typ = type(n)
        #~ print(n, modifiers)

        if typ == c_ast.TypeDecl:
            s = ''
            if n.quals: s += ' '.join(n.quals) + ' '
            s += self.visit(n.type)

            nstr = n.declname if n.declname else ''
            # Resolve modifiers.
            # Wrap in parens to distinguish pointer to array and pointer to
            # function syntax.
            #
            for i, modifier in enumerate(modifiers):
                if isinstance(modifier, c_ast.ArrayDecl):
                    if (i != 0 and isinstance(modifiers[i - 1], c_ast.PtrDecl)):
                        nstr = '(' + nstr + ')'
                    nstr += '[' + self.visit(modifier.dim) + ']'
                elif isinstance(modifier, c_ast.FuncDecl):
                    if (i != 0 and isinstance(modifiers[i - 1], c_ast.PtrDecl)):
                        nstr = '(' + nstr + ')'
                    nstr += '(' + self.visit(modifier.args) + ')'
                elif isinstance(modifier, c_ast.PtrDecl):
                    if modifier.quals:
                        nstr = '* %s %s' % (' '.join(modifier.quals), nstr)
                    else:
                        nstr = '*' + nstr
            if nstr: s += ' ' + nstr
            return s
        elif typ == c_ast.Decl:
            return self._generate_decl(n.type)
        elif typ == c_ast.Typename:
            return self._generate_type(n.type)
        elif typ == c_ast.IdentifierType:
            return ' '.join(n.names) + ' '
        elif typ in (c_ast.ArrayDecl, c_ast.PtrDecl, c_ast.FuncDecl):
            return self._generate_type(n.type, modifiers + [n])
        else:
            return self.visit(n)

    def _parenthesize_if(self, n, condition):
        """ Visits 'n' and returns its string representation, parenthesized
            if the condition function applied to the node returns True.
        """
        s = self._visit_expr(n)
        if condition(n):
            return '(' + s + ')'
        else:
            return s

    def _parenthesize_unless_simple(self, n):
        """ Common use case for _parenthesize_if
        """
        return self._parenthesize_if(n, lambda d: not self._is_simple_node(d))

    def _is_simple_node(self, n):
        """ Returns True for nodes that are "simple" - i.e. nodes that always
            have higher precedence than operators.
        """
        return isinstance(n,(   c_ast.Constant, c_ast.ID, c_ast.ArrayRef,
                                c_ast.StructRef, c_ast.FuncCall))
