import logging
import re
import os
import glob

# Logging Configuration
logger = logging.getLogger()
logformat = """\n%(levelname)s: %(name)s: %(message)s"""
logging.basicConfig(level=logging.INFO, format=logformat)
logging.basicConfig(level=logging.INFO)


class Connection(object):
    pass


def print_rs(res):
    for row in res:
        # Print row
        pass


class Cli:
    """A simple REPL (Read–Eval–Print Loop) to submit commands to PysiliskSQL"""
    def __init__(self):
        self.data_directory = ""
        self.db_conn = None

    @property
    def prompt(self):
        return "%s>" % self.db_conn.db_name

    def run_cli(self):
        """REPL (Read–Eval–Print Loop) to submit commands to PysiliskSQL"""
        while True:
            str_cmd = input(self.prompt).strip()
            if str_cmd.startswith('\\'):
                # Process meta-commands
                if str_cmd.upper == '\\Q':
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
            elif re.match(r'^\\C \w+$', str_cmd.upper()):
                self.db_conn.close()
                # Open a new connection
                db_name = str_cmd.split()[-1]
                db_path = os.path.join(self.data_directory, db_name)
                self.db_conn = create_connection(db_path)
            elif str_cmd == '\\sd':
                # Show the databases
                db_dirs = glob.glob(os.path.join(self.data_directory,'*/'))
                for dir in db_dirs:
                    db_name = dir.strip('/').split("/")[-1]
                    print(db_name)
        else:
            print('Invalid command "%s". Try \h for help.'%str_cmd)

    def process_sql_query(str_query):
        pass



def help_cmd():
    help_txt = ("You are using the command-line interface to PysiliskSQL.",
                "Type:  \\h          : help",
                "       \\q          : quit the pysilik console",
                "       \\sd         : show databases",
                "       \\c <dbname> : connect to database")
    help_txt = ['%s' % s for s in help_txt]
    print('\n'.join(help_txt))


def meta_cmd_is_valid(str_cmd):
    pass


def create_connection(db_path):
    pass


# def do_main():
#     data_directory = 'pisilik-dbs/'
#     conn = Connection(data_directory)
#
#     cursor = conn.create_cursor()
#     while True:
#         raw_sql = input()
#         is_rs = cursor.execute(raw_sql)
#         if is_rs:
#             rs = cursor.get_result_set()
#             print_rs(rs)
#         else:
#
#
#         if res.error_code == 0:
#             pass
#
#         if res.is_result_set:
#             print_result_set(res)