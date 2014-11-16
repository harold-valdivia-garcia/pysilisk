from unittest import TestCase
from pysilisk.dsm import DiskSpaceManager, DiskPage
import os


class TestDiskSpaceManager(TestCase):

    def setUp(self):
        # Create a 10-pages database
        self.database_filename = 'test_database.db'
        self.dsm = DiskSpaceManager(self.database_filename)
        self.num_pages = 10
        self.dsm.create_file(self.num_pages)

    def tearDown(self):
        if os.path.exists(self.test_database_filename):
            os.remove(self.test_database_filename)

    def extra_setup_teardown(method_to_decorate):
        def wrapper(self):
            self.dsm.open_file()
            result = method_to_decorate(self)
            self.dsm.close_file()
            return result
        return wrapper

    def test_create_file(self):
        # The file-size should be the same
        expected_size = self.num_pages*DiskPage.PAGE_SIZE
        real_size = os.path.getsize(self.test_database_filename)
        self.assertEqual(expected_size, real_size)

    def test_delete_file(self):
        self.dsm.delete_file()
        self.assertFalse(os.path.exists(self.test_database_filename))

    def test_open_file(self):
        filename = 'temp-db.db'
        dsm = DiskSpaceManager(filename)
        # An indirect way to check if the file is opened
        with self.assertRaises(OSError):
            self.dsm.open_file()
            self.dsm.delete_file()  # raise exception because it is open
        self.dsm.close_file()

    @extra_setup_teardown
    def test_get_free_and_release_pages(self):
        # A database has the following free-pages:
        # 1, 2, 3, 4, 5, 6 ... num_pages
        # and page-0 is reserved
        #
        # The ids of the first four free-pages are:  1, 2, 3, 4
        for page_id in [1, 2, 3, 4]:
            disk_page = self.dsm.get_free_page()
            self.assertEqual(page_id, disk_page.id)

        # Release pages in the following order
        self.dsm.release_page(2)
        self.dsm.release_page(4)
        self.dsm.release_page(1)
        self.dsm.release_page(3)

         # The ids of the first four free-pages are:  3, 1, 4, 2
        for page_id in [3, 1, 4, 2]:
            disk_page = self.dsm.get_free_page()
            self.assertEqual(page_id, disk_page.id)

    @extra_setup_teardown
    def test_write_page(self):
        # Create "num_pages" disk-pages with random data
        list_data = list()
        for i in range(self.num_pages):
            data = bytearray(os.urandom(DiskPage.PAGE_DATA_SIZE))
            #disk_page = DiskPage(i) --> this will destroy the next-page-id
            disk_page = self.dsm.read_page(i)
            disk_page.data = data.copy()
            self.dsm.write_page(disk_page)
            list_data.append(data)
        # Read again the pages and check the content
        for i in range(self.num_pages):
            disk_page = self.dsm.read_page(i)
            self.assertEqual(disk_page.data, list_data[i])

        # Try to write outside the database-space
        with self.assertRaises(OSError):
            disk_page = DiskPage(self.num_pages+10)
            self.dsm.write_page(disk_page)

    @extra_setup_teardown
    def test_read_page(self):
        for i in range(self.num_pages):
            disk_page = self.dsm.read_page(i)
            self.assertEqual(i, disk_page.id)
