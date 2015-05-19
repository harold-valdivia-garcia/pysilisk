import logging

from pysilisk.parser.sqlgrammar import SQL_GRAMMAR
from pysilisk.parser.ast import AST_DropIndex, AST_DropTable, AST_CreateIndex
from pysilisk.parser.ast import AST_ColumnDefinition, AST_CreateTable
from pysilisk.parser.ast import AST_NumberLiteral, AST_StringLiteral, AST_Insert
from pysilisk.parser.ast import AST_Delete, AST_OR, AST_AND, AST_NotBoolExpr
from pysilisk.parser.ast import AST_EQ, AST_NEQ, AST_GTE, AST_LTE, AST_GT
from pysilisk.parser.ast import AST_LT, AST_Add, AST_Sub, AST_Mult, AST_Div
from pysilisk.parser.ast import AST_NegArithExpr, AST_Column, AST_FunctionCall
from pysilisk.parser.ast import NullConstrain
from pyparsing import ParseResults

import pyparsing



logger = logging.getLogger(__name__)


class SQLParser(object):
    def parse_query(self, sql_str):
        try:
            return parse(sql_str)
        except UnknownStatementOrExpressionException as parse_exc:
            # Add the sql_str
            parse_exc.sql_str = sql_str
            raise parse_exc
        except pyparsing.ParseException as parse_exc:
            pass


class UnknownStatementOrExpressionException(Exception):
    """Unrecoverable Error produced during the creation
     of the AST-tree of an unknown sql-stmt-type or an
     unknown expression."""
    pass

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
    elif stmt_type == 'DROP_TABLE':
        table_name = result.table_name[0]
        logger.debug('table: "%s"', table_name)
        return AST_DropTable(table_name)
    elif stmt_type == 'CREATE_INDEX':
        idx_type = result.index_type
        idx_name = result.index_name[0]
        table_name = result.table_name[0]
        list_idx_columns = [c for c in result.list_index_columns]
        logger.debug('index: "%s"', idx_name)
        logger.debug('table: "%s"', table_name)
        logger.debug('on-columns: "%s"', list_idx_columns)
        logger.debug('indexType: "%s"', idx_type)
        return AST_CreateIndex(idx_name, table_name, list_idx_columns, idx_type)
    elif stmt_type == 'CREATE_TABLE':
        table_name = result.table_name[0]
        logger.debug('table: "%s"', table_name)

        # Extract column-definitions
        ast_column_defs = []
        for definition in result.list_column_defs:
            col_name = definition.column_name[0]
            type_name = definition.data_type.type_name
            type_size = definition.data_type.size
            type_size = int(type_size) if type_size.isdigit() else -1
            null_constrain = ' '.join(definition.null_constrain)
            null_identifier = NullConstrain.from_string(null_constrain)
            msg = "colName: %s, typeName: %s, typeSize: %s, nullIdentifier: %s"
            logger.debug(msg, col_name, type_name, type_size, null_identifier)
            # Create and append an ast-definition
            ast_column_defs.append(
                AST_ColumnDefinition(col_name, type_name, type_size, null_identifier)
            )
        # Extract index information
        ast_idx = None
        if result.index_type != '':
            idx_type = result.index_type
            idx_columns = [c for c in result.list_index_columns]
            idx_name = 'pk_%s' % table_name  # Only 1 clustered-index per table
            logger.debug('index: "%s"', idx_name)
            logger.debug('index-columns: "%s"', idx_columns)
            logger.debug('indexType: "%s"', idx_type)
            ast_idx = AST_CreateIndex(idx_name, table_name, idx_columns, idx_type)
        return AST_CreateTable(table_name, ast_column_defs, ast_idx)
    elif stmt_type == 'INSERT':
        table_name = result.table_name[0]
        logger.debug('table: "%s"', table_name)
        ast_inserted_values = []
        for literal in result.insert_values:
            literal_value = literal[0]
            literal_type = literal.getName()
            ast_value = None
            if literal_type in ['integer_literal', 'float_literal']:
                ast_value = AST_NumberLiteral(float(literal_value))
            elif literal_type == 'string_literal':
                ast_value = AST_StringLiteral(literal_value)
            ast_inserted_values.append(ast_value)
            logger.debug('value: %s  -  type: %s', literal_value, literal_type)
        return AST_Insert(table_name, ast_inserted_values)
    elif stmt_type == 'DELETE':
        table_name = result.table_name[0]
        ast_where_clause = to_ast_expr(result.where_clause, 'where_clause')
        return AST_Delete(table_name, ast_where_clause)
    else:
        msg = 'Unknown Stmt-type: "%s" in query: "%s"' % (stmt_type, sql_str)
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
    if logger.level == logging.DEBUG:
        try:
            if isinstance(parseResult, ParseResults):
                expr_name = parseResult.getName()
        except TypeError:
            pass
    return expr_name

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
        # ============================================
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
        # ============================================
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
        # ============================================
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
        # ============================================
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
        # ============================================
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
        # ============================================
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
        # ============================================
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
        # ============================================
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
        # ============================================
    elif _type == 'integer_literal':
        logger.debug('%s- value: %s', align, parsed_expr)
        integer_literal = parsed_expr
        return AST_NumberLiteral(int(integer_literal))
        # ============================================
    elif _type == 'float_literal':
        logger.debug('%s- value: %s', align, parsed_expr)
        float_literal = parsed_expr
        return AST_NumberLiteral(float(float_literal))
        # ============================================
    elif _type == 'string_literal':
        logger.debug('%s- value: %s', align, parsed_expr)
        string_literal =  parsed_expr
        return AST_StringLiteral(string_literal)
        # ============================================
    elif _type == 'column':
        column = parsed_expr
        column_name = column.column_name[0]
        table_name = column.table_name[0] if column.table_name != '' else ''
        logger.debug('%s- tbname: %s', align, table_name)
        logger.debug('%s- colname: %s', align, column_name)
        return AST_Column(column_name, table_name)
        # ============================================
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
        # ============================================
    else:
        msg = ('Unknown Expr-type: "%s" (parent-type: "%s") in '
               'Expr: "%s"') % (_type, parent, parsed_expr)
        logger.error(msg)
        raise UnknownStatementOrExpressionException(msg)
