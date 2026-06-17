import os
import struct
from mmap import *
from sonic_py_common import device_info
from sonic_py_common.general import getstatusoutput_noshell

HOST_CHK_CMD = ["docker"]
EMPTY_STRING = ""

# Allowed base directories for file write operations
ALLOWED_WRITE_PATHS = [
    '/sys/bus/i2c/devices/',
    '/sys/devices/',
    '/sys/class/',
    '/run/',
    '/var/run/'
]


class APIHelper():

    def __init__(self):
        (self.platform, self.hwsku) = device_info.get_platform_and_hwsku()

    def is_host(self):
        try:
            status, output = getstatusoutput_noshell(HOST_CHK_CMD)
            return status == 0
        except Exception:
            return False

    def pci_get_value(self, resource, offset):
        status = True
        result = ""
        try:
            fd = os.open(resource, os.O_RDWR)
            mm = mmap(fd, 0)
            mm.seek(int(offset))
            read_data_stream = mm.read(4)
            result = struct.unpack('I', read_data_stream)
        except Exception:
            status = False
        return status, result

    def read_txt_file(self, file_path):
        try:
            with open(file_path, 'r', errors='replace') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

    def _is_path_allowed(self, file_path):
        """
        Validate that the file path is within allowed directories.
        
        Args:
            file_path: The file path to validate
            
        Returns:
            bool: True if path is allowed, False otherwise
        """
        try:
            # Resolve the real path to prevent directory traversal
            real_path = os.path.realpath(file_path)
            
            # Check if the resolved path starts with any allowed prefix
            for allowed_path in ALLOWED_WRITE_PATHS:
                if real_path.startswith(allowed_path):
                    return True
            
            return False
        except Exception:
            return False

    def write_txt_file(self, file_path, value):
        # Validate the file path before writing
        if not self._is_path_allowed(file_path):
            return False
        
        try:
            with open(file_path, 'w') as fd:
                fd.write(str(value))
        except IOError:
            return False
        return True