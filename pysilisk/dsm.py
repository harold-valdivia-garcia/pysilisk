import struct
import os
import io

class DiskPage(object):
    """ """

    PAGE_SIZE = 4096  # Size of a physical disk-page

    ID_SIZE = 4  # Number of bytes used to store the page-id

    NEXT_PAGE_ID_SIZE = 4  # Number of bytes used to store the next-page-id

    # Size of the available data in the disk-page
    PAGE_DATA_SIZE = PAGE_SIZE - ID_SIZE - NEXT_PAGE_ID_SIZE

    # struct-format to pack/unpack a disk-page into/from bytes.
    # The integers are packed using little-endian (<)
    FMT_PACK_UNPACK_PAGE = '<{data_size}sii'.format(data_size=PAGE_DATA_SIZE)

    def __init__(self, page_id=-1):
        if page_id < -1:
            raise ValueError("Page-id must be greater than or equal to -1")
        self._data = bytearray(DiskPage.PAGE_DATA_SIZE)
        self._id = page_id
        self.next_page_pointer = -1

    @property
    def id(self):
        return self._id

    @property
    def data(self):
        #return bytes(self._data)
        return self._data

    @data.setter
    def data(self, value):
        if len(value) != DiskPage.PAGE_DATA_SIZE:
            raise ValueError('The length of argument value must'
                             ' be the same as PAGE_DATA_SIZE')
        self._data[:] = value  # This ensure not to change the _data's type

    @staticmethod
    def from_bytes(array_bytes):
        # Unpack the bytes into "data, "id" and "next"
        fields = struct.unpack(DiskPage.FMT_PACK_UNPACK_PAGE, array_bytes)
        data, page_id, next_page_pointer = fields

        # Create the page
        disk_page = DiskPage(page_id)
        disk_page.data = data
        disk_page.next_page_pointer = next_page_pointer
        return disk_page

    @staticmethod
    def to_bytes(disk_page):
        # Pack the disk_page as bytes
        array_bytes = struct.pack(DiskPage.FMT_PACK_UNPACK_PAGE,
                                  disk_page._data,
                                  disk_page._id,
                                  disk_page.next_page_pointer)
        return array_bytes


class DiskSpaceManager(object):
    def __init__(self, filename):
        self.filename = filename
        self._is_opened = False
        self._dbfile = io.BytesIO()  # dummy file to avoid from checking
        self._dbfile.close()         # _dbfile == None everytime

    def create_file(self, num_pages):
        """Creates a file (database space) with 'num_pages' pages.
        num_pages - it should be at least 2.
        """
        if num_pages < 2:
            raise ValueError('Num-pages must be greater than or equal to two')
        if os.path.exists(self.filename):
            raise OSError('The filename %s already exists' % self.filename)

        # Create a sequence of connected disk-pages
        with open(self.filename, 'wb') as f:
            for i in range(num_pages):
                disk_page = DiskPage(i)
                if i < num_pages - 1:
                    disk_page.next_page_pointer = i+1
                f.write(DiskPage.to_bytes(disk_page))

    def delete_file(self):
        self.close_file()
        if not os.path.exists(self.filename):
            raise OSError('Could not delete the db space.')
        os.remove(self.filename)

    def open_file(self):
        if not self._dbfile.closed:
            if not os.path.exists(self.filename):
                raise OSError('File %s  does not exist.' % self.filename)
            self._dbfile = open(self.filename, 'wb')
            self._size = os.path.getsize(self.filename)

    def close_file(self):
        self._dbfile.close()

    def get_free_page(self):
        pass

    def release_page(self, page_id):
        # before release page:
        #     page   --> another_page
        #     header --> first_free
        #
        # step 1:
        #          page
        #              ¯¯¯¯v
        #     header --> first_free
        #
        # step 2:
        #     header --> page --> first_free

        if page_id < 0 or page_id >= self._num_pages:
            msg = 'Page-id %s is outside of the db space.' % page_id
            raise ValueError(msg)

        # Easiest-approach:
        # ---------------
        #    # Get the first-free-page
        #    header = self.read_page(0)
        #    first_free_id = header.next_page_pointer
        #
        #    # page --> first_free
        #    page = self.read_page(page_id)
        #    page.next_page_pointer = first_free_id
        #    self.write_page(page)
        #
        #    # header --> page
        #    header.next_page_pointer = page_id
        #    self.write_page(header)

        # The following code avoids the overhead caused by
        # read_page and write_page (ifs and the offset calculations).

        # Get the first-free-page
        self._dbfile.seek(0)
        array_bytes = self._dbfile.read(DiskPage.PAGE_SIZE)
        header = DiskPage.from_bytes(array_bytes)
        first_free_id = header.next_page_pointer

        # page --> first-free
        offset_page = page_id*DiskPage.PAGE_SIZE
        self._dbfile.seek(offset_page)
        array_bytes = self._dbfile.read(DiskPage.PAGE_SIZE)
        page = DiskPage.from_bytes(array_bytes)
        page.next_page_pointer = first_free_id
        self._dbfile.seek(offset_page)
        self._dbfile.write(DiskPage.to_bytes(page))

        # header --> page
        header.next_page_pointer = page_id
        self._dbfile.seek(0)
        self._dbfile.write(DiskPage.to_bytes(header))

    def write_page(self, disk_page):
        if disk_page.id < 0 or disk_page.id >= self._num_pages:
            msg = 'Page-id %s is outside of the db space.' % disk_page.id
            raise ValueError(msg)
        self._dbfile.write(DiskPage.to_bytes(disk_page))

    def read_page(self, page_id):
        if page_id < 0 or page_id >= self._num_pages:
            msg = 'Page-id %s is outside of the db space.' % page_id
            raise ValueError(msg)

        # Read the page from disk
        self._dbfile.seek(page_id*DiskPage.PAGE_SIZE)
        array_bytes = self._dbfile.read(DiskPage.PAGE_SIZE)
        return DiskPage.from_bytes(array_bytes)



