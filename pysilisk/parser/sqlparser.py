import logging
import pyparsing

from pysilisk.parser.sqlgrammar import SQL_GRAMMAR
from pysilisk.parser.ast import AST_DropIndex, AST_Update, AST_UpdateSetClause
from pysilisk.parser.ast import AST_ColumnDefinition, AST_CreateTable, AST_Table
from pysilisk.parser.ast import AST_NumberLiteral, AST_StringLiteral, OrderType
from pysilisk.parser.ast import AST_OR, AST_EQ, AST_FunctionCall, AST_EmptyExpr
from pysilisk.parser.ast import AST_NEQ, AST_GTE, AST_LTE, AST_Mult, AST_Insert
from pysilisk.parser.ast import AST_NegArithExpr, AST_Column, AST_LT, AST_Select
from pysilisk.parser.ast import AST_Add, AST_Sub, AST_Div, AST_GT, AST_DropTable
from pysilisk.parser.ast import NullConstrain, AST_OrderByColumn, AST_AllColumns
from pysilisk.parser.ast import AST_NotBoolExpr, AST_CreateIndex, AST_Delete
from pysilisk.parser.ast import AST_AND


logger = logging.getLogger(__name__)


class SQLParser(object):
    """This Parser generates the AST-tree of sql-query that match
    the sql-grammar specified by SQL_GRAMMAR. Since SQL_GRAMMAR is
    defined using pyparsing, our SQLParser translates the output of
    SQL_GRAMMAR.parseString(sql) into a tree of AST nodes.

    For example, given the query:
        SELECT name, score/4
        FROM student, course
        WHERE year=2000;

    SQLParse generates:
                     ____________ ast-select ___________________
                   /                     \                       \
                 /                        \                       \
         select_list                  from_clause             where_clause
          /       \                    /       \                   |
    ast-col       ast-div         ast-tbl     ast-tbl          ast-equal
     (name)        /    \       (student)    (course)           /     \
              ast-col   ast-num                            ast-col   ast-num
              (score)       (4)                             (year)    (2000)
    """
    def parse_query(self, sql_str):
        try:
            return parse(sql_str)
        except pyparsing.ParseException as ex:
            error_desc = ex.msg.split(',')[0]  # Some ParseException's msg
                                               # are too long.
            raise SQLParseException(sql_str, ex.loc, error_desc)


