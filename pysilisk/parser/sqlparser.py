# Copyright (C) 2015 Harold Valdivia-Garcia
#
# A simple parser for sql written in python with a decent support
# for arithmetic and boolean expressions
#
# This code is based on:
# http://pyparsing.wikispaces.com/file/view/simpleSQL.py
# https://pyparsing.wikispaces.com/file/view/select_parser.py
# https://github.com/tgulacsi/plsql_parser
# http://stackoverflow.com/questions/16909380/sql-parsing-using-pyparsing
#
# The references above could not handle some complex arith-expression or
# they were extremely slow. So, I decided to implemented by myself.
#
# The statements supported are:
#   INSERT
#   DELETE
#   UPDATE
#   SELECT
#   DROP TABLE
#   CREATE TABLE
#   DROP INDEX
#   CREATE INDEX

from pyparsing import Word, Literal, Group, QuotedString, Suppress, Forward
from pyparsing import alphas, alphanums, CaselessKeyword, ZeroOrMore
from pyparsing import Optional, delimitedList, Regex

# Define keywords
(SELECT, FROM, WHERE, AS, NULL, NOT,AND, OR, DISTINCT, ALL, INSERT, INTO,
 VALUES, DELETE, UPDATE, SET, CREATE, INDEX, USING, BTREE, HASH,
 ON, INTEGER, FLOAT, DATETIME, DATE, VARCHAR, CHAR, TABLE, DATABASE,
 DROP) = map(CaselessKeyword, """SELECT, FROM, WHERE, AS, NULL, NOT, AND,
 OR, DISTINCT, ALL, INSERT, INTO, VALUES, DELETE, UPDATE, SET, CREATE,
 INDEX, USING, BTREE, HASH, ON, INTEGER, FLOAT, DATETIME, DATE, VARCHAR,
 CHAR, TABLE, DATABASE, DROP""".replace(",","").split())

keywords = (SELECT|FROM|WHERE|AS|NULL|NOT|AND|OR|DISTINCT|ALL|INSERT|INTO|
            VALUES|DELETE|UPDATE|SET|CREATE|INDEX|USING|BTREE|HASH|ON|
            INTEGER|FLOAT|DATETIME|DATE|VARCHAR|CHAR|TABLE|DATABASE|DROP)

# Define basic symbols
LPAR, RPAR = map(Suppress, '()')
dot = Literal(".").suppress()
comma = Literal(",").suppress()
semi_colon  = Literal(";").suppress()

# Basic identifier used to define vars, tables, columns
identifier = ~keywords + Word(alphas, alphanums + '_')

# Literal Values
integer_literal = Regex(r"([+-]?[1-9][0-9]*|0)")
integer_literal = integer_literal.setResultsName('integer_literal')
float_literal = Regex(r"([+-]?[1-9][0-9]*|0)\.[0-9]+")
float_literal = float_literal.setResultsName('float_literal')
numeric_literal = float_literal | integer_literal
string_literal = QuotedString("'").setResultsName('string_literal')
literal_value = (numeric_literal|string_literal|NULL)

# SQL-Type-names
INTEGER = INTEGER.setResultsName('type_name')
FLOAT = FLOAT.setResultsName('type_name')
DATETIME = DATETIME.setResultsName('type_name')
DATE = DATE.setResultsName('type_name')
VARCHAR = VARCHAR.setResultsName('type_name')
CHAR = CHAR.setResultsName('type_name')

# SQL-Data-types
integer_type = Group(INTEGER)
float_type = Group(FLOAT)
datetime_type = Group(DATETIME)
date_type = Group(DATE)
string_size = integer_literal.setResultsName('size')
nvarchar_type = Group(VARCHAR + LPAR + string_size + RPAR)
nchar_type = Group(CHAR + LPAR + string_size + RPAR)
data_type = (integer_type|float_type|datetime_type|
             date_type|nvarchar_type|nchar_type).setResultsName('data_type')

