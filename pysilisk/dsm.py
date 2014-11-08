__author__ = 'harold'

class DiskPage(object):

    @property
    def id(self):
        pass

    @property
    def next_page_id(self):
        pass

    @property
    def data(self):
        pass


class DiskSpaceManager(object):

    def __init__(self):
        pass

    def create_file(self, filename):
        pass

    def delete_file(self):
        pass

    def open_file(self, filename):
        pass

    def close_file(self):
        pass

    def allocate_new_page(self):
        pass

    def release_page(self, page_id):
        pass

    def write_page(self, disk_page):
        pass

    def read_page(self, page_id):
        pass

    @property
    def size(self):
        pass

    @property
    def num_pages(self):
        pass

