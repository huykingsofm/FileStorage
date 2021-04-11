import os

MAX_BUFFER = 3 * 1024 * 1024 # 3MB
FROM_START = 0  # 'whence' arg of seek() method of io
FROM_CUR = 1    # 'whence' arg of seek() method of io
FROM_END = 2    # 'whence' arg of seek() method of io

class Util(object):
    @staticmethod
    def get_file_elements(
            file_name: str,
            positions: list,
            min_of_positions: int = None,
            max_of_positions: int = None
        ):
        if not min_of_positions:
            min_of_positions = min(positions)

        if not max_of_positions:
            max_of_positions = max(positions)

        if max_of_positions - min_of_positions > MAX_BUFFER:
            raise Exception("Cannot read because out of buffer")

        with open(file_name, "rb") as file:
            file.seek(min_of_positions)
            array = file.read(max_of_positions - min_of_positions + 1)
            func = lambda position: array[position - min_of_positions]
            values = bytes(map(func, positions))
        return values

    @staticmethod
    def get_identifier(file_name, identifier_size):
        with open(file_name, "rb") as file:
            file.seek(-identifier_size, FROM_END)
            last_bytes = file.read(identifier_size)
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
            

    @staticmethod
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