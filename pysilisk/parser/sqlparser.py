from pyparsing import Word, Literal, Group, QuotedString, Suppress, Forward
from pyparsing import alphas, alphanums, CaselessKeyword, ZeroOrMore
from pyparsing import Optional, delimitedList, Regex

# This code is based on:
# http://pyparsing.wikispaces.com/file/view/simpleSQL.py
# https://pyparsing.wikispaces.com/file/view/select_parser.py
# https://github.com/tgulacsi/plsql_parser
# http://stackoverflow.com/questions/16909380/sql-parsing-using-pyparsing

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

# Create and drop database Statements
database_name = identifier.setResultsName('db_name')
create_database_stmt = CREATE + DATABASE + database_name
drop_db_stmt = DROP + DATABASE + database_name

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
integer_type = INTEGER
float_type = FLOAT
datetime_type = DATETIME
date_type = DATE
string_size = integer_literal.setResultsName('size')
nvarchar_type = Group(VARCHAR + LPAR + string_size + RPAR)
nchar_type = Group(CHAR + LPAR + string_size + RPAR)
data_type = (integer_type|float_type|datetime_type|
             date_type|nvarchar_type|nchar_type).setResultsName('data_type')

# Table
alias = identifier.copy().setResultsName('alias')
simple_table_name = identifier.setResultsName("table_name")
table_name = simple_table_name.copy()

# Column
simple_column_name = identifier.setResultsName("column_name")
fully_qualified_column_name = Group(simple_table_name + dot + simple_column_name)
column_name = fully_qualified_column_name | simple_column_name

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

# From-clause
# bnf-from_table = table ( (AS){0,1} alias)*
from_table = Group(table_name + Optional(Optional(AS) + alias))
from_table = from_table.setResultsName("from_table")
from_tables = delimitedList(from_table)  # tbl1 as t, tbl2 as b,...
from_tables = from_tables.setResultsName("from_tables")
from_clause = Group(FROM + from_tables).setResultsName("from_clause")

# Select Statement
star = Literal("*")
attribute = star|Group(arith_expr + Optional(AS+alias))
projected_attrs = delimitedList(attribute)
projected_attrs = projected_attrs.setResultsName("projected_attributes")
select_stmt = (SELECT + Optional(DISTINCT|ALL) + projected_attrs +
              from_clause  +
              Optional(where_clause))

# Insert statement
# Contrary to standard SQL, our implementation of the Insert-Statement does not
# consider the list-of-columns. To reduce the complexity of the execution of an
# Insert-Stmt, pysilik supports only literals (not arith-expression) in the list
# of values.
#
# <insert> := INSERT INTO <table> VALUES(literal [, literal]*)
insert_stmt = (INSERT + INTO + table_name + VALUES +
              LPAR +
              delimitedList(literal_value).setResultsName('list_values') +
              RPAR)

# Delete Statement
delete_stmt = (DELETE + FROM +table_name + Optional(where_clause))

# Update Statement
# Similar to the insert-stmt, pysilik only supports literal as values
column_and_value = Group(simple_column_name + equal_op + literal_value)
set_col_values = delimitedList(column_and_value)
update_stmt = (UPDATE + table_name +
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
null_constrain = (Group(NOT+NULL)| NULL).setResultsName('null_constrain')
column_definition = (simple_column_name +
                     data_type +
                     Optional(null_constrain))
list_col_defs  = delimitedList(Group(column_definition))
index_definition = INDEX +  index_columns + USING + index_type
create_table_stmt = (CREATE + TABLE + table_name + LPAR +
                     list_col_defs.setResultsName('list_column_defs') +
                     Optional(comma + index_definition) +
                     RPAR)

# Drop table statement
# Only one table at a time
drop_table_stmt = DROP + TABLE + table_name

# SQL =
sql_stmt = (create_database_stmt|drop_db_stmt|
            select_stmt|insert_stmt|delete_stmt|
            update_stmt|create_index_stmt|
            create_table_stmt|drop_table_stmt) + semi_colon

# The following commands will not be implemented in the parser
# but in the console
#
# \h or \help       : help
# \sd               : show all databases
# \u <db-name>      : connect to a database
# \st               : show all user-tables in the db
# \si               : show all user-indices
# \si <idx-name>    : show an index
# \dt <table-name>  : describe a table
