import os
import struct
from mmap import *
from sonic_py_common import device_info
from sonic_py_common.general import getstatusoutput_noshell

HOST_CHK_CMD = ["docker"]
EMPTY_STRING = ""


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
            # Validate resource path - must be a PCI resource file
            resource = os.path.realpath(resource)
            if not resource.startswith('/sys/bus/pci/devices/') and \
               not resource.startswith('/sys/devices/pci'):
                return False, "Invalid PCI resource path"
            
            # Validate offset is non-negative and reasonable
            try:
                offset_int = int(offset)
                if offset_int < 0:
                    return False, "Invalid offset: must be non-negative"
                # PCI config space is typically 256 bytes (legacy) or 4096 bytes (PCIe)
                # Resource files can be larger, but set a reasonable upper bound
                if offset_int > 0x100000:  # 1MB max offset
                    return False, "Invalid offset: exceeds maximum allowed"
            except (ValueError, TypeError):
                return False, "Invalid offset: must be an integer"
            
            # Use O_RDONLY since we only need to read
            fd = os.open(resource, os.O_RDONLY)
            try:
                # Get file size to validate offset + read size
                file_stat = os.fstat(fd)
                file_size = file_stat.st_size
                
                if offset_int + 4 > file_size:
                    return False, "Offset exceeds resource size"
                
                # Map only the necessary region instead of entire file
                # Map from offset (page-aligned) with minimal size
                page_size = os.sysconf('SC_PAGE_SIZE')
                map_offset = (offset_int // page_size) * page_size
                map_size = offset_int - map_offset + 4
                
                mm = mmap(fd, map_size, prot=PROT_READ, offset=map_offset)
                try:
                    mm.seek(offset_int - map_offset)
                    read_data_stream = mm.read(4)
                    if len(read_data_stream) != 4:
                        return False, "Failed to read 4 bytes"
                    result = struct.unpack('I', read_data_stream)
                finally:
                    mm.close()
            finally:
                os.close(fd)
        except Exception as e:
            status = False
            result = str(e)
        return status, result

    def read_txt_file(self, file_path):
        try:
            with open(file_path, 'r', errors='replace') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

    def write_txt_file(self, file_path, value):
        try:
            with open(file_path, 'w') as fd:
                fd.write(str(value))
        except IOError:
            return False
        return True