# Initial parse-implementation:
def parse(sql_str):
    result = SQL_GRAMMAR.parseString(sql_str)
    stmt_type = result.getName()
    logger.debug('Stmt-type: %s', stmt_type)
    if stmt_type == 'DROP_INDEX':
        index_name = result.index_name[0]
        table_name = result.table_name[0]
        logger.debug('index: "%s"', index_name)
        logger.debug('table: "%s"', table_name)
        return AST_DropIndex(index_name, table_name)
        # ==============================================================
    elif stmt_type == 'DROP_TABLE':
        table_name = result.table_name[0]
        logger.debug('table: "%s"', table_name)
        return AST_DropTable(table_name)
        # ==============================================================
    elif stmt_type == 'CREATE_INDEX':
        idx_name = result.index_name[0]
        table_name = result.table_name[0]
        logger.debug('index-name: "%s"', idx_name)
        logger.debug('table: "%s"', table_name)

        list_idx_columns = [c for c in result.indexed_columns]
        idx_type = result.index_type
        logger.debug('on-columns: "%s"', list_idx_columns)
        logger.debug('indexType: "%s"', idx_type)

        return AST_CreateIndex(idx_name, table_name, list_idx_columns, idx_type)
        # ==============================================================
    elif stmt_type == 'CREATE_TABLE':
        table_name = result.table_name[0]
        logger.debug('table: "%s"', table_name)

        # Extract column-definitions
        ast_column_defs = []
        for definition in result.list_column_definitions:
            col_name = definition.column_name[0]
            type_name = definition.data_type.type_name

            type_size = definition.data_type.size
            type_size = int(type_size) if type_size.isdigit() else -1

            null_constrain = ' '.join(definition.null_constrain)
            null_code = NullConstrain.from_string(null_constrain)

            msg = ("colName: %s, typeName: %s, typeSize: %s, "
                   "nullIdentifier: %s   -   "+null_constrain)
            logger.debug(msg, col_name, type_name, type_size, null_code)

            # Create and append an ast-definition
            ast_column_defs.append(
                AST_ColumnDefinition(col_name, type_name, type_size, null_code)
            )

        # Extract index information
        ast_idx = None
        if result.index_definition != '':
            index_definition = result.index_definition

            # Only 1 clustered-index per table. So,
            # we use pk_<table> as the index-name
            idx_name = 'pk_%s' % table_name
            indexed_cols = [c for c in index_definition.indexed_columns]
            idx_type = index_definition.index_type

            args = (idx_name, table_name, indexed_cols, idx_type)
            ast_idx = AST_CreateIndex(*args)

            logger.debug('index-name: "%s"', idx_name)
            logger.debug('indexed-columns: "%s"', indexed_cols)
            logger.debug('index-type: "%s"', idx_type)
        return AST_CreateTable(table_name, ast_column_defs, ast_idx)
        # ==============================================================
    elif stmt_type == 'INSERT':
        table_name = result.table_name[0]
        logger.debug('table: "%s"', table_name)

        # Extract list-of-values
        ast_inserted_values = []
        for literal in result.insert_values:
            literal_value = literal[0]
            literal_type = literal.getName()
            logger.debug('value: %s - type: %s', literal_value, literal_type)

            # The ast for the literal (we don't support expr)
            # ast-number is used for both integers and floats
            # ast-string is used for varchar, char, date and datetime
            #       although date and datetime are entered as strings,
            #       they are stored as integers and floats respectively
            ast_value = None
            if literal_type in ['integer_literal', 'float_literal']:
                ast_value = AST_NumberLiteral(float(literal_value))
            elif literal_type == 'string_literal':
                ast_value = AST_StringLiteral(literal_value)
            ast_inserted_values.append(ast_value)
        return AST_Insert(table_name, ast_inserted_values)
        # ==============================================================
    elif stmt_type == 'DELETE':
        table_name = result.table_name[0]
        logger.debug('table: %s', table_name)
        if result.where_clause == '':
            ast_where = AST_EmptyExpr()
        else:
            where_clause = result.where_clause
            ast_where = to_ast_expr(where_clause, 'where_clause')
        return AST_Delete(table_name, ast_where)
        # ==============================================================
    elif stmt_type == 'UPDATE':
        table_name = result.table_name[0]
        logger.debug('table: %s', table_name)

        # Extract the <col = value>
        logger.debug('update-set-clauses:')
        list_set_clauses = []
        for set_clause in result.list_set_clauses:
            colname = set_clause.column_name[0]
            update_source = set_clause.update_source[0]
            logger.debug('   column: %s', colname)
            logger.debug('   update-source: %s', update_source)

            ast_update_source = to_ast_expr(update_source, 'arith_expr')
            ast_set_clause = AST_UpdateSetClause(colname, ast_update_source)
            list_set_clauses.append(ast_set_clause)

        if result.where_clause == '':
            ast_where = AST_EmptyExpr()
        else:
            where_clause = result.where_clause
            ast_where = to_ast_expr(where_clause, 'where_clause')
        return AST_Update(table_name, list_set_clauses, ast_where)
        # ==============================================================
    elif stmt_type == 'SELECT':
        is_distinct = True if result.distinct == 'DISTINCT' else False

        # Extract the select-list
        logger.debug('select-list:')
        select_list = []
        for derived_column in result.select_list:
            logger.debug('  derived-column: %s', derived_column)
            if derived_column == '*':
                select_list.append(AST_AllColumns())
                break
            ast_derived_column = to_ast_expr(derived_column[0], 'arith_expr')
            select_list.append(ast_derived_column)

        # Extract the tables in the from-clause
        from_list = []
        logger.debug('from-list:')
        for from_table in result.from_clause.list_tables:
            logger.debug('  from-table: %s', from_table)
            table_name = from_table.table_name[0]
            alias = from_table.alias[0] if from_table.alias != '' else ''
            ast_table = AST_Table(table_name, alias)
            from_list.append(ast_table)

        # where-clause
        logger.debug('where-clause:')
        if result.where_clause == '':
            ast_where = AST_EmptyExpr()
        else:
            where_clause = result.where_clause
            ast_where = to_ast_expr(where_clause, 'where_clause')

        # Extract the order-by-clause
        logger.debug('order-by-list:')
        order_by_list = []
        if result.order_by_clause != '':
            for sort_spec in result.order_by_clause.list_sort_spec:
                logger.debug('  sort-spec: %s', sort_spec)
                ast_column = to_ast_expr(sort_spec.column, 'column')
                order_type = OrderType.from_string(sort_spec.order_type)

                ast_sort_spec = AST_OrderByColumn(ast_column, order_type)
                order_by_list.append(ast_sort_spec)
        args = (is_distinct, select_list, from_list, ast_where, order_by_list)
        return AST_Select(*args)
        # ==============================================================
    else:
        msg = 'Unknown Stmt-type: "%s" in query: "%s"' % (stmt_type, sql_str)
        raise UnknownStatementOrExpressionException(msg)


