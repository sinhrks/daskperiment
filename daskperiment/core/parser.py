import argparse
import ast

from pyparsing import Word, alphanums, printables, ParseException
PARAM = Word(alphanums + '_') + '=' + Word(printables)


def parse_command_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int)

    knowns, unknowns = parser.parse_known_args()
    seed = knowns.seed

    parameters = {}
    for expr in unknowns:
        lvalue, rvalue = parse_parameter(expr)
        parameters[lvalue] = rvalue
    return seed, parameters


def parse_parameter(param_expr):
    try:
        lvalue, _, rvalue = PARAM.parseString(param_expr)
        return lvalue, ast.literal_eval(rvalue)
    except (SyntaxError, ParseException):
        msg = 'Parameters must be passed with key=value form: {}'
        raise SyntaxError(msg.format(param_expr))
