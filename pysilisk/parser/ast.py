import logging
from pysilisk.sqltypes import SQLDataType, NullConstrain
from pysilisk.parser.sqlparser import SQL_GRAMMAR
from pyparsing import ParseResults

logger = logging.getLogger(__name__)

class ComparisonOp(object):
    EQ = 3                # Conditional equality("=") expression
    GT = 4                # Conditional greater than(">") expression
    GTE = 5                # Conditional greater than or equal(">=") expression
    LT = 6                # Conditional less than("<") expression
    LTE = 7                # Conditional less than or equal("<=") expression


class LogicalOp(object):
    AND = 2                # Conditional "and" expression
    OR = 9
    NOT = 8                # Conditional "not" expression

class AST_Node(object):
    TABLE = -1
    EXPRESSION = -1
    DROP_TABLE = -1
    SELECT = -1
    INSERT = -1
    PROJECTION = -1
    DELETE = -1
    CREATE_INDEX = -1
    DROP_INDEX = -1
    COLUMN_ORDER_BY = -1
    EMPTY_EXPR = -1
    COLUMN_DEFINITION = -1
    CREATE_TABLE = -1
    NUM_CONST = 0
    BOOL_CONST = 1        # Boolean constant expression
    AND = 2                # Conditional "and" expression
    EQ = 3                # Conditional equality("=") expression
    GT = 4                # Conditional greater than(">") expression
    GTE = 5                # Conditional greater than or equal(">=") expression
    LT = 6                # Conditional less than("<") expression
    LTE = 7                # Conditional less than or equal("<=") expression
    NOT = 8                # Conditional "not" expression
    OR = 9                # Conditional "or" expression
    STRING_CONST = 10   # String constant expression
    COLUMN = 11            # Column (table attribute) reference
    NO_EXPR = 12        # Stub for an empty expression
    ADD = 13            # Arithmetic addition/plus("a+b") expression
    SUB = 14            # Arithmetic substraction/minus("a-b") expression
    NEG = 15            # Arithmetic negation ("-a") expression
    MULT = 16            # Arithmetic multiplication ("a*b") expression
    DIV = 17            # Arithmetic division ("a/b") expression
    FUNCTION_CALL = 18    # Function call expression

    def __init__(self, ast_id):
        self.ast_id = ast_id


class AST_Table(AST_Node):
    def __init__(self, name, alias):
        super().__init__(AST_Node.TABLE)
        self.name = name
        self.alias = alias


class AST_Expression(AST_Node):
    """We use ast_id to identify the type of expressions"""
    def __init__(self, ast_id):
        super().__init__(ast_id)

class AST_Literal(AST_Expression):
    def __init__(self, value, literal_type):
        super().__init__(AST_Node.NUM_CONST)
        self.value = value

class AST_NumberLiteral(AST_Expression):
    def __init__(self, value):
        super().__init__(AST_Node.NUM_CONST)
        self.value = value


class AST_StringLiteral(AST_Expression):
    def __init__(self, value):
        super().__init__(AST_Node.STRING_CONST)
        self.value = value

# BooleanLiteral is not supported
# I've never used booleans in sql

class AST_Column(AST_Expression):
    def __init__(self, col_name, tbl_name=''):
        super().__init__(AST_Node.COLUMN)
        self.col_name = col_name
        self.tbl_name = tbl_name


class AST_Projection(AST_Node):
    def __init__(self, expression, alias=None):
        super().__init__(AST_Node.PROJECTION)
        self.expression = expression
        self.alias = alias


class AST_FunctionCall(AST_Expression):
    def __init__(self, funct_name, arguments=None):
        super().__init__(AST_Node.FUNCTION_CALL)
        self.funct_name = funct_name
        self.arguments = arguments


class AST_BooleanExpr(AST_Expression):
    def __init__(self, ast_id, left_expr, right_expr):
        super().__init__(ast_id)
        self.left_expr = left_expr
        self.right_expr = right_expr


class AST_AND(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.AND, left_expr, right_expr)


class AST_OR(AST_BooleanExpr):
    def __init__(self, left_expr=None, right_expr=None):
        super().__init__(AST_Node.OR, left_expr, right_expr)


