# Copyright (C) 2015 Harold Valdivia-Garcia
#
# A simple parser for sql written in python with a decent support
# for arithmetic and boolean expressions
#
# This code is based on:
#   http://pyparsing.wikispaces.com/file/view/simpleSQL.py
#   https://pyparsing.wikispaces.com/file/view/select_parser.py
#   https://github.com/tgulacsi/plsql_parser
#   http://stackoverflow.com/questions/16909380/sql-parsing-using-pyparsing
#
# The references above could not handle some complex arith-expression or
# they were extremely slow. So, I decided to implement it by myself.
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
#
# Some grammar rules were borrowed from:
#   http://www.savage.net.au/SQL/sql-92.bnff
#   http://www.contrib.andrew.cmu.edu/~shadow/sql/sql2bnf.aug92.txt

from pyparsing import Word, Literal, Group, QuotedString, Suppress, Forward
from pyparsing import alphas, alphanums, CaselessKeyword, ZeroOrMore
from pyparsing import Optional, delimitedList, Regex

# Define keywords
# Note: Don't remove whitespaces otherwise
#       replace(",", "").split() won't work
(SELECT, FROM, WHERE, AS, NULL, NOT,AND, OR, DISTINCT, ALL, INSERT,
 INTO, VALUES, DELETE, UPDATE, SET, CREATE, INDEX, USING, BTREE, HASH,
 ON, INTEGER, FLOAT, DATETIME, DATE, VARCHAR, CHAR, TABLE, DATABASE,
 DROP, ORDER, BY, ASC, DESC) = map(CaselessKeyword, """SELECT, FROM,
 WHERE, AS, NULL, NOT, AND, OR, DISTINCT, ALL, INSERT, INTO, VALUES,
 DELETE, UPDATE, SET, CREATE, INDEX, USING, BTREE, HASH, ON, INTEGER,
 FLOAT, DATETIME, DATE, VARCHAR, CHAR, TABLE, DATABASE, DROP, ORDER,
 BY, ASC, DESC""".replace(",","").split())

keywords = (SELECT|FROM|WHERE|AS|NULL|NOT|AND|OR|DISTINCT|ALL|INSERT|
            INTO|VALUES|DELETE|UPDATE|SET|CREATE|INDEX|USING|BTREE|HASH|
            ON|INTEGER|FLOAT|DATETIME|DATE|VARCHAR|CHAR|TABLE|DATABASE|
            DROP|ORDER|BY|ASC|DESC)

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
# in the projections (SELECT days/7 AS weeks). We based our expressions on the
# following grammar:
#
#      <bool-expr>      ::= <bool-term> [OR <bool-term>]*
#      <bool-term>      ::= <not-factor> [AND <not-factor>]*
#      <bool-factor>    ::= [NOT] <predicate>
#      <predicate>      ::= <arith-expr> [<pred-op> <arith-expr>]
#      <arith-expr>     ::= <term> [<add-op> <term>]*
#      <term>           ::= <signed factor> [<mult-op> factor]*
#      <signed factor>  ::= [<sign>] <factor>
#      <factor>         ::= <literal> | <column> | function | (<bool-expr>)
#
# Note: Writing a perfect grammar for boolean and arithmetic expressions are
#       beyond the scope of this project. I followed the approach suggested
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
neq_op = Literal("<>")
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
funct_name = identifier.setResultsName('funct_name')
funct_args = Group(Optional(delimitedList(arith_expr)))
funct_args = funct_args.setResultsName('funct_args')
funct_call = Group(funct_name + LPAR + funct_args + RPAR).setResultsName('function')

# Define arith-expression
#      <arith-expr>     ::= <term> [<add-op> <term>]*
#      <term>           ::= <signed factor> [<mult-op> factor]*
#      <signed factor>  ::= [<sign>] <factor>
#      <factor>         ::= <literal> | <column> | function | (<bool-expr>)
factor << (Group(literal_value)|Group(funct_call)|Group(column)|Group(LPAR + bool_expr + RPAR))
signed_factor << Group(Optional(sign_op) + factor)
term << Group(signed_factor + ZeroOrMore(mult_div_mod_op + factor))
arith_expr << Group(term + ZeroOrMore(add_sub_op + term))

# Define a predicate
#      <predicate>      ::= <arith-expr> [<pred-op> <arith-expr>]
#      <pred-op>        ::= <> | < | >| <= |  >= | =
predicate_op = neq_op|greater_then_op|less_than_op|greater_op|less_op|equal_op
predicate = Group(arith_expr + Optional(predicate_op + arith_expr))
predicate = predicate.setResultsName('predicate')

# Define boolean-expression
#      <bool-expr>      ::= <bool-term> [OR <bool-term>]*
#      <bool-term>      ::= <not-factor> [AND <not-factor>]*
#      <bool-factor>    ::= [NOT] <predicate>
not_op = NOT.setResultsName('not_op')
bool_factor << Group(Optional(not_op) + predicate)
bool_term << Group(bool_factor + ZeroOrMore(AND  + bool_factor))
bool_expr <<  Group(bool_term + ZeroOrMore(OR + bool_term))