def to_ast_expr(parsed_expr, _type, depth=0, parent=None):
    """Create an AST-tree representation of an bool and arith expression.

        - This function is used for where-clauses in Select, Delete
          and Update Statements:
                DELETE FROM professor WHERE (salary > 100000);

        - It also can be used for the projections in Select stmts.
                SELECT (salary/12) FROM professor;
    """

    # Debugging Stuffs
    align = '|  ' * depth  # Used to output the debug-info as a tree
    new_depth = depth + 1  # Used to output the debug-info as a tree
    expr_name = get_expression_name(parsed_expr)
    logger.debug('%s- Expr: %s', align, parsed_expr)
    logger.debug(('%s- expr-type: %s '
                  ' -  expr-name: %s '
                  ' -  parent-type: %s'), align, _type, expr_name, parent)

    # Create the AST recursively (Main Point)
    if _type == 'where_clause':
        next_expr = parsed_expr.bool_expr
        return to_ast_expr(next_expr, 'bool_expr', new_depth, _type)
        # ==============================================================
    elif _type == 'bool_expr':
        # RULE:
        #       <bool-expr>  ::=  <bool-term> [OR <bool-term>]*
        # A bool-expr with length > 1, has bool_terms concatenated with ORs.
        # For an expr [a, OR, b, OR, c],  we create the following ast-tree:
        #             OR
        #           /   \
        #        OR      c
        #       /  \
        #      a    b
        bool_expr = parsed_expr[0]  # It should be just parsed_expr, But For
                                    # some reason our grammar adds an extra
                                    # level. In the other rules we don't have
                                    # this extra level.
        left_ast = to_ast_expr(bool_expr[0], 'bool_term', new_depth, _type)
        for i in range(2, len(bool_expr), 2):  # i: 2, 4, 6 ...
            logger.debug('%s| BOOL-OP: OR', align)

            right_factor = bool_expr[i]
            right_ast = to_ast_expr(right_factor, 'bool_term', new_depth, _type)

            # Set the ast-operation
            left_ast = AST_OR(left_expr=left_ast, right_expr=right_ast)
        return  left_ast
        # ==============================================================
    elif _type == 'bool_term':
        # RULE:
        #       <bool-term>  ::=  <not-factor> [AND <not-factor>]*
        # A bool-term with length > 1, has bool_factors concatenated
        # with ANDs. For an expr [a, AND, b, AND, c], we create the
        # following ast-tree:
        #             AND
        #           /    \
        #        AND      c
        #       /   \
        #      a     b
        bool_term = parsed_expr
        left_ast = to_ast_expr(bool_term[0], 'bool_factor', new_depth, _type)
        for i in range(2, len(bool_term), 2):  # i: 2, 4, 6 ...
            logger.debug('%s| BOOL-OP: AND', align)

            right_factor = bool_term[i]
            right_ast = to_ast_expr(right_factor, 'bool_factor', new_depth, _type)

            # Set the ast-operation
            left_ast = AST_AND(left_expr=left_ast, right_expr=right_ast)
        return  left_ast
        # ==============================================================
    elif _type == 'bool_factor':
        # RULE:
        #      <bool-factor>  ::=  [NOT] <predicate>
        bool_factor = parsed_expr
        predicate = bool_factor.predicate
        not_op = bool_factor.not_op
        logger.debug('%s|    BOOL-NEGATION: %s', align, not_op)
        ast_expr = to_ast_expr(predicate, 'predicate', new_depth, _type)
        if not_op == 'NOT':
            return AST_NotBoolExpr(ast_expr)
        return ast_expr
        # ==============================================================
    elif _type == 'predicate':
        # RULE:
        #       <predicate>  ::=  <arith-expr> [<pred-op> <arith-expr>]
        # All predicates have either:
        #  * length = 1 e.g.,  ["a+b"]. Here, there is no comparison.
        #  * length = 3 e.g., ["a+b", "<", "c"]. Here, we create the
        #    ast-tree:
        #             <
        #           /   \
        #         a+b    c
        predicate = parsed_expr
        left_ast = to_ast_expr(predicate[0], 'arith_expr', new_depth, _type)
        for i in range(1, len(predicate), 2):  # i: 1, 3, 5 ...
            # Get the ast-operation
            op = predicate[i]
            ast_op = AST_EQ() if op == '=' else None
            ast_op = AST_NEQ if op == '<>' else ast_op
            ast_op = AST_GTE() if op == '>=' else ast_op
            ast_op = AST_LTE() if op == '<=' else ast_op
            ast_op = AST_GT() if op == '>' else ast_op
            ast_op = AST_LT() if op == '<' else ast_op
            logger.debug('%s| PREDICATE-OP: %s', align, op)

            # Get the next expression
            right_expr = predicate[i+1]
            right_ast = to_ast_expr(right_expr, 'arith_expr', new_depth, _type)

            # Set the ast-operation
            ast_op.left_expr = left_ast
            ast_op.right_expr = right_ast
            left_ast = ast_op
        return  left_ast
        # ==============================================================
    elif _type == 'arith_expr':
        # RULE:
        #       <arith-expr>  ::=  <term> [<add-op> <term>]*
        # An arith-expr with length > 1, has terms concatenated  with
        # "+" or "-" operators. For an expr [a, +, b, -, c], we create
        # the following ast-tree:
        #             -
        #           /  \
        #          +    c
        #        /  \
        #       a    b
        arith_expr = parsed_expr
        left_ast = to_ast_expr(arith_expr[0], 'term', new_depth, _type)
        for i in range(1, len(arith_expr), 2):  # i: 1, 3, 5 ...
            # Get the ast-operation
            op = arith_expr[i]
            ast_op = AST_Add() if op == '+' else AST_Sub()
            logger.debug('%s| OP-ADD-SUB: %s', align, op)

            # Get the next expression
            right_term = arith_expr[i+1]
            right_ast = to_ast_expr(right_term, 'term', new_depth, _type)

            # Set the ast-operation
            ast_op.left_expr = left_ast
            ast_op.right_expr = right_ast
            left_ast = ast_op
        return  left_ast
        # ==============================================================
    elif _type == 'term':
        # RULE:
        #       <term>  ::=  <signed factor> [<mult-op> factor]*
        # A term with with length > 1, has factors concatenated with "*"
        # or "/" operators. For an expr [a, *, b, *, c], we create the
        # following ast-tree:
        #             *
        #           /  \
        #          *    c
        #        /  \
        #       a    b
        term = parsed_expr
        left_ast = to_ast_expr(term[0], 'signed_factor', new_depth, _type)
        for i in range(1, len(term), 2):  # i: 1, 3, 5 ...
            # Get the ast-operation
            op = term[i]
            ast_op = AST_Mult() if op == '*' else AST_Div()
            logger.debug('%s| OP-MULT-DIV: %s', align, op)

            # Get the next expression
            right_factor = term[i+1]
            right_ast = to_ast_expr(right_factor, 'factor', new_depth, _type)

            # Set the ast-operation
            ast_op.left_expr = left_ast
            ast_op.right_expr = right_ast
            left_ast = ast_op
        return  left_ast
        # ==============================================================
    elif _type == 'signed_factor':
        # RULE:
        #       <signed factor>  ::=  [<sign>] <factor>
        signed_factor = parsed_expr
        factor = signed_factor.factor
        sign_op = signed_factor.sign_op
        logger.debug('%s|    SIGN: %s', align, sign_op)
        ast_expr = to_ast_expr(factor, 'factor', new_depth, _type)
        if sign_op == '-':
            return AST_NegArithExpr(ast_expr)
        return ast_expr
        # ==============================================================
    elif _type == 'factor':
        # RULE:
        #       <factor>  ::=  <literal> | <column> | function | (<bool-expr>)
        # Note:
        #   Pyparsing names <literal> as integer_literal, float_literal, etc.
        #   Pyparsing names <column> as column.
        #   Pyparsing names <function> as function.
        # * Pyparsing names (<bool-expr>) as factor. This is weird. Therefore,
        #                                            we need to provide, the
        #                                            correct _type manually.
        factor_name = parsed_expr.getName()
        factor = parsed_expr
        if  factor_name == 'factor':
            return to_ast_expr(factor.bool_expr, 'bool_expr', new_depth, _type)
        else:
            return  to_ast_expr(factor[0], factor_name, new_depth, _type)
        # ==============================================================
    elif _type == 'integer_literal':
        logger.debug('%s- value: %s', align, parsed_expr)
        integer_literal = parsed_expr
        return AST_NumberLiteral(int(integer_literal))
        # ==============================================================
    elif _type == 'float_literal':
        logger.debug('%s- value: %s', align, parsed_expr)
        float_literal = parsed_expr
        return AST_NumberLiteral(float(float_literal))
        # ==============================================================
    elif _type == 'string_literal':
        logger.debug('%s- value: %s', align, parsed_expr)
        string_literal =  parsed_expr
        return AST_StringLiteral(string_literal)
        # ==============================================================
    elif _type == 'column':
        column = parsed_expr
        column_name = column.column_name[0]
        table_name = column.table_name[0] if column.table_name != '' else ''
        logger.debug('%s- tbname: %s', align, table_name)
        logger.debug('%s- colname: %s', align, column_name)
        return AST_Column(column_name, table_name)
        # ==============================================================
    elif _type == 'function':
        function = parsed_expr
        funct_name = function.funct_name[0]
        funct_args = function.funct_args
        logger.debug('%s  funct-name: %s', align, funct_name)
        logger.debug('%s  funct-args: %s', align, funct_args)

        # Extract the ASTs for each argument
        arguments = []
        for i in range(len(funct_args)):
            arg = funct_args[i]
            logger.debug('%s  Arg[%s]: %s ', align, i, arg)
            ast_arg = to_ast_expr(arg, 'arith_expr', new_depth, _type)
            arguments.append(ast_arg)
        ast_expr = AST_FunctionCall(funct_name, arguments)
        return ast_expr
        # ==============================================================
    else:
        msg = ('Unknown Expr-type: "%s" (parent-type: "%s") in '
               'Expr: "%s"') % (_type, parent, parsed_expr)
        logger.error(msg)
        raise UnknownStatementOrExpressionException(msg)


