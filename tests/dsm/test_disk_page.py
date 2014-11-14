from unittest import TestCase
from pysilisk.dsm import DiskPage
import os
import struct
import io

__author__ = 'harold'


class TestDiskPage(TestCase):
    def test_data(self):
        self.fail()

    def test_from_bytes(self):
        # Create an in-memory stream with the size of a disk-page
        buffer = io.BytesIO(bytearray(DiskPage.PAGE_SIZE))

        # Generate a random content for the page
        data = bytearray(os.urandom(DiskPage.PAGE_DATA_SIZE))
        buffer.write(data)

        # set the page-id
        page_id = 5
        page_id_as_bytes = struct.pack('<i', page_id)
        buffer.write(page_id_as_bytes)

        # write the next-page pointer
        next_page_id = 11
        next_page_id_bytes = struct.pack('<i', next_page_id)
        buffer.write(next_page_id_bytes)

        # Create a disk-page
        buffer.seek(0)
        disk_page = DiskPage.from_bytes(buffer.read(DiskPage.PAGE_SIZE))

        self.assertEqual(page_id, disk_page.id)
        self.assertEqual(next_page_id, disk_page.next_page_pointer)
        self.assertEqual(data, disk_page.data)

    def test_to_bytes(self):
        # Create a disk-page
        disk_page = DiskPage()

        # Generate a random content for the page
        data = bytearray(os.urandom(DiskPage.PAGE_DATA_SIZE))
        disk_page.data = data

        # Set the id and the next-page
        id_page = 17
        disk_page.id = id_page
        nex_id = 33
        disk_page.next_page_pointer = nex_id

        # Convert to bytes
        array_bytes = DiskPage.to_bytes(disk_page)
        self.assertEqual(len(array_bytes), DiskPage.PAGE_SIZE)

        # Wrap it with a in-memory stream
        buffer = io.BytesIO(array_bytes)

        # get the fields from the bytes
        data_from_bytes = buffer.read(DiskPage.PAGE_DATA_SIZE)
        id_from_bytes, next_id_from_bytes = struct.unpack('<ii', buffer.read(8))

        self.assertEqual(data, data_from_bytes)
        self.assertEqual(id_page, id_from_bytes)
        self.assertEqual(nex_id, next_id_from_bytes)
