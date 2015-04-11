from pyparsing import Word, Literal
from pyparsing import alphas, alphanums

# Define and remove dot from the outputs
dot = Literal(".").suppress()

# Basic identifier used to define vars, tables, columns
identifier = Word(alphas, alphanums + '_')

# Table
simple_table_name = identifier.setResultsName("table_name")

# Column
simple_col_name = identifier.setResultsName("column_name")
fully_qualified_col_name = simple_table_name + dot + simple_col_name
col_name = fully_qualified_col_name ^ simple_col_name
