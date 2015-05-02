import logging
import re
import os
import glob
import argparse

# Logging Configuration
logger = logging.getLogger()
logformat = """\n%(levelname)s: %(name)s: %(message)s"""
logging.basicConfig(level=logging.INFO, format=logformat)
logging.basicConfig(level=logging.INFO)


class PysiliskSQL:
    pass

class Connection(object):
    def __init__(self, db_path, buffer_size):
        self.db_path = db_path
        self.db_name = db_path.strip('/').split('/')[-1]

        # Open a direct access to pysilisk
        self.pysilisk_server = PysiliskSQL(self.db_path, buffer_size)
        if not os.path.exists(self.db_path):
            self.pysilisk_server.create_db()
        self.pysilisk_server.open_db()

    def execute(self, sql_str):
        pass

    def close(self):
        pass

    def has_resultset(self):
        pass

    def resultset(self):
        pass

    @property
    def affected_rows(self):
        pass

    @property
    def execution_time(self):
        pass

class SimpleCli:
    """A simple REPL (Read–Eval–Print Loop) to submit commands to PysiliskSQL"""
    def __init__(self):
        self.data_directory = ""
        self.db_conn = Connection()

    @property
    def prompt(self):
        return "%s>" % self.db_conn.db_name

    def run_cli(self):
        """REPL (Read–Eval–Print Loop) to submit commands to PysiliskSQL"""
        while True:
            str_cmd = input(self.prompt).strip()
            if str_cmd.startswith('\\'):
                # Process meta-commands
                if str_cmd == '\\q':
                    self.db_conn.close()
                    break
                self.process_meta_command(str_cmd)
            elif str_cmd != '':
                # Process DDL and DML queries
                self.process_sql_query(str_cmd)
        print('Bye, bye ...')

    def process_meta_command(self, str_cmd):
        if meta_cmd_is_valid(str_cmd):
            if str_cmd == '\\h':
                help_cmd()
            elif re.match(r'^\\c \w+$', str_cmd):
                self.db_conn.close()
                # Open a new connection
                db_name = str_cmd.split()[-1]
                db_path = os.path.join(self.data_directory, db_name)
                self.db_conn = create_connection(db_path)
                print('You are now connected to database "%s"' % db_name)
            elif str_cmd == '\\sd':
                # Show the databases
                db_dirs = glob.glob(os.path.join(self.data_directory,'*/'))
                for dir in db_dirs:
                    db_name = dir.strip('/').split("/")[-1]
                    print(db_name)
        else:
            print('Invalid command "%s". Try \h for help.'%str_cmd)

    def process_sql_query(self, str_query):
        self.db_conn.execute(str_query)
        if self.db_conn.has_resultset():
            print_rs(self.db_conn.resultset())
        else:
            print('Affected rows: %s' % self.db_conn.affected_rows)
            print('Execution time: %s' % self.db_conn.execution_time)


def print_rs(result_set):
    """Output the rows of the result-set"""
    num_retrieved_rows = 0
    for row in result_set:
        print(row)
        num_retrieved_rows += 1
    print('Query runtime: %s' % result_set.execution_time)
    print('Retrieved rows: %s' % num_retrieved_rows)


def help_cmd():
    """Output help-information"""
    help_txt = ('You are using the command-line interface to PysiliskSQL.',
                'Type:  \\h        : help.',
                '       \\q        : quit the pysilik console.',
                '       \\sd       : show databases.',
                '       \\c dbname : connect to dbname.',
                '                    create a new db if dbname doesn\'t exist')
    help_txt = ['%s' % s for s in help_txt]
    print('\n'.join(help_txt))


def meta_cmd_is_valid(meta_cmd):
    """Check if it is a valid-meta-command"""
    if meta_cmd == '\\h' or meta_cmd == '\\sd' or meta_cmd == '\\q':
        return True
    if re.compile(r'^\\c \w+$', meta_cmd):
        return  True
    return False


def create_connection(db_path):
    conn = Connection(db_path=db_path)
    return conn


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pysilisk-dir',
                        metavar='DIRECTORYPATH',
                        required=True,
                        help="set the data-directory of PysiliskSQL")
    args = parser.parse_args()
    # Run the pysilisk-shell
    cmd_line = SimpleCli(data_directory=args.pysilisk_dir)
    cmd_line.run_cli()