# Table identifier
table_name = identifier.setResultsName("table_name")

# Column identifier
column_name = identifier.setResultsName("column_name")
fully_qualified_column_name = table_name + dot + column_name
column = Group(fully_qualified_column_name | column_name)
column = column.setResultsName('column')

# Boolean and Arithmetic expression:
# =================================
# Bool and Arith expressions are used in the where clause ( WHERE a > 3*c) and
# in the projections (SELECT days/7 AS weeks). We based our expressions based on
# the following grammar as a basis:
#
#      <bool-expr>      ::= <bool-term> [OR <bool-term>]*
#      <bool-term>      ::= <not-factor> [AND <not-factor>]*
#      <bool-factor>    ::= [NOT] <predicate>
#      <predicate>      ::= | <arith-expr> [<pred-op> <arith-expr>]
#      <arith-expr>     ::= <term> [<add-op> <term>]*
#      <term>           ::= <signed factor> [<mult-op> factor]*
#      <signed factor>  ::= [<sign>] <factor>
#      <factor>         ::= <integer> | <variable>| function | (<bool-expr>)
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
sign_op = add_sub_op.setResultsName('sign_op')

# Predicate Operators (a.k.a Relational-Operators or Comparison-Operators)
equal_op = Literal("=")
diff_op = Literal("<>")
less_op = Literal("<")
greater_op  = Literal(">")
less_than_op = Literal("<=")
greater_then_op = Literal(">=")

# Expression-nodes
arith_expr = Forward().setResultsName('arith_expr')
term = Forward().setResultsName('term')
factor = Forward().setResultsName('factor')
signed_factor = Forward().setResultsName('signed_factor')
bool_factor = Forward().setResultsName('bool_factor')
bool_expr = Forward().setResultsName('bool_expr')
bool_term = Forward().setResultsName('bool_term')

# Define a function
funct_name = identifier.copy()
funct_args = Group(Optional(delimitedList(arith_expr)))
funct_call = Group(funct_name + LPAR + funct_args + RPAR).setResultsName('function')

# Define arith-expression
#      <arith-expr>     ::= <term> [<add-op> <term>]*
#      <term>           ::= <signed factor> [<mult-op> factor]*
#      <signed factor>  ::= [<sign>] <factor>
#      <factor>         ::= <integer> | <variable>| function | (<bool-expr>)
factor << (Group(literal_value)|funct_call|column|Group(LPAR + bool_expr + RPAR))
signed_factor << Group(Optional(sign_op) + factor)
term << Group(signed_factor + ZeroOrMore(mult_div_mod_op + factor))
arith_expr << Group(term + ZeroOrMore(add_sub_op + term))

# Define a predicate
#      <predicate>      ::= <arith-expr> [<pred-op> <arith-expr>]
#      <pred-op>        ::= <> | < | >| <= |  >= | =
predicate_op = diff_op|greater_then_op|less_than_op|greater_op|less_op|equal_op
predicate = Group(arith_expr + Optional(predicate_op + arith_expr))
predicate = predicate.setResultsName('predicate')

# Define boolean-expression
#      <bool-expr>      ::= <bool-term> [OR <bool-term>]*
#      <bool-term>      ::= <not-factor> [AND <not-factor>]*
#      <bool-factor>    ::= [NOT] <predicate>
bool_factor << Group(Optional(NOT) + predicate)
bool_term << Group(bool_factor + ZeroOrMore(AND  + bool_factor))
bool_expr <<  Group(bool_term + ZeroOrMore(OR + bool_term))

# Where Clause (used in SELECT, DELETE and UPDATE)
where_clause = Group(WHERE + bool_expr).setResultsName("where_clause")

# SQL-STATEMENT DEFINITIONS:

# Insert statement
# Contrary to standard SQL, our implementation of the Insert-Statement does not
# consider the list-of-columns. To reduce the complexity of the execution of an
# Insert-Stmt, pysilik supports only literals (not arith-expression) in the list
# of values.
#      <insert> := INSERT INTO <table> VALUES(literal [, literal]*)
insert_values = delimitedList(literal_value).setResultsName('list_values')
insert_stmt = INSERT + INTO + table_name + VALUES +LPAR + insert_values + RPAR

# Delete Statement
delete_stmt = (DELETE + FROM +table_name + Optional(where_clause))

# Update Statement
# Similar to the insert-stmt, pysilik only supports literal as values
column_and_value = Group(column_name + equal_op + literal_value)
set_col_values = delimitedList(column_and_value)
update_stmt = (UPDATE + table_name +
              SET + set_col_values.setResultsName('list_columns_and_values') +
              Optional(where_clause))

# Select Statement
#      <from-table> := <table> [AS  <alias>] [, <table> [AS  <alias>]]*
alias = identifier.copy().setResultsName('alias')
from_table = Group(table_name + Optional(Optional(AS) + alias))
from_table = from_table.setResultsName("from_table")
from_tables = delimitedList(from_table)  # tbl1 as t, tbl2 as b,...
from_tables = from_tables.setResultsName("from_tables")
from_clause = Group(FROM + from_tables).setResultsName("from_clause")
#      <projected>  := "*" | <expr> [AS  <alias>] [, <expr> [AS  <alias>]]*
star = Literal("*")
attribute = star|Group(arith_expr + Optional(AS+alias))
projected_attrs = delimitedList(attribute)
projected_attrs = projected_attrs.setResultsName("projected_attributes")
#      <select> := SELECT <projected> <from> [<where>]
select_stmt = (SELECT + Optional(DISTINCT|ALL) + projected_attrs +
              from_clause  +
              Optional(where_clause))

# Create-Index Statement
#      <create-index> := CREATE INDEX <index-name>
#                        ON <table-name> (list-columns)
#                        USING {BTREE|HASH}
index_name = identifier.setResultsName('index_name')
index_type = (BTREE|HASH).setResultsName('index_type')
index_columns =  (LPAR + delimitedList(column_name) + RPAR)
index_columns = index_columns.setResultsName('list_index_columns')
create_index_stmt = (CREATE + INDEX + index_name + ON + table_name +
                     index_columns +
                     USING + index_type)

# Create-Table Statement
#       <create-table> := CREATE TABLE <table-name> (
#                             <column-definitions>
#                             [, <column-definitions>]*
#                             [, INDEX (<list-columns>) USING <index-type>]
#                         )
#  <column-def>  := <column> <data_type> + Optional(NULL|NOT_NULL)
null_constrain = (Group(NOT+NULL)|Group(NULL)).setResultsName('null_constrain')
column_definition = column_name + data_type + Optional(null_constrain)
list_col_defs  = delimitedList(Group(column_definition))
index_definition = INDEX + ON + index_columns + USING + index_type
create_table_stmt = (CREATE + TABLE + table_name + LPAR +
                     list_col_defs.setResultsName('list_column_defs') +
                     Optional(comma + index_definition) +
                     RPAR)

# Drop table and index Statements
drop_table_stmt = DROP + TABLE + table_name
drop_index_stmt = DROP + INDEX  + index_name + ON + table_name

# SQL Statement
SQL_GRAMMAR = (select_stmt.setResultsName('SELECT')|
               insert_stmt.setResultsName('INSERT')|
               delete_stmt.setResultsName('DELETE')|
               update_stmt.setResultsName('UPDATE')|
               create_index_stmt.setResultsName('CREATE_INDEX')|
               create_table_stmt.setResultsName('CREATE_TABLE')|
               drop_table_stmt.setResultsName('DROP_TABLE')|
               drop_index_stmt.setResultsName('DROP_INDEX')) + semi_colon


# Other commands such as 'create-db', 'use-db' 'help' or 'quit' are not
# supported by the grammar. These commands and others are implemented in
# the console (cli) as meta-commands

