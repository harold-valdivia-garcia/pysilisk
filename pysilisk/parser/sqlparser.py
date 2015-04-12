from pyparsing import Word, Literal, Group, QuotedString
from pyparsing import alphas, alphanums, CaselessKeyword
from pyparsing import Optional, delimitedList, Regex

# This code is based on:
# http://pyparsing.wikispaces.com/file/view/simpleSQL.py
# https://pyparsing.wikispaces.com/file/view/select_parser.py
# https://github.com/tgulacsi/plsql_parser
# http://stackoverflow.com/questions/16909380/sql-parsing-using-pyparsing

# Define keywords
(SELECT, FROM, WHERE, AS, NULL) = map(CaselessKeyword, """SELECT, FROM,
 WHERE, AS, NULL""".replace(",","").split())


# Define and remove dot from the outputs
dot = Literal(".").suppress()
comma = Literal(",").suppress()

# Basic identifier used to define vars, tables, columns
identifier = Word(alphas, alphanums + '_')

alias = identifier.copy().setResultsName('alias')

# Table
simple_table_name = identifier.setResultsName("table_name")
table_name = simple_table_name.copy()

# Column
simple_column_name = identifier.setResultsName("column_name")
fully_qualified_column_name = simple_table_name + dot + simple_column_name
column_name = fully_qualified_column_name ^ simple_column_name

# From-clause
# bnf-from_table = table ( (AS){0,1} alias)*
from_table = Group(table_name + Optional(Optional(AS) + alias))
from_table = from_table.setResultsName("from_table")
from_tables = delimitedList(from_table)  # tbl1 as t, tbl2 as b,...
from_tables = from_tables.setResultsName("from_tables")
from_clause = Group(FROM + from_tables).setResultsName("from_clause")

# Literal Values
nonzero_digits = Word('123456789')
integer_literal = Regex(r"[+-]?([1-9][0-9]*|0)")
Literal(".")
num_dot = Literal(".")
real_number_literal = Regex(r"[+-]?([1-9][0-9]*|0)\.[0-9]+")
numeric_literal = real_number_literal | integer_literal
string_literal = QuotedString("'")
literal_value = (numeric_literal|string_literal|NULL)


# Select-Statement
selectStmt = SELECT + column_name + from_clause.setResultsName("from_clause")

