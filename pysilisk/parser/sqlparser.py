from pyparsing import Word, Literal, Group, QuotedString, Suppress, Forward
from pyparsing import alphas, alphanums, CaselessKeyword, ZeroOrMore
from pyparsing import Optional, delimitedList, Regex, Empty, OneOrMore

# This code is based on:
# http://pyparsing.wikispaces.com/file/view/simpleSQL.py
# https://pyparsing.wikispaces.com/file/view/select_parser.py
# https://github.com/tgulacsi/plsql_parser
# http://stackoverflow.com/questions/16909380/sql-parsing-using-pyparsing

# Define keywords
(SELECT, FROM, WHERE, AS, NULL, NOT,AND, OR, DISTINCT, ALL, INSERT, INTO,
 VALUES, DELETE, UPDATE, SET, CREATE, INDEX, USING, BTREE, HASH, ON,
 INTEGER, FLOAT, DATETIME, DATE, VARCHAR, CHAR, TABLE) = map(CaselessKeyword, """SELECT, FROM, WHERE, AS,
 NULL, NOT, AND, OR, DISTINCT, ALL, INSERT, INTO, VALUES, DELETE, UPDATE,
 SET, CREATE, INDEX, USING, BTREE, HASH, ON, INTEGER, FLOAT, DATETIME,
 DATE, VARCHAR, CHAR, TABLE""".replace(",","").split())

NOT_NULL = 'NOT NULL'
keywords = (SELECT|FROM|WHERE|AS|NULL|NOT|AND|OR|DISTINCT|ALL|INSERT|INTO|
            VALUES|DELETE|UPDATE|SET|CREATE|INDEX|USING|BTREE|HASH|ON|
            INTEGER|FLOAT|DATETIME|DATE|VARCHAR|CHAR|TABLE|NOT_NULL)

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

# Data-types
INTEGER_TYPE = INTEGER
FLOAT_TYPE = FLOAT
DATETIME_TYPE = DATETIME
DATE_TYPE = DATE
string_size = integer_literal.setResultsName('size')
VARCHAR_TYPE = Group(VARCHAR + LPAR + string_size + RPAR)
CHAR_TYPE = Group(CHAR + LPAR + string_size + RPAR)
data_type = (INTEGER_TYPE|FLOAT_TYPE|DATETIME_TYPE|
             DATE_TYPE|VARCHAR_TYPE|CHAR_TYPE).setResultsName('data_type')

# Arithmetic expression:
# We use the following grammar as a basis:
#
#      <b-expression> ::= <b-term> [<orop> <b-term>]*
#      <b-term>       ::= <not-factor> [AND <not-factor>]*
#      <not-factor>   ::= [NOT] <b-factor>
#      <b-factor>     ::= <b-literal> | <b-variable> | <relation>
#      <relation>     ::= | <expression> [<relop> <expression]
#      <expression>   ::= <term> [<addop> <term>]*
#      <term>         ::= <signed factor> [<mulop> factor]*
#      <signed factor>::= [<addop>] <factor>
#      <factor>       ::= <integer> | <variable> | (<b-expression>)
#
# Note: Writing a perfect grammar for the boolean and arithmetic expressions
#       are beyond the scope of this project. I followed the approach suggested
#       by Crenshaw [1].
# References:
# [1] http://compilers.iecc.com/crenshaw/tutor6.txt
# [2] http://en.wikipedia.org/wiki/Syntax_diagram
# [3] https://pyparsing.wikispaces.com/file/view/fourFn.py
# [4] http://matt.might.net/articles/grammars-bnf-ebnf/

# Arith-Operators
add_op = Literal("+")
sub_op = Literal("-")
mult_op = Literal("*")
div_op = Literal("/")
mod_op = Literal("%")
add_sub_op = (add_op | sub_op).setResultsName('operator')
mult_div_mod_op = (mult_op | div_op | mod_op).setResultsName('operator')

# Relational-Operators
equal_op = Literal("=")
diff_op = Literal("<>")
less_op = Literal("<")
greater_op  = Literal(">")
less_than_op = Literal("<=")
greater_then_op = Literal(">=")

