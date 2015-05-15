import logging
from pysilisk.sqltypes import SQLDataType, NullConstrain
from pysilisk.parser.sqlparser import SQL_GRAMMAR

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
            idx_name = 'pk_%s' % table_name
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
        print("column-col-name: %s " % column_name)
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





