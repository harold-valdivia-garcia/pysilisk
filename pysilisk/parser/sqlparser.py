from pyparsing import Word, Literal, Group, QuotedString, Suppress, Forward
from pyparsing import alphas, alphanums, CaselessKeyword, ZeroOrMore
from pyparsing import Optional, delimitedList, Regex, Empty, OneOrMore

# This code is based on:
# http://pyparsing.wikispaces.com/file/view/simpleSQL.py
# https://pyparsing.wikispaces.com/file/view/select_parser.py
# https://github.com/tgulacsi/plsql_parser
# http://stackoverflow.com/questions/16909380/sql-parsing-using-pyparsing

# Define keywords
(SELECT, FROM, WHERE, AS, NULL) = map(CaselessKeyword, """SELECT, FROM,
 WHERE, AS, NULL""".replace(",","").split())
#
keywords = (SELECT|FROM|WHERE|AS|NULL)

# Define and remove dot from the outputs
LPAR,RPAR = map(Suppress, '()')
dot = Literal(".").suppress()
comma = Literal(",").suppress()

# Basic identifier used to define vars, tables, columns
identifier = ~keywords + Word(alphas, alphanums + '_')

alias = identifier.copy().setResultsName('alias')

# Table
simple_table_name = identifier.setResultsName("table_name")
table_name = simple_table_name.copy()

# Column
simple_column_name = identifier.setResultsName("column_name")
fully_qualified_column_name = Group(simple_table_name + dot + simple_column_name)
column_name = fully_qualified_column_name | simple_column_name

# From-clause
# bnf-from_table = table ( (AS){0,1} alias)*
from_table = Group(table_name + Optional(Optional(AS) + alias))
from_table = from_table.setResultsName("from_table")
from_tables = delimitedList(from_table)  # tbl1 as t, tbl2 as b,...
from_tables = from_tables.setResultsName("from_tables")
from_clause = Group(FROM + from_tables).setResultsName("from_clause")

# Literal Values
nonzero_digits = Word('123456789')
integer_literal = Regex(r"([+-]?[1-9][0-9]*|0)")
Literal(".")
num_dot = Literal(".")
real_number_literal = Regex(r"([+-]?[1-9][0-9]*|0)\.[0-9]+")
numeric_literal = real_number_literal | integer_literal
string_literal = QuotedString("'")
literal_value = (numeric_literal|string_literal|NULL)
literal_value = literal_value.setName('literal_value')

# Arithmetic expression:
# We use the following grammar as a basis:
#
#   arithExp   =  term adOp arithExp' | term
#   term       =  factor multOp term | factor
#   factor     =  literal | funct | colname | '('arithExp')'
#   funct      =  functName '('functArgs')'
#   functArgs  =  [ arithExp [',' arithExp]* ]*
#
# Then, we remove the left-recursion since pyparsing does not support it:
#
#   arithExp   =  term arithExp' | term
#   arithExp'  =  addOp term arithExp' | null
#   term       =  factor term'
#   term'      =  multOp factor term' | null
#   factor     =  literal | funct | colname | '('arithExp')'
#   funct      =  functName '('functArgs')'
#   functArgs  =  [ arithExp [',' arithExp]* ]*
#
# References:
# http://en.wikipedia.org/wiki/Syntax_diagram
# http://matt.might.net/articles/grammars-bnf-ebnf/
# https://pyparsing.wikispaces.com/file/view/fourFn.py

# Arith-Operators
add_op = Literal("+")
sub_op = Literal("-")
mult_op = Literal("*")
div_op = Literal("/")
mod_op = Literal("%")
add_sub_op = (add_op | sub_op).setResultsName('operator')
mult_div_mod_op = (mult_op | div_op | mod_op).setResultsName('operator')

# Arith-expression
arith_expr = Forward()
term = Forward()
factor = Forward()
arith_expr_ = Forward()
term_ = Forward()

# Define a function:
funct_name = identifier.copy()
funct_args = Group(Optional(delimitedList(arith_expr)))
funct_call = Group(funct_name + LPAR + funct_args + RPAR).setResultsName('function')
factor = (literal_value.setResultsName('value')|funct_call|
          column_name.setResultsName('column')|Group(LPAR + arith_expr + RPAR))
term_ <<  Optional(mult_div_mod_op + factor + term_)
term << Group(factor + term_)
arith_expr_ << Optional(add_sub_op + term + arith_expr_)
arith_expr << (term + arith_expr_)

# Where Clause
where_clause = Group(WHERE + arith_expr.setResultsName('expression')).setResultsName("where_clause")

# Select Statement
projected_attributes = OneOrMore(arith_expr).setResultsName('projected_attributes')
selectStmt = SELECT +  projected_attributes + from_clause.setResultsName("from_clause") + Optional(where_clause)

