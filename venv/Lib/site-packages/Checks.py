from inspect import signature
import sys, traceback

"""
    This framework using annotations, it is for adding
    in an easy way functionality to function,
    in spasipc for checking conditions on an argument of
    the function and raise an error with detail,
    if the condition is not vaild
    

    Example to use it:
    check if the argument if a integer

    @check
    def print_integer(number : IsInteger):
        print(number)

    @check - is a decorator is for executing
    the IsInteger function with the value of number
    rasie an error is its not Integer

    Anoter example:
    check if first argument is a number
    bigger than 10
    and second arg is string

    @check
    def print_message(number : (BiggerThan, 10), msg : IsString):
        print(msg + ' ' + str(number))

    Using function in the annotation that is with more than one
    argument, use a parenthasis in the annotation place as
    that the function is first and then the other values
    BiggerThan is a function with 2 args BiggerThan(value, compare_to)
    so in this example it will execute like this: BiggerThan(number, 10)
"""


def is_instance(value, var):
    """
        Use isinstance builtin function
        and raise custom annotation error
    """
    
    if(isinstance(value, str)):
        condition = 'isinstance("{}", {})'.format(value, var.__name__)
    else:
        condition = 'isinstance({}, {})'.format(value, var.__name__)
    message = 'The value {} is not an {}'.format(value, var.__name__)
    check_annotation_error(condition, message)

def call_function(tb_stack):
    """ Return the function that uses the annotation """

    # Counter place in tb_stack
    i = 0
    call_func = []
    temp_tb = []

    # This loop need to find the call to ann[name][0](val, ann[name][1])
    # ann[name](val) function - where they are in the check wraper(decator)
    # Then the function with the annotation is in the place before it
    # tb_stack[i].splitlines() spilt it to 2 strings - place of the traceback(file, line, function)
    #  and the function call to other function for example :
    # ['File "C:\Users\...\Framework.py", line 170, in warpper',
    #  'ann[name][0](val, ann[name][1])']
    while(i != len(tb_stack)):
        temp_tb = tb_stack[i].splitlines()
        if('ann[name][0](val, *ann[name][1:])' in temp_tb[1] or 'ann[name](val)' in temp_tb[1]):
            call_func = tb_stack[i-1]
            break
        i = i + 1
    return call_func.splitlines()[1]

def print_AnnoError(tb_stack, message):
    """
        Print the annotationerror - custom error
        for this framework
    """
    
    call_func = call_function(tb_stack).strip(' ')
    message = 'AnnotationError: In Function {}\n{}'.format(call_func, message)
    for tb in tb_stack:
        print(tb[:-1], file=sys.stderr)
    print(message, file=sys.stderr)

def check_annotation_error(condition, message):
    """ Check annotion error use assert to raise the error"""

    try:
        assert eval(condition)
    except AssertionError:
        # The first 3 items in the list are system
        # and fixed so there is no use to show them
        tb_stack = traceback.format_stack()[3:]
        print_AnnoError(tb_stack, message)
        sys.exit()

def IsInteger(value):
    is_instance(value, int)

def IsFloat(value):
    is_instance(value, float)

def IsString(value):
    is_instance(value, str)

def IsChar(value):
    IsString(value)
    message = 'The vaule {} is not char'.format(value)
    condition = 'len("{}") == 1'.format(value)
    check_annotation_error(condition, message)

def BiggterThan0(value):
    condition = '{} > 0'.format(value)
    check_annotation_error(condition, 'Vaule {} need to be bigger the 0'.format(value))

def SmallerThan0(value):
    condition = '{} < 0'.format(value)
    check_annotation_error(condition, 'Vaule {} need to be smaller the 0'.format(value))
        
def EqualTo0(value):
    condition = '{} == 0'.format(value)
    check_annotation_error(condition, 'Vaule {} need to be equal to 0'.format(value))

def BiggerThan(value, *args, func_name='BiggerThan'):
    message = 'There is no value to compare, check the annotaion'
    message = message + '\nannotaion of {} should look ({}, 1)'.format(func_name,
                                                                       func_name)
    check_annotation_error('len({}) > 0'.format(args), message)
    for compare_to in args:
        condition = '{} > {}'.format(value, compare_to)
        message = 'Vaule {} need to be bigger than {}'.format(value, compare_to)
        check_annotation_error(condition, message)

