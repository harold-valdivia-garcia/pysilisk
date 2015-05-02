class DDLCompiler(object):
    pass

class QueryCompiler(object):
    class QueryParser(object):
        pass
    class QueryOptimizer(object):
        pass
    #QueryPreProcessor

class ExecutionEngine(object):
    pass

class BufferManager(object):
    pass

class IndexManager(object):
    pass

class FileManager(object):
    pass

class RecordManager(object):
    pass

class ResultSet(object):
    def __init__(self, physical_plan):
        self._physical_plan = physical_plan
        self._buffer_tuples = []
        self._size_buffer = len(self.buffer_tuples)
        self._idx_next == 0

    def __iter__(self):
        return self

    def next(self):
        if self._idx_next == self._size_buffer:
            self._buffer_tuples = self._physical_plan.next()
            self._size_buffer = len(self._buffer_tuples)
            if self._size_buffer == 0:
                raise StopIteration()
            self._idx_next = 0
        next_row = self._buffer_tuples[self._idx_next]
        self._idx_next += 1
        return next_row


# http://en.wikibooks.org/wiki/Python_Programming/Source_Documentation_and_Comments
# http://thomas-cokelaer.info/tutorials/sphinx/docstring_python.html
# http://thomas-cokelaer.info/tutorials/sphinx/docstring_python.html

class PysiliskDB:
    ddl_compiler = DDLCompiler()
    def __init__(self):
        self.ddl_compiler = DDLCompiler()
        self.query_compiler = QueryCompiler()
        self.engine = ExecutionEngine()
        self.buff_mngr = BufferManager()
        self.sql_preprocessor = 1
        self.query_preproc = 1
        self.sql_preprocsr = 1

    def execute(self, sql_str):
        parse_tree = self.parser(sql_str)
        # semantic check with the query_preprocessor
        annotate_tree = self.sql_preprocsr.check_and_annotate_tree(parse_tree)
        if parse_tree.type == self.parser.DDL_STMT_TYPE:
            #
            self.affected_rows = -1
        if parse_tree.type == self.parser.DML_STMT_TYPE:
            pass
            # Create a logical-plan
            # create a phisical-plan using an optimizer
            # Create a wrapper of the physical-plan that simulate the results-of-the-query
            physical_plan = None
            self._resultset = ResultSet(physical_plan)




    def close(self):
        pass