def get_expression_name(parseResult):
    """
    To safely call the getName() method in ParseResults objects during
    DEBUGGING. With getName(), we obtain the name of the grammar-rule
    that matched the result. These objects are created by parseString().
    In our case, we create them, when we call:
        result = SQL_GRAMMAR.parseString(sql_str)
        result = where_clause.parseString("WHERE c > 3*5")
    For some reason, some of the inner ParseResults objects generated
    by the where_clause-rule are crashing when their getName is called.
    """
    expr_name = 'NONE'
    if logger.isEnabledFor(logging.DEBUG):
        try:
            if isinstance(parseResult, pyparsing.ParseResults):
                expr_name = parseResult.getName()
        except TypeError:
            pass
    return expr_name


class SQLParseException(Exception):
    """Exception produced while parsing a syntactically invalid query
    (query that does not follow our sql-grammar). This exception is
    similar to pyparsing.ParseException and we use it to reduce the
    our dependency on pyparsing.

    Additionally, this exception creates a readable message for users.
    For example, given the invalid query:
        SELECT age, class,
               title, address,
        FROM student;
    The message would be:
        Error: Expected "FROM"  (at char 41), Marked-str(»•«):
           ⎪SELECT age, class,
           ⎪       title, address»•«,
           ⎪FROM student;
    """
    def __init__(self, sql_str, error_loc=0, error_desc=None):
        self.sql_str = sql_str           # str that generated the error
        self.error_location = error_loc  # error-location
        self.error_desc = error_desc     # error-description

        # Create a readable message
        marked_sql = []
        marked_sql.extend(sql_str)
        marked_sql.insert(error_loc, '»•«')
        marked_sql = ''.join(marked_sql)
        marked_sql = marked_sql.split('\n')
        marked_sql = ''.join(['   ⎪' + line + '\n' for line in marked_sql])
        msg = ("Error: %s  (at char %s), "
               "Marked-str(»•«):\n%s") % (error_desc, error_loc, marked_sql)
        self.message = msg
        super().__init__(msg)


class UnknownStatementOrExpressionException(Exception):
    """Unrecoverable Error produced during the creation
     of the AST-tree of an unknown sql-stmt-type or an
     unknown expression."""
    pass