def SmallerThan(value, *args, func_name='SmallerThan'):
    message = 'There is no value to compare, check the annotaion'
    message = message + '\nannotaion of {} should look ({}, 1)'.format(func_name,
                                                                       func_name)
    check_annotation_error('len({}) > 0'.format(args), message)
    for compare_to in args:
        condition = '{} < {}'.format(value, compare_to)
        message = 'Vaule {} need to be smaller than {}'.format(value, compare_to)
        check_annotation_error(condition, message)
        
def EqualTo(value, *args, func_name='EqualTo'):
    message = 'There is no value to compare, check the annotaion'
    message = message + '\nannotaion of {} should look ({}, 1)'.format(func_name,
                                                                       func_name)
    check_annotation_error('len({}) > 0'.format(args), message)
    for compare_to in args:
        condition = '{} == {}'.format(value, compare_to)
        message = 'Vaule {} need to be equal to {}'.format(value, compare_to)
        check_annotation_error(condition, message)
 
def IntEqualTo0(value):
    IsInteger(value)
    EqualTo0(value)

def IntSmallerThan0(value):
    IsInteger(value)
    SmallerThan0(value)
    
def IntBiggterThan0(value):
    IsInteger(value)
    BiggterThan0(value)

def FloatEqualTo0(value):
    IsFloat(value)
    EqualTo0(value)

def FloatSmallerThan0(value):
    IsFloat(value)
    SmallerThan0(value)
    
def FloatBiggterThan0(value):
    IsFloat(value)
    BiggterThan0(value)

def IntEqualTo(value, compare_to):
    IsInteger(value)
    if(isinstance(compare_to, int) or isinstance(compare_to, float)):
        EqualTo(value, compare_to, func_name='IntEqualTo')
    else:
        check_annotation_error('0', 'The value to compare to need to be a number')

def IntSmallerThan(value, compare_to):
    IsInteger(value)
    if(isinstance(compare_to, int) or isinstance(compare_to, float)):
        SmallerThan(value, compare_to, func_name='IntSmallerThan')
    else:
        check_annotation_error('0', 'The value to compare to need to be a number')

def IntBiggerThan(value, compare_to):
    IsInteger(value)
    if(isinstance(compare_to, int) or isinstance(compare_to, float)):
        BiggerThan(value, compare_to, func_name='IntBiggerThan')
    else:
        check_annotation_error('0', 'The value to compare to need to be a number')

def FloatEqualTo(value, compare_to):
    IsFloat(value)
    if(isinstance(compare_to, int) or isinstance(compare_to, float)):
        EqualTo(value, compare_to, func_name='FloatEqualTo')
    else:
        check_annotation_error('0', 'The value to compare to need to be a number')

def FloatSmallerThan(value, compare_to):
    IsFloat(value)
    if(isinstance(compare_to, int) or isinstance(compare_to, float)):
        SmallerThan(value, compare_to, func_name='FloatSmallerThan')
    else:
        check_annotation_error('0', 'The value to compare to need to be a number')

def FloatBiggerThan(value, compare_to):
    IsFloat(value)
    if(isinstance(compare_to, int) or isinstance(compare_to, float)):
        BiggerThan(value, compare_to, func_name='FloatSmallerThan')
    else:
        check_annotation_error('0', 'The value to compare to need to be a number')
       
def check(func):
    """
        This decorator check if there is any annotations
        in the givan function, annotations are look like this
        func(var : annotaion) and apply then the annotation
        function for example:
        func(5: IsInteger) - execute IsInteger(5)
        func(5: (BiggerThan, 4)) - execute BiggerThan(5,4)
    """
    
    # Signature(func) tuple of var name and the annotations
    # for func(a:IntBT0,b) return
    # (a:<function IntBT0 at 0x02D8F618>, b)
    # sing.bind - bind the args with the vars
    # for func(1,2) return <BoundArguments (a=1, b=2)>
    # Then check if a var in the ann dict,
    # if it there check is the ann is not a tuple
    # for example func(a:(IntEqualTo, 2)),
    # execute the IntEqualTo(a,2)
    # if not tuple execute the annotation of that var with its value
    # add1(1:IntBT0) run the function IntBT0(1)

    sig = signature(func)
    ann = func.__annotations__
    def warpper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        for name, val in bound.arguments.items():
            if(name in ann):
                if(isinstance(ann[name], tuple)):
                    # *ann[name][1:] - as arguments for
                    # custom functions that need more than 1
                    ann[name][0](val, *ann[name][1:])
                else:
                    ann[name](val)
        return func(*args, **kwargs)
    return warpper


