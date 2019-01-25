import argparse
import ast

from pyparsing import Word, alphanums, printables, ParseException
PARAM = Word(alphanums + '_') + '=' + Word(printables)


def parse_command_arguments():
    parser = argparse.ArgumentParser()
    _, unknowns = parser.parse_known_args()

    parameters = {}
    for expr in unknowns:
        lvalue, rvalue = parse_parameter(expr)
        parameters[lvalue] = rvalue
    return parameters


def parse_parameter(param_expr):
    try:
        lvalue, _, rvalue = PARAM.parseString(param_expr)
        return lvalue, ast.literal_eval(rvalue)
    except (SyntaxError, ParseException):
        msg = 'Parameters must be passed with key=value form: {}'
        raise SyntaxError(msg.format(param_expr))