# Where Clause (used in SELECT, DELETE and UPDATE)
where_clause = Group(WHERE + bool_expr).setResultsName("where_clause")


# SQL-STATEMENT DEFINITIONS:


# Insert statement
# ================
# Contrary to standard SQL, our implementation of the Insert-Statement does not
# consider the list-of-columns. To reduce the complexity of the execution of an
# Insert-Stmt, pysilik supports only literals (not arith-expression) in the list
# of values.
#      <insert> ::= INSERT INTO <table> VALUES(literal [, literal]*)
insert_values = delimitedList(Group(literal_value)).setResultsName('insert_values')
insert_stmt = INSERT + INTO + table_name + VALUES +LPAR + insert_values + RPAR

# Delete Statement
# ================
delete_stmt = (DELETE + FROM +table_name + Optional(where_clause))


# Update Statement
# ================
#      <update>          ::= UPDATE <table>
#                            SET <list-set-clause>
#                            [<where-clause>]
#      <list-set-clause> ::= <set-clause> [, <set-clause>]*
#      <set-clause>      ::= <colname> = <update-source>
#      <update-source>   ::= <arith-expr>
update_source = arith_expr.setResultsName('update_source')
set_clause = Group(column_name + equal_op + update_source)
list_set_clauses = delimitedList(set_clause).setResultsName('list_set_clauses')
update_stmt = (UPDATE + table_name +
               SET + list_set_clauses +
               Optional(where_clause))

# Select Statement
# ================
#      <select>         ::= SELECT [DISTINCT] <select list>
#                           <from-clause>
#                           [<where-clause>]
#                           [<order-by-clause>]
#
#      <select list>    ::= <start> | <derived-col> [<comma> <derived-col>]*
#      <derived-col>    ::= <arith-expr> [AS <alias>]
#
#      <from-clause>    ::= FROM <list-tables>
#      <list-tables>    ::= <from-table> [<comma> <from-table>]*
#      <from-table>     ::= <table> [AS  <alias>]
#
#      <order-by-clause>::= ORDER BY <list-sort-spec>
#      <list-sort-spec> ::= <sort-spec> [<comma> <sort-spec>]
#      <sort-spec>      ::= <colname> [ASC|DESC]

sort_spec = Group(column + Optional(ASC|DESC).setResultsName('order_type'))
sort_spec = sort_spec.setResultsName('sort_spec')
list_sort_spec = delimitedList(sort_spec)
list_sort_spec = list_sort_spec.setResultsName('list_sort_spec')
order_by_clause = Group(ORDER + BY + list_sort_spec)
order_by_clause = order_by_clause.setResultsName('order_by_clause')

alias = identifier.copy().setResultsName('alias')
from_table = Group(table_name + Optional(Optional(AS) + alias))
from_table = from_table.setResultsName("from_table")

list_tables = delimitedList(from_table)
list_tables = list_tables.setResultsName("list_tables")
from_clause = Group(FROM + list_tables).setResultsName("from_clause")

derived_column = Group(arith_expr + Optional(AS+alias))
derived_column = derived_column.setResultsName('derived_column')
star = Literal("*").setResultsName('star')
select_list = star|Group(delimitedList(derived_column))
select_list = select_list.setResultsName("select_list")

DISTINCT = DISTINCT.setResultsName("distinct")
select_stmt = (SELECT + Optional(DISTINCT) + select_list +
              from_clause +
              Optional(where_clause) +
              Optional(order_by_clause))

# Create-Index Statement
# ======================
#      <create-index>     ::= CREATE INDEX <index-name>
#                             ON <table-name> (indexed-columns)
#                             USING {BTREE|HASH}
#      <indexed-columns>  ::= <colname> [<comma> <colname>]*
index_name = identifier.setResultsName('index_name')
index_type = (BTREE|HASH).setResultsName('index_type')
indexed_columns = (LPAR + delimitedList(column_name) + RPAR)
indexed_columns = indexed_columns.setResultsName('indexed_columns')
create_index_stmt = (CREATE + INDEX + index_name + ON + table_name +
                     indexed_columns +
                     USING + index_type)

# Create-Table Statement
# ======================
#     <create-table>         ::= CREATE TABLE <table-name>
#                                (
#                                    <list-col-definitions>
#                                    [<comma> <index-definition>]
#                                )
#     <list-col-definitions> ::= <column-def> [<comma> <column-def>]
#     <column-def>           ::= <colname> <data-type> [<null-constrain>]
#     <index-definition>     ::= INDEX (<indexed-columns>) USING <index-type>]
null_constrain = (Group(NOT+NULL)|Group(NULL))
null_constrain = null_constrain.setResultsName('null_constrain')
column_definition = column_name + data_type + Optional(null_constrain)
column_definition = column_definition.setResultsName('column_definition')
list_column_defs  = delimitedList(Group(column_definition))
list_column_defs  = list_column_defs.setResultsName('list_column_definitions')
index_definition = INDEX + ON + indexed_columns + USING + index_type
index_definition = index_definition.setResultsName('index_definition')
create_table_stmt = (CREATE + TABLE + table_name +
                     LPAR +
                     list_column_defs +
                     Optional(comma + index_definition) +
                     RPAR)

# Drop table and index Statements
# ===============================
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
