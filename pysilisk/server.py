import os


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
        self._physical_plan.open()
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
                self._physical_plan.close()
                raise StopIteration()
            self._idx_next = 0
        next_row = self._buffer_tuples[self._idx_next]
        self._idx_next += 1
        return next_row


def create_pysilisk_server(db_path):
    pass


class PysiliskSQL:
    """Facade component"""

    def __init__(self, db_directory_path):
        self.db_directory_path = db_directory_path
        self.ddl_compiler = DDLCompiler()
        self.query_compiler = QueryCompiler()
        self.engine = ExecutionEngine()
        self.buff_mngr = BufferManager()
        self.sql_preprocessor = 1
        self.query_preproc = 1
        self.sql_preprocsr = 1
        self.result_set = None
        self.ddl_manager = None
        self.parser = None
        self.optimizer = None

    def execute(self, sql_str):
        # Create and check the ast-tree that represent the query
        query_tree = self.parser.parse_query(sql_str)
        checked_query_tree = self.sql_preprocsr.semantic_check(query_tree)

        if not checked_query_tree.is_dml_stmt():
            physical_plan = self.ddl_manager.evaluate(checked_query_tree)
        else:
            # Create a logical-plan | plan-rewriter| do basic transformations
            # create a physical-plan using the optimizer
            # Create a wrapper of the physical-plan that
            # simulate the results-of-the-query
            #: Optimize is a better word but I use evaluate because ddlmanager
            #: uses it
            physical_plan = self.optimizer.evaluate(checked_query_tree)

        result = physical_plan.execute()
        if isinstance(result, int):
            self.affected_rows = result
            self.result_set = None
        elif isinstance(result, ResultSet):
            self.result_set = result
            self.affected_rows = -1

    def open(self):
        if not os.path.exists(self.db_directory_path):
            self.pysilisk_server.create_db()
        self.pysilisk_server.open_db()

    def close(self):
        pass



# Notes:
# =========================
# http://en.wikibooks.org/wiki/Python_Programming/Source_Documentation_and_Comments
# http://thomas-cokelaer.info/tutorials/sphinx/docstring_python.html
# http://thomas-cokelaer.info/tutorials/sphinx/docstring_python.html

# Note: A physical-plan is not an iterator
# We use two different concepts: relational-operators(iterators)
# and Plans. A plan can wrap a set of rel-operators or DDL-code


# Purdue professor: clifton
# =========================
# Minisql-mini in Java:
#https://www.cs.purdue.edu/homes/clifton/cs541/project4/javadocs/index.html?query/Insert.html
# CS541 Spring12 - Project 4: Query Evaluation and Optimization
#https://www.cs.purdue.edu/homes/clifton/cs541/project4/project4.zip
#https://www.cs.purdue.edu/homes/clifton/cs541/project2/
#https://www.cs.purdue.edu/homes/clifton/cs541/project4/


# Original MINI just doc
# =========================
# http://research.cs.wisc.edu/coral/minibase/


# Berkeley:
# =========================
#https://inst.eecs.berkeley.edu/~cs186/sp07/homework/hw1/hw1.html
# https://inst.eecs.berkeley.edu/~cs186/sp07/homework/hw2/hw2.html
#https://inst.eecs.berkeley.edu/~cs186/sp07/projects.html


# Portland:
# =========================
# http://web.cecs.pdx.edu/~tufte/dbimplem-spr2014/
#http://www.cse.unsw.edu.au/~cs9315/14s2/notes/G/notes.html
#http://cgi.cse.unsw.edu.au/~cs9315/14s2/index.php

# =========================
# http://www.cse.unsw.edu.au/~cs9315/14s2/notes/A/notes.html

# =======================================================================
