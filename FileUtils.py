import os
import re
import random

MAX_BUFFER = 3 * 1024 * 1024 # 3MB
FROM_START = 0 # whence arg of seek() method of io
FROM_CUR = 1   # whence arg of seek() method of io
FROM_END = 2   # whence arg of seek() method of io

class File(object):
    @staticmethod
    def _get_element(file, position):
        file.seek(position)
        return file.read(1)

    @staticmethod
    def _get_element_in_array(array, position):
        return array[position]
        
    @staticmethod
    def get_elements(file_name, positions, min_of_positions = None, max_of_positions = None):
        if not min_of_positions:
            min_of_positions = min(positions)

        if not max_of_positions:
            max_of_positions = max(positions)

        if max_of_positions - min_of_positions > MAX_BUFFER:
            raise Exception("Cannot read because out of buffer")

        with open(file_name, "rb") as file:
            file.seek(min_of_positions)
            array = file.read(max_of_positions - min_of_positions + 1)
            func = lambda position: File._get_element_in_array(array, position - min_of_positions)
            values = bytes(map(func, positions))
        return values

    @staticmethod
    def get_elements_at_the_end(file_name, n_elements):
        with open(file_name, "rb") as file:
            file.seek(-n_elements, FROM_END)
            last_bytes = file.read(n_elements)
            return last_bytes

    @staticmethod
    def readlines(file_name, mode = "rt", remove_endline = True):
        file = open(file_name, mode)
        for line in file:
            if remove_endline:
                line = line.rstrip("\n")
            if line:
                yield line
        file.close()
            

def split_path(path, stop = None, include_stop = True):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            if parts[1] == stop:
                if include_stop:
                    allparts.insert(0, parts[1])
                break
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts