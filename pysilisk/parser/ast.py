from pysilisk.types import SQLDataType, NullConstrain
from pysilisk.parser.sqlparser import sql_stmt

# Inpired in the Berkeley COOL Project


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
    def __init__(self, col_name, tbl_name=None):
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
    def __init__(self, left_expr, right_expr):
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
    def __init__(self, list_values):
        super().__init__(AST_Node.INSERT)
        self.list_values = list_values


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
    def __init__(self, column_name, type_name, type_size, nullable):
        super().__init__(AST_Node.COLUMN_DEFINITION)
        self.column_name = column_name
        self.type_name = type_name
        self.type_id = SQLDataType.from_string(type_name)
        self.type_size = type_size  # Only for varchar and char types
        self.nullable = nullable


class AST_CreateTable(AST_Node):
    def __init__(self, table_name, col_definitions, index_definition):
        super().__init__(AST_Node.CREATE_TABLE)
        self.table_name = table_name
        self.col_definitions = col_definitions
        self.index_definition = index_definition


# Initial parse-implementation:
def parse(sql_str):
    result = sql_stmt.parseString(sql_str)
    stmt_type = result.getName()
    if stmt_type == 'DROP_INDEX':
        index_name = result.index_name[0]
        table_name = result.table_name[0]
        return AST_DropIndex(index_name, table_name)
    elif stmt_type == 'DROP_TABLE':
        table_name = result.table_name[0]
        return AST_DropTable(table_name)
    elif stmt_type == 'CREATE_INDEX':
        idx_type = result.index_type
        idx_name = result.index_name[0]
        table_name = result.table_name[0]
        list_idx_columns = [c for c in result.list_index_columns]
        return AST_CreateIndex(idx_name, table_name, list_idx_columns, idx_type)
    elif stmt_type == 'CREATE_TABLE':
        table_name = result.table_name[0]
        # Extract column-definitions
        ast_column_defs = []
        for definition in result.list_column_defs:
            col_name = definition.column_name
            type_name = definition.type_name
            type_size = definition.data_type.size
            type_size = int(type_size) if type_size.isdigit() else -1
            nullable = ' '.join(definition.null_constrain)
            nullable = NullConstrain.from_string(nullable)
            # Create and append an ast-definition
            ast_column_defs.append(
                AST_ColumnDefinition(col_name, type_name, type_size, nullable)
            )
        # Extract index information
        ast_idx = None
        if result.index_type != '':
            idx_type = result.index_type
            idx_columns = [c for c in result.list_index_columns]
            idx_name = 'pk_%s' % table_name
            ast_idx = AST_CreateIndex(idx_name, table_name, idx_columns, idx_type)
        return AST_CreateTable(table_name, ast_column_defs, ast_idx)

