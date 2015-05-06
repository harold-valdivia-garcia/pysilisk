import ast
# Inpired in the Berkeley COOL Project

ast.parse()
ast.BinOp

class AST_Node(object):
    TABLE = -1
    EXPRESSION = -1
    DROP_TABLE = -1
    INSERT = -1
    PROJECTION = -1
    DELETE = -1
    NUM_CONST = 0
    BOOL_CONST = 1		# Boolean constant expression
    AND = 2		        # Conditional "and" expression
    EQ = 3		        # Conditional equality("=") expression
    GT = 4		        # Conditional greater than(">") expression
    GTE = 5		        # Conditional greater than or equal(">=") expression
    LT = 6		        # Conditional less than("<") expression
    LTE = 7		        # Conditional less than or equal("<=") expression
    NOT = 8		        # Conditional "not" expression
    OR = 9		        # Conditional "or" expression
    STRING_CONST = 10	# String constant expression
    COLUMN = 11		    # Column (table attribute) reference
    NO_EXPR = 12		# Stub for an empty expression
    ADD = 13		    # Arithmetic addition/plus("a+b") expression
    SUB = 14		    # Arithmetic substraction/minus("a-b") expression
    NEG = 15		    # Arithmetic negation ("-a") expression
    MULT = 16		    # Arithmetic multiplication ("a*b") expression
    DIV = 17		    # Arithmetic division ("a/b") expression
    FUNCTION_CALL = 18	# Function call expression

    def __init__(self, ast_id):
        self.ast_id = ast_id


class AST_Table(AST_Node):
    def __init__(self, ast_id, name, alias):
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
        super().__init__(self, ast_id)
        self.left_expr = left_expr
        self.right_expr = right_expr


class AST_AND(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Expression.AND)
        self.left_expr = left_expr
        self.right_expr = right_expr


class AST_OR(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Expression.OR)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_EQ(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Expression.EQ)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_GT(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Expression.GT)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_GTE(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Expression.GTE)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_LT(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Expression.LT)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_LTE(AST_BooleanExpr):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Expression.LTE)
        self.left_expr = left_expr
        self.right_expr = right_expr




class AST_BinaryArithOp(AST_Expression):
    def __init__(self, ast_id, left_expr, right_expr):
        super().__init__(self, ast_id)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_Div(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Node.DIV)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_Mult(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Node.MULT)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_Add(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Node.ADD)
        self.left_expr = left_expr
        self.right_expr = right_expr

class AST_Sub(AST_BinaryArithOp):
    def __init__(self, left_expr, right_expr):
        super().__init__(self, AST_Node.SUB)
        self.left_expr = left_expr
        self.right_expr = right_expr




class AST_DropTable(AST_Node):
    def __init__(self, table):
        super().__init__(AST_Node.DROP_TABLE)
        self.table = table


class AST_Insert(AST_Node):
    def __init__(self, list_values):
        super().__init__(AST_Node.INSERT)
        self.list_values = list_values


class AST_Delete(AST_Node):
    def __init__(self, table, where):
        super().__init__(AST_Node.DELETE)
        self.table = table
        self.where = where


"""
AllColumns.java
ColumnDef.java
CreateDef.java
CreateDefs.java
CreateIndex.java
CreateTable.java
DropIndex.java
Ident.java
Idents.java
IndexDef.java
ListNode.java
Neg.java
NoExpr.java
Not.java
OrderBy.java
Select.java




Expressions.java
Projections.java
CreateDatabase.java
Columns.java
Tables.java
TreeNode.java
Describe.java

    Plus.java
    Minus.java
    Mult.java
    BinaryOperator.java
    Div.java
    >>>>>Column.java
    >>>>Insert.java
    >>>>And.java
    >>>>>Condition.java
    >>>>Delete.java
    >>>>>DropTable.java
    >>>>>EQ.java
    >>>>> incomplete >>>>>>Expression.java
    >>>>FunctionCall.java
    >>>>GT.java
    >>>>GTE.java
    >>>>LT.java
    >>>>LTE.java
    >>>>NumConst.java
    >>>>Or.java
    >>>>>Projection.java
    >>>>>StringConst.java
    >>>>>Table.java
"""