# expression-nodes
arith_expr = Forward()
term = Forward()
factor = Forward()
signed_factor = Forward()
arith_expr_ = Forward()
term_ = Forward()
bool_factor = Forward()
bool_expr = Forward()
bool_term = Forward()

# Define a function:
funct_name = identifier.copy()
funct_args = Group(Optional(delimitedList(arith_expr)))
funct_call = Group(funct_name + LPAR + funct_args + RPAR).setResultsName('function')

# Define arith-expression
factor << (literal_value|funct_call|column_name|Group(LPAR + bool_expr + RPAR))
signed_factor << Optional(add_sub_op) + factor
term << Group(signed_factor + ZeroOrMore(mult_div_mod_op + factor))
arith_expr << term + ZeroOrMore(add_sub_op + term)

# Define a relation
#     <relation>  ::= <expression> <rel-op> <expression>
#     <rel-op>    ::= =|<> | < | >| <= |  >=
relation_op = diff_op|greater_then_op|less_than_op|greater_op|less_op|equal_op
relation = Group(arith_expr) + ZeroOrMore(relation_op + Group(arith_expr))

# Define boolean-expression
bool_factor << relation
bool_term << Optional(NOT) + bool_factor + ZeroOrMore(AND + Optional(NOT) + bool_factor)
bool_expr << Group(bool_term) + ZeroOrMore(OR + Group(bool_term))

# Where Clause
where_clause = Group(WHERE + bool_expr).setResultsName("where_clause")

# Select Statement
star = Literal("*")
attribute = star|Group(arith_expr + Optional(AS+alias))
projected_attrs = delimitedList(attribute)
projected_attrs = projected_attrs.setResultsName("projected_attributes")
selectStmt = (SELECT + Optional(DISTINCT|ALL) + projected_attrs +
              from_clause  +
              Optional(where_clause))

# Insert statement
# Contrary to standard SQL, our implementation of the Insert-Statement does not
# consider the list-of-columns. To reduce the complexity of the execution of an
# Insert-Stmt, pysilik supports only literals (not arith-expression) in the list
# of values.
#
# <insert> := INSERT INTO <table> VALUES(literal [, literal]*)
insertStmt = (INSERT + INTO + table_name + VALUES +
              LPAR +
              delimitedList(literal_value).setResultsName('list_values') +
              RPAR)

# Delete Statement
deleteStmt = (DELETE + FROM +table_name + Optional(where_clause))

# Update Statement
# Similar to the insert-stmt, pysilik only supports literal as values
column_and_value = Group(simple_column_name + equal_op + literal_value)
set_col_values = delimitedList(column_and_value)
updateStmt = (UPDATE + table_name +
              SET + set_col_values.setResultsName('list_columns_and_values') +
              Optional(where_clause))

# Create-Index Statement
# <create-index> := CREATE INDEX <index-name>
#                   ON <table-name> (list-columns)
#                   USING {BTREE|HASH}
index_name = identifier.setResultsName('index_name')
index_type = (BTREE|HASH).setResultsName('index_type')
index_columns =  (LPAR +
                  delimitedList(simple_column_name) +
                  RPAR)
index_columns = index_columns.setResultsName('list_index_columns')
create_index_stmt = (CREATE + INDEX + index_name + ON + simple_table_name +
                     index_columns +
                     USING + index_type)

# Create-Table Statement
# <create-table> := CREATE TABLE <table-name> (
#                       <column-definitions>
#                       [, <column-definitions>]*
#                       [, INDEX (<list-columns>) USING <index-type>]
#                   )
#  <column-def>  := <column> <data_type> + Optional(NULL|NOT_NULL)

#NOT_NULL = Group(NOT + NULL)
null_constrain = (Group(NOT+NULL)| NULL).setResultsName('null_constrain')
column_definition = (simple_column_name +
                     data_type +
                     Optional(null_constrain))

list_col_defs  = delimitedList(Group(column_definition))
# INDEX (list-columns) USING {btree|hash}
index_definition = INDEX +  index_columns + USING + index_type
create_table_stmt = (CREATE + TABLE + table_name + LPAR +
                     list_col_defs.setResultsName('list_column_defs') +
                     Optional(comma + index_definition) +
                     RPAR)

