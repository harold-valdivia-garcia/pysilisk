import struct


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
        pass

    def create_file(self, num_pages):
        """Creates a file (database space) with 'num_pages' pages.
        num_pages - it should be at least 2.
        """
        pass

    def delete_file(self):
        pass

    def open_file(self):
        pass

    def close_file(self):
        pass

    def get_free_page(self):
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

