import os
import re
import random
import shutil

from .FileUtils import split_path, File

N_SPLITS = 3
N_BYTES_FOR_IDENTIFYING = 100
NAME_OF_PROPERTY_IN_LEAF = ".files"
NAME_OF_PROPERTY_IN_STORAGE = ".storage"

class FileStorageException(Exception): ...
class NotReadInfoYet(FileStorageException): ...
class WrongPath(FileStorageException): ...

def __extract_node__(node):
    n_childs = int(node[0])
    childs = []

    for i in range(n_childs):
        child = {}
        child["name"] = node[2 * i + 1]
        child["line"] = int(node[2 * i + 2])
        childs.append(child)

    return childs


# structure storage
# -- ORIGINAL_DIR/
# ----- 1/
# ----------- 41238871928011
# ----------- 32419818231726
# ----------- .files
# ----- 2/
# ----------- 12341876191287
# ----------- 89182694192839
# ----------- 12986912983733
# ----------- 98102423813280
# ----------- .files
# ----- 3/
# ----------- 12930189280192
# ----------- .files
# ----- 4/
# ----------- .files
# ----- .storage

# .storage:
# 0. 1 root_name root_line (= 1)
# 1. N child1_name child1_line child2_name child2_line ... childN_name childN_line (root_line)
# 2. N child11_name child11_line child12_name child12_line ... child1N_name child1N_line (child1_line)
# 3. N child21_name child21_line child22_name child22_line ... child2N_name child2N_line (child2_line)
# 4. ...
# X. 0 (if this node is leaf node)

class StorageStructure(object):
    @staticmethod
    def initialize(root_name: str, file_path):
        root_name = root_name.replace("/", "")
        root_name = root_name.replace("\\", "")
        with open(file_path, "wt") as file:
            file.write(f"1 {root_name} 1\n")
            file.write(f"0")

    def hash_byte(self, byte):
        return str(byte % self.__n_splits__)

    def __init__(self, n_splits):
        self.__n_splits__ = n_splits

    def read(self, prop_file):
        with open(prop_file, "rt") as file:
            self.__tree__ = file.readlines()

        split = lambda s: re.split(r"\s", s)
        self.__tree__ = map(split, self.__tree__)
        self.__tree__ = list(map(__extract_node__, self.__tree__))
        self.__original_directory__ = self.__tree__[0][0]["name"]

    def write(self, prop_file):
        with open(prop_file, "wt") as file:
            for node in self.__tree__:
                file.write(str(len(node)))
                for child in node:
                    file.write(" " + child["name"])
                    file.write(" " + str(child["line"]))
                file.write("\n")

    def add_file(self, path):
        if os.path.isfile(path) == False:
            raise WrongPath("File is not exist")

        dir_path, file_name = os.path.split(path)
        node_idx = self.get_nodeidx_from_path(dir_path)

        if len(self.__tree__[node_idx]) != 0:
            raise WrongPath("File cannot be stored at {}".format(dir_path))

        prop_file = os.path.join(dir_path, NAME_OF_PROPERTY_IN_LEAF)

        if file_name in tuple(File.readlines(prop_file)):
            raise WrongPath("Duplicate file")

        with open(prop_file, "at") as file:
            file.write(file_name + "\n")

    def find_path(self, last_bytes_of_file: bytes):
        n_pad = N_BYTES_FOR_IDENTIFYING - len(last_bytes_of_file)
        last_bytes_of_file = b"0" * n_pad + last_bytes_of_file

        paths = [self.__original_directory__]
        current_node = self.__tree__[1]
        for byte in last_bytes_of_file[::-1]:
            if len(current_node) == 0:
                break
            
            part = self.hash_byte(byte)
            for child_node in current_node:
                if part == child_node["name"]:
                    paths.append(child_node["name"])
                    current_node = self.__tree__[child_node["line"]]
                    break
                    
        return os.path.join(*paths)

    def get_nodeidx_from_path(self, path):
        if not hasattr(self, "__original_directory__"):
            raise NotReadInfoYet("Had not used method read() yet")

        paths = split_path(path, stop= self.__original_directory__)
        current_node = self.__tree__[0]
        current_node_idx = 0

        for path in paths:
            found = False
            for child in current_node:
                if path == child["name"]:
                    current_node = self.__tree__[child["line"]]
                    current_node_idx = child["line"]
                    found = True
                    break
            if not found:
                raise WrongPath("Cannot extract this path")

        return current_node_idx

    def reconstruct(self, path):
        node_idx = self.get_nodeidx_from_path(path)

        # Create dir and this's property file
        for i in range(self.__n_splits__):
            full_child_name = os.path.join(path, str(i))
            os.mkdir(full_child_name)

            child_prop_file = os.path.join(full_child_name, NAME_OF_PROPERTY_IN_LEAF)
            open(child_prop_file, "wt").close() # create file
            
            self.__tree__[node_idx].append({"name": str(i), "line": len(self.__tree__)})
            self.__tree__.append([])
        
        # Move all file in this path to its child path
        prop_file = os.path.join(path, NAME_OF_PROPERTY_IN_LEAF)
        for file_name in File.readlines(prop_file):
            file_path = os.path.join(path, file_name)
            last_bytes_of_file = File.get_elements_at_the_end(file_path, N_BYTES_FOR_IDENTIFYING)
            
            new_path = self.find_path(last_bytes_of_file)
            new_file_path = os.path.join(new_path, file_name)

            shutil.move(file_path, new_file_path)
            self.add_file(new_file_path)

        # Remove its property file
        os.remove(prop_file)

class FileStorage(object):
    def __init__(self, directory):
        self.storage_structure = StorageStructure(N_SPLITS)
        self.directory = directory
        if not os.path.isdir(self.directory):
            print("Create dir {}".format(self.directory))
            os.mkdir(self.directory)

        self.__storage_prop_file__ = os.path.join(directory, NAME_OF_PROPERTY_IN_STORAGE)
        if not os.path.isfile(self.__storage_prop_file__):
            print("Create file {}".format(self.__storage_prop_file__))
            StorageStructure.initialize(directory, self.__storage_prop_file__)

            # Empty storage --> root is leaf node
            prop_file = os.path.join(directory, NAME_OF_PROPERTY_IN_LEAF)
            open(prop_file, "wt").close() # Create file

    def create_new_path(self, last_bytes_of_file):
        self.storage_structure.read(self.__storage_prop_file__)
        file_name = str(random.randint(10 ** 20, 10 ** 21 - 1))
        directory = self.storage_structure.find_path(last_bytes_of_file)
        return os.path.join(directory, file_name)

    def save_info(self, path_to_file):
        directory, _ = os.path.split(path_to_file)

        self.storage_structure.read(self.__storage_prop_file__)
        self.storage_structure.add_file(path_to_file)

        prop_file = os.path.join(directory, NAME_OF_PROPERTY_IN_LEAF)
        if len(tuple(File.readlines(prop_file))) >= N_SPLITS:
            self.storage_structure.reconstruct(directory)
        
        self.storage_structure.write(self.__storage_prop_file__)

    def iter(self, last_bytes_of_file):
        self.storage_structure.read(self.__storage_prop_file__)
        directory = self.storage_structure.find_path(last_bytes_of_file)    
        prop_file = os.path.join(directory, NAME_OF_PROPERTY_IN_LEAF)
        add_path = lambda file_name: os.path.join(directory, file_name)
        return map(add_path, File.readlines(prop_file))
            