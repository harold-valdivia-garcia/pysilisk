import logging
import re
import os
import glob
import argparse
from pysilisk.server import PysiliskSQL

# Logging Configuration
logger = logging.getLogger()
logformat = """\n%(levelname)s: %(name)s: %(message)s"""
logging.basicConfig(level=logging.INFO, format=logformat)
logging.basicConfig(level=logging.INFO)


class MetaCMD(object):
    """
    Meta-commands always begin with "\". These commands are implemented
    in the cli-component.
        \h        : help.',
        \q        : quit the pysilik console
        \sd       : show databases.
        \c dbname : connect to dbname
                    create a new db if dbname does not exist
    """
    QUIT = '\\q'
    HELP = '\\h'
    SHOW_DBs = '\\sd'
    CONNECT_DB = r'^\\c \w+$'
    @classmethod
    def meta_cmd_is_valid(cls, meta_cmd):
        """Check if it is a valid-meta-command"""
        if meta_cmd in [cls.HELP, cls.SHOW_DBs, cls.QUIT]:
            return True
        if re.compile(cls.CONNECT_DB, meta_cmd):
            return  True
        return False


class SimpleCli:
    """A simple REPL (Read–Eval–Print Loop) to submit commands to PysiliskSQL"""
    def __init__(self):
        self.data_directory = ""
        self.pysilisk_server = PysiliskSQL()

    @property
    def prompt(self):
        return "%s>" % self.pysilisk_server.db_name

    def run_cli(self):
        """REPL (Read–Eval–Print Loop) to submit commands to PysiliskSQL"""
        while True:
            str_cmd = input(self.prompt).strip()
            if str_cmd.startswith('\\'):
                # Process meta-commands
                if str_cmd == MetaCMD.QUIT:
                    self.pysilisk_server.close()
                    break
                self.process_meta_command(str_cmd)
            elif str_cmd != '':
                # Process DDL and DML queries
                self.process_sql_query(str_cmd)
        print('Bye, bye ...')

    def process_meta_command(self, str_cmd):
        if MetaCMD.meta_cmd_is_valid(str_cmd):
            if str_cmd == MetaCMD.HELP:
                help_cmd()
            elif re.match(MetaCMD.CONNECT_DB, str_cmd):
                self.pysilisk_server.close()
                # Open a new connection
                cmd, db_name = str_cmd.split()  # str_cmmd = "\c dbname"
                db_path = os.path.join(self.data_directory, db_name)
                self.pysilisk_server = create_pysilisk_server(db_path)
                print('You are now connected to database "%s"' % db_name)
            elif str_cmd == MetaCMD.SHOW_DBs:
                # Show the databases in the data-dir
                for db_name in list_subdirs(self.data_directory):
                    print(db_name)
        else:
            print('Invalid command "%s". Try \\h for help.'%str_cmd)

    def process_sql_query(self, str_query):
        self.pysilisk_server.execute(str_query)
        if self.pysilisk_server.has_resultset():
            print_rs(self.pysilisk_server.resultset())
        else:
            print('Affected rows: %s' % self.pysilisk_server.affected_rows)
            print('Execution time: %s' % self.pysilisk_server.execution_time)


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
                '                    create a new db if dbname does not exist')
    help_txt = ['%s' % s for s in help_txt]
    print('\n'.join(help_txt))


def list_subdirs(root_dir):
    fullpath_dirs = glob.glob(os.path.join(root_dir,'*/'))
    sub_dirs = []
    for dir in fullpath_dirs:
        subdir = dir.strip('/').split("/")[-1]
        sub_dirs.append(subdir)
    return sub_dirs


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--pysilisk-dir',
                        metavar='DIRECTORYPATH',
                        required=True,
                        help="set the data-directory of PysiliskSQL")
    args = arg_parser.parse_args()

    # Run the pysilisk-shell
    cmd_line = SimpleCli(data_directory=args.pysilisk_dir)
    cmd_line.run_cli()