class AST_EQ(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.EQ, left_expr, right_expr)


class AST_GT(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.GT, left_expr, right_expr)


class AST_GTE(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.GTE, left_expr, right_expr)


class AST_LT(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.LT, left_expr, right_expr)


class AST_LTE(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.LTE, left_expr, right_expr)


class AST_BinaryArithOp(AST_Expression):
    def __init__(self, ast_id, left_expr, right_expr):
        super().__init__(ast_id)
        self.left_expr = left_expr
        self.right_expr = right_expr


class AST_Div(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.DIV, left_expr, right_expr)


class AST_Mult(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.MULT, left_expr, right_expr)


class AST_Add(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.ADD, left_expr, right_expr)


class AST_Sub(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(AST_Node.SUB, left_expr, right_expr)


class AST_DropTable(AST_Node):
    def __init__(self, table_name):
        super().__init__(AST_Node.DROP_TABLE)
        self.table_name = table_name


class AST_Insert(AST_Node):
    def __init__(self, table_name, inserted_values):
        super().__init__(AST_Node.INSERT)
        self.table_name = table_name
        self.inserted_values = inserted_values


class AST_Delete(AST_Node):
    def __init__(self, table, where):
        super().__init__(AST_Node.DELETE)
        self.table = table
        self.where = where


class AST_CreateIndex(AST_Node):
    def __init__(self, idx_name, table_name, list_column_names, idx_type):
        super().__init__(AST_Node.CREATE_INDEX)
        self.idx_name = idx_name
        self.table_name = table_name
        self.list_column_names = list_column_names  # list col-names
        self.idx_type = idx_type


class AST_DropIndex(AST_Node):
    def __init__(self, idx_name, table_name):
        super().__init__(AST_Node.DROP_INDEX)
        self.idx_name = idx_name
        self.table_name = table_name


class AST_EmptyExpr(AST_Expression):
    def __init__(self):
        super().__init__(AST_Node.EMPTY_EXPR)


class AST_NegArithExpr(AST_Expression):
    def __init__(self, arith_expr):
        super().__init__(AST_Node.NEG)
        self.arith_expr = arith_expr


class AST_NotBoolExpr(AST_BooleanExpr):
    def __init__(self, bool_expr):
        super().__init__(AST_Node.NOT, None, None)
        self.bool_expr = bool_expr


class AST_OrderByColumn(AST_Node):
    def __init__(self, column, ordering):
        super().__init__(AST_Node.COLUMN_ORDER_BY)
        self.column = column  # we only support ast-columns
        self.ordering = ordering  # list of ascs or descs


class AST_Select(AST_Node):
    def __init__(self, has_distinct, prj_attrs, from_cls, where_cls, order_by):
        super().__init__(AST_Node.SELECT)
        self.has_distinct = has_distinct
        self.prj_attrs = prj_attrs     # list-projected-attrs
        self.from_clause = from_cls    # list-tables
        self.where_clause = where_cls  # list-bool-expr
        self.order_by = order_by       # list of order_by_columns


class AST_ColumnDefinition(AST_Node):
    def __init__(self, column_name, type_name, type_size, null_identifier):
        super().__init__(AST_Node.COLUMN_DEFINITION)
        self.column_name = column_name
        self.type_name = type_name
        self.type_id = SQLDataType.from_string(type_name)
        self.type_size = type_size  # Only for varchar and char types
        self.null_identifier = null_identifier


class AST_CreateTable(AST_Node):
    def __init__(self, table_name, col_definitions, index_definition):
        super().__init__(AST_Node.CREATE_TABLE)
        self.table_name = table_name
        self.col_definitions = col_definitions
        self.index_definition = index_definition


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
        ast_where_clause = get_ast_expression(result.where_clause)
        return AST_Delete(table_name, ast_where_clause)


class SQLParseException(Exception):
    pass



def get_ast_expression2(raw_expr, expr_type, original_raw_expr=None, current_depth=0, parent=None):
    MAX_DEPTH = 100
    if current_depth <= MAX_DEPTH:
        align = '| ' * current_depth
        next_depth = current_depth + 1
        try:
            logger.debug('%s- typeProc: %s  -  typeExpr: %s  -  expr: %s  -  parent-type: %s', align, expr_type, raw_expr.getName() if not isinstance(raw_expr, str) else 'NONE', raw_expr, parent)
        except TypeError:
            logger.debug('%s- typeProc: %s  -  typeExpr: %s  -  expr: %s  -  parent-type: %s', align, expr_type, 'NONE' if not isinstance(raw_expr, str) else 'NONE', raw_expr, parent)

        if expr_type == 'where_clause':
            next_expr = raw_expr.bool_expr
            get_ast_expression2(next_expr, 'bool_expr', original_raw_expr, next_depth, expr_type)
        elif expr_type == 'bool_expr':
            bool_expr = raw_expr[0]
            if len(bool_expr) == 1:
                get_ast_expression2(bool_expr[0], 'bool_term', original_raw_expr, next_depth, expr_type)
            else:
                for item in bool_expr:
                    if item != 'OR':
                        get_ast_expression2(item, 'bool_term', original_raw_expr, next_depth, expr_type)
                    else:
                        logger.debug('%s| - LOGICAL-OR', align)
        elif expr_type == 'bool_term':
            bool_term = raw_expr
            if len(bool_term) == 1:
                get_ast_expression2(bool_term[0], 'bool_factor', original_raw_expr, next_depth, expr_type)
            else:
                for item in bool_term:
                    if item != 'AND':
                        get_ast_expression2(item, 'bool_factor', original_raw_expr, next_depth, expr_type)
                    else:
                        logger.debug('%s| - LOGICAL-AND', align)
        elif  expr_type == 'bool_factor':
            bool_factor = raw_expr
            if bool_factor.not_op == 'NOT':
                logger.debug('%s| - NOT-OP predicate', align)
            #logger.debug('%s| - predicat: %s', align, raw_expr.predicate)
            get_ast_expression2(raw_expr.predicate, 'predicate', original_raw_expr, next_depth, expr_type)
        elif  expr_type == 'predicate':
            predicate = raw_expr
            if len(predicate) == 1:
                get_ast_expression2(predicate[0], 'arith_expr', original_raw_expr, next_depth, expr_type)
            else:
                logger.debug('%s| - PRED-OP: %s', align, predicate[1])
                get_ast_expression2(predicate[0], 'arith_expr', original_raw_expr, next_depth, expr_type)
                get_ast_expression2(predicate[2], 'arith_expr', original_raw_expr, next_depth, expr_type)
        elif  expr_type == 'arith_expr':
            arith_expr = raw_expr
            if len(arith_expr) == 1:
                get_ast_expression2(arith_expr[0], 'term', original_raw_expr, next_depth, expr_type)
            else:
                for item in arith_expr:
                    if item != '+' and item != '-':
                        get_ast_expression2(item, 'term', original_raw_expr, next_depth, expr_type)
                    else:
                        logger.debug('%s|  op: %s', align, item)
        elif  expr_type == 'term':
            term = raw_expr
            if len(term) == 1:
                get_ast_expression2(term[0], 'signed_factor', original_raw_expr, next_depth, expr_type)
            else:
                next_expr_type = 'signed_factor'
                for item in term:
                    if item != '*' and item != '/':
                        get_ast_expression2(item, next_expr_type, original_raw_expr, next_depth, expr_type)
                        next_expr_type = 'factor'
                    else:
                        logger.debug('%s|  op: %s', align, item)
        elif  expr_type == 'signed_factor':
            signed_factor = raw_expr
            if signed_factor.sign_op != '':
                logger.debug('%s| - SIGN: %s', align, signed_factor.sign_op)
            get_ast_expression2(signed_factor.factor, 'factor', original_raw_expr, next_depth, expr_type)
        elif  expr_type == 'factor':
            #logger.debug('%s- size: %s   -   type: %s', align, len(raw_expr), raw_expr.getName())
            factor_type = raw_expr.getName()
            factor = raw_expr
            if  factor_type != 'factor':
                get_ast_expression2(factor[0], factor_type, original_raw_expr, next_depth, expr_type)
            else:
                get_ast_expression2(factor.bool_expr, 'bool_expr', original_raw_expr, next_depth, expr_type)
        elif  expr_type == 'integer_literal':
            logger.debug('%s- value: %s', align, raw_expr)
        elif  expr_type == 'float_literal':
            pass
            logger.debug('%s- value: %s', align, raw_expr)
        elif  expr_type == 'string_literal':
            pass
            logger.debug('%s- value: %s', align, raw_expr)
        elif  expr_type == 'column':
            logger.debug('%s- value: %s', align, raw_expr)
        elif  expr_type == 'function':
            logger.debug('%s- value: %s', align, raw_expr)
        else:
            logger.error('Error when processing expr: %s',  raw_expr)
            logger.error('type-expr: %s', raw_expr.getName())
            logger.error('Parent expr: %s', parent)
            logger.error('type-parent: %s', parent.getName())
            logger.error('Original expr: %s', original_raw_expr)
            raise SQLParseException()
    else:
        logger.error('Error during ast-expression creation. max-depth exceeded')
        raise SQLParseException()







def get_ast_expression(raw_expr, original_raw_expr=None, current_depth=0, parent=None):
    MAX_DEPTH = 100
    if current_depth <= MAX_DEPTH:
        align = '| ' * current_depth
        next_depth = current_depth + 1
        if 'bool_expr' in raw_expr:
            logger.debug('%s-bool_expr: %s', align, raw_expr.bool_expr)
            next_expr = raw_expr.bool_expr[0]  # Because of the Group in bool_expr
            # ==============================
            if len(next_expr) == 1:
                get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
            else:
                # A bool-expr with length > 1, has bool_terms concatenated
                # with OR operators: [a, OR, b, OR, c]. For this expression,
                # we create a ast-tree of the form:
                #             OR
                #           /   \
                #        OR      c
                #       /  \
                #      a    b
                get_ast_expression(next_expr[0], original_raw_expr, next_depth, raw_expr)
                #or_exp = AST_OR(left_expr=first_exp)
                #print('OR-right: %s' % str_deep, bool_expr[0])
                for item in next_expr[1:]:
                    if item != 'OR':
                        logger.debug('%s-OR', align)
                        get_ast_expression(item, original_raw_expr, next_depth, raw_expr)
            # ==============================
            #get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
        elif 'bool_term' in raw_expr:
            logger.debug('%s-bool_term: %s', align, raw_expr.bool_term)
            next_expr = raw_expr.bool_term[0]
            # ==============================
            if len(next_expr) == 1:
                get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
            else:
                # A bool-term with length > 1, has bool_factors concatenated
                # with AND operators: [a, AND, b, AND, c]. For this expression,
                # we create a ast-tree of the form:
                #             AND
                #           /    \
                #        AND      c
                #       /   \
                #      a     b
                get_ast_expression(next_expr[0], original_raw_expr, next_depth, raw_expr)
                #or_exp = AST_OR(left_expr=first_exp)
                #print('OR-right: %s' % str_deep, bool_expr[0])
                for item in next_expr[1:]:
                    if item != 'AND':
                        logger.debug('%s-AND', align)
                        get_ast_expression(item, original_raw_expr, next_depth, raw_expr)
            # ==============================
            #get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
        elif 'bool_factor' in raw_expr:
            logger.debug('%s-bool_factor: %s', align, raw_expr.bool_factor)
            next_expr = raw_expr.bool_factor[0]
            get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
        elif 'predicate' in raw_expr:
            logger.debug('%s-predicate: %s', align, raw_expr.predicate)
            next_expr = raw_expr.predicate
            # ==============================
            if len(next_expr) == 1:
                get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
            else:
                get_ast_expression(next_expr[0], original_raw_expr, next_depth, raw_expr)
                pred_op = next_expr[1]
                logger.debug('%s- %s', align, pred_op)
                get_ast_expression(next_expr[2], original_raw_expr, next_depth, raw_expr)
            # ==============================
            #get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
        elif 'arith_expr' in raw_expr:
            logger.debug('%s-arith_expr: %s', align, raw_expr.arith_expr)
            next_expr = raw_expr.arith_expr[0]
            # ==============================
            if len(next_expr) == 1:
                get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
            else:
                # A arith-expr with length > 1, has terms concatenated with
                # "+" or "-" operators:  [a, +, b, +, c]. For this expression,
                # we create a ast-tree of the form:
                #             +
                #           /  \
                #          +    c
                #        /  \
                #       a    b
                get_ast_expression(next_expr[0], original_raw_expr, next_depth, raw_expr)
                #or_exp = AST_OR(left_expr=first_exp)
                #print('OR-right: %s' % str_deep, bool_expr[0])
                for item in next_expr[1:]:
                    if item not in ['+', '-']:
                        get_ast_expression(item, original_raw_expr, next_depth, raw_expr)
                    else:
                        logger.debug('%s- "%s"', align, item)
            # ==============================
        elif 'term' in raw_expr:
            logger.debug('%s-term: %s  -  type: %s  -  size: %s  -  keys: %s', align, raw_expr.term, raw_expr.term.getName(), len(raw_expr.term), list(raw_expr.term.keys()))
            next_expr = raw_expr.term[0]
            logger.debug('%s-next_expr: %s  - type: %s  - size: %s  - keys: %s', align, next_expr, next_expr.getName(), len(next_expr), list(next_expr.keys()))
            logger.debug('%s-term-signed: %s ', align, next_expr.signed_factor, )

            # ==============================
            if len(next_expr) == 1:
                get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
            else:
                # A arith-expr with length > 1, has terms concatenated with
                # "*" or "/" operators:  [a, *, b, *, c]. For this expression,
                # we create a ast-tree of the form:
                #             *
                #           /  \
                #          *    c
                #        /  \
                #       a    b
                item = next_expr[0]
                if len(item) > 1:  # It is a signed_factor with SIGN
                    sf_expr = ParseResults(toklist=next_expr.signed_factor,
                                           name='signed_factor')
                else:
                    sf_expr = ParseResults(toklist=next_expr.signed_factor[0],
                                           name='signed_factor')
                get_ast_expression(sf_expr, original_raw_expr, next_depth, raw_expr)

                # The others
                for idx in range(1, len(next_expr)):
                    item = next_expr[idx]
                    if item not in ['*', '/']:
                        logger.debug('%s- item-type: %s', align, item.getName())
                        get_ast_expression(item, original_raw_expr, next_depth, raw_expr)
                    else:
                        logger.debug('%s- "%s"', align, item)
            # ==============================
        elif 'signed_factor' in raw_expr:
            logger.debug('%s-signed_factor: %s  - signed-factor-type: %s', align, raw_expr.signed_factor, raw_expr.signed_factor.getName())
            next_expr = raw_expr.signed_factor[0]
            logger.debug('%s-next_expr: %s  - size: %s   -  ', align, next_expr, len(next_expr))
            # ==============================
            sign = ''
            if len(next_expr) == 1:
                logger.debug('%s- SIGN: %s', align, None)
                get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
            else:
                sign = next_expr[0]
                logger.debug('%s- SIGN: %s', align, sign)
                get_ast_expression(next_expr[1], original_raw_expr, next_depth, raw_expr)
            # ==============================
            #get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
        elif 'factor' in raw_expr:
            logger.debug('%s-factor: %s - type: %s - keys: %s', align, raw_expr.factor, raw_expr.factor.getName(), list(raw_expr.factor.keys()) )
            next_expr = raw_expr.factor
            get_ast_expression(next_expr, original_raw_expr, next_depth, raw_expr)
        elif 'integer_literal' in raw_expr:
            logger.debug('%s-integer_literal: %s', align, raw_expr.integer_literal)
        elif 'float_literal' in raw_expr:
            logger.debug('%s-float_literal: %s', align, raw_expr.float_literal)
        elif 'string_literal' in raw_expr:
            logger.debug('%s-string_literal: %s', align, raw_expr.string_literal)
        elif 'column' in raw_expr:
            column = raw_expr.column
            table_name = column.table_name[0] if len(column) == 2 else ''
            column_name = column.column_name[0]
            logger.debug('%s-column: %s.%s', align, table_name, column_name)
        elif 'function' in raw_expr:
            logger.debug('%s-function: %s', align, raw_expr.function)
            #next_expr = raw_expr.bool_expr
            #get_ast_expression(next_expr, original_raw_expr, next_depth)
        else:
            logger.error('Error when processing expr: %s',  raw_expr)
            logger.error('type-expr: %s', raw_expr.getName())
            logger.error('Parent expr: %s', parent)
            logger.error('type-parent: %s', parent.getName())
            logger.error('Original expr: %s', original_raw_expr)
            raise SQLParseException()
    else:
        logger.error('Error during ast-expression creation. max-depth exceeded')
        raise SQLParseException()

def find_type(exp, deep=0, parent=''):
    if deep > 100:
        return None
    _type = type(exp)
    _len = len(exp)
    str_deep = '  '*deep
    print('%s len: %s  - type-exp: %s  -  exp: %s  - parent: %s' %(str_deep, _len, exp.getName(), exp,parent))

    if 'column' in exp:
        column = exp.column
        table_name = ''
        if len(column) == 2:
            table_name = column.table_name[0]
        column_name = column.column_name[0]
        print("column-tbl-name: %s" % table_name)
        print("column-col-name: %s" % column_name)
        return AST_Column(column_name, table_name)
    elif 'integer_literal' in exp:
        integer_literal =  exp.integer_literal
        print("integer-literal: %s" % integer_literal)
        return AST_NumberLiteral(int(integer_literal))
    elif 'float_literal' in exp:
        float_literal =  exp.float_literal
        print("float_literal: %s" % float_literal)
        return AST_NumberLiteral(float(float_literal))
    elif 'string_literal' in exp:
        string_literal =  exp.string_literal
        print("string_literal: %s" % string_literal)
        return AST_StringLiteral(string_literal)
    elif 'bool_expr' in exp:
        bool_expr = exp.bool_expr[0]  # Because of the Group in bool_expr
        if len(bool_expr) == 1:
            return find_type(bool_expr, deep+1, 'bool_expr-len:1')
        else:
            # Given a boolean expression of ORs: [a, OR, b, OR, c]
            # Create the following ast:
            #        OR
            #      /   \
            #   OR      c
            #  /  \
            # a    b

            first_exp = find_type(bool_expr[0], deep+1, 'bool_expr-len:%s'%len(bool_expr))
            or_exp = AST_OR(left_expr=first_exp)
            print('OR-right: %s' % str_deep, bool_expr[0])
            for item in bool_expr[1:]:
                if item != 'OR':
                    ast_expr = find_type(item, deep+1, 'bool_expr-len:%s'%len(bool_expr))
                    or_exp.right_expr = ast_expr
                    new_or = AST_OR(left_expr=or_exp)
                    or_exp = new_or
                    print('OR-left: %s' % item)
            return or_exp
    elif 'bool_term' in exp:
        bool_term = exp.bool_term[0]  # Because of the Group in bool_expr
        if len(bool_term) == 1:
            return find_type(bool_term, deep+1, 'bool_term-len:1')
        else:
            # Given a boolean expression of ORs: [a, OR, b, OR, c]
            # Create the following ast:
            #        OR
            #      /   \
            #   OR      c
            #  /  \
            # a    b

            first_exp = find_type(bool_term[0], deep+1, 'bool_expr-len:%s'%len(bool_term))
            and_exp = AST_AND(right_expr=first_exp)
            print('AND-right: %s' % str_deep, bool_term[0])
            for item in bool_term[1:]:
                if item != 'AND':
                    ast_expr = find_type(item, deep+1, 'bool_term-len:%s'%len(bool_term))
                    or_exp.left_expr = ast_expr
                    new_or = AST_AND(right_expr=or_exp)
                    or_exp = new_or
                    print('AND-left: %s' % item)
            return or_exp
    elif 'signed_factor' in exp:
        sign = exp.signed_factor[0]
        factor = exp.signed_factor[1]
        ast_expr = find_type(factor,  deep+1, 'signed_factor')
        print("signed-factor sign: %s" % sign)
        if sign == '-':
            return AST_NegArithExpr(ast_expr)
        return ast_expr
    elif 'term' in exp:
        print("term-len: %s  - term: %s" %(len(exp.term), exp.term))
        return AST_NegArithExpr(None)
    else:
        return find_type(exp[0], deep+1, 'unknown')





