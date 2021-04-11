import os
import re
import shutil

from file_storage.util import Util


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
    def _extract_node(node):
        n_childs = int(node[0])
        childs = []

        for i in range(n_childs):
            child = {}
            child["name"] = node[2 * i + 1]
            child["line"] = int(node[2 * i + 2])
            childs.append(child)

        return childs

    def __init__(self,
            directory: str,
            n_splits: int,
            identifier_size: int = 100,
            name_of_leaf_prop_file: int = ".files",
            name_of_root_prop_file: int = ".storage",
            force_reinitilize: bool = False,
        ):
        self._directory = directory
        self._root_name = None

        self._n_splits = n_splits

        self._identifier_size = identifier_size

        self._name_of_leaf_prop_file = name_of_leaf_prop_file
        self._name_of_root_prop_file = name_of_root_prop_file
        self.__tree = None

        self._path_of_root_prop_file = os.path.join(self._directory, self._name_of_root_prop_file)
        if force_reinitilize or os.path.isfile(self._path_of_root_prop_file) is False:
            if force_reinitilize and os.path.isdir(self._directory):
                shutil.rmtree(self._directory)

            if os.path.isdir(self._directory) is False:
                os.mkdir(self._directory)

            root_name = os.path.split(self._directory)[-1]

            with open(self._path_of_root_prop_file, "wt") as file:
                file.write(f"1 {root_name} 1\n")
                file.write(f"0")
            
            prop_file = os.path.join(self._directory, self._name_of_leaf_prop_file)
            open(prop_file, "wt").close()  # create file

    def _hash_byte(self, byte: int):
        return str(byte % self._n_splits)

    def read(self):
        with open(self._path_of_root_prop_file, "rt") as file:
            self.__tree = file.readlines()

        split = lambda s: re.split(r"\s", s)
        self.__tree = map(split, self.__tree)
        self.__tree = list(map(StorageStructure._extract_node, self.__tree))
        
        self._root_name = self.__tree[0][0]["name"]  # also is the root name
        if os.path.split(self._directory)[-1] != self._root_name:
            raise Exception("The initialized directory is different from the read directory")

    def write(self):
        with open(self._path_of_root_prop_file, "wt") as file:
            for node in self.__tree:
                file.write(str(len(node)))
                for child in node:
                    file.write(" " + child["name"])
                    file.write(" " + str(child["line"]))
                file.write("\n")

    def add_file(self, path):
        if os.path.isfile(path) is False:
            raise Exception("File does not exist")

        dir_path, file_name = os.path.split(path)
        node_idx = self.get_node_idx(dir_path)

        if len(self.__tree[node_idx]) != 0:  # if node is not a leaf node
            raise Exception("File cannot be stored at {}".format(dir_path))

        leaf_prop_file = os.path.join(dir_path, self._name_of_leaf_prop_file)

        if file_name in tuple(Util.readlines(leaf_prop_file)):
            raise Exception("Duplicated file")

        with open(leaf_prop_file, "at") as file:
            file.write(file_name + "\n")

    def get_node_directory(self, identifier: bytes):
        n_pad = self._identifier_size - len(identifier)
        identifier = b"0" * n_pad + identifier

        paths = [self._directory]
        current_node = self.__tree[1]
        for current_byte in identifier[::-1]:
            if len(current_node) == 0:
                break
            
            expected_child_node = self._hash_byte(current_byte)

            found = False
            for child_node in current_node:
                if expected_child_node == child_node["name"]:
                    paths.append(child_node["name"])
                    current_node = self.__tree[child_node["line"]]
                    found = True
                    break
            if not found:
                raise Exception("The passed identifier does not match with storage structure")
                    
        return os.path.join(*paths)

    def get_node_idx(self, node_path: str):
        if self._root_name is None:
            raise Exception("Please call read() before calling other methods")

        node_names = Util.split_path(node_path, stop=self._root_name)
        current_node = self.__tree[0]
        current_node_idx = 0

        for i, node_name in enumerate(node_names):
            found = False
            for child in current_node:
                if node_name == child["name"]:
                    current_node = self.__tree[child["line"]]
                    current_node_idx = child["line"]
                    found = True
                    break

            if not found:
                raise Exception("Cannot find the node match with node_path (at level {})".format(i))

        return current_node_idx

    def reconstruct(self, path):
        node_idx = self.get_node_idx(path)

        # Create directories and their property file
        for i in range(self._n_splits):
            subchild_directory = os.path.join(path, str(i))
            os.mkdir(subchild_directory)

            path_of_subchild_leaf_prop_file = os.path.join(subchild_directory, self._name_of_leaf_prop_file)
            open(path_of_subchild_leaf_prop_file, "wt").close() # create file
            
            self.__tree[node_idx].append({"name": str(i), "line": len(self.__tree)})
            self.__tree.append([])
        
        # Move all file in this path to its child path
        path_of_leaf_prop_file = os.path.join(path, self._name_of_leaf_prop_file)
        for file_name in Util.readlines(path_of_leaf_prop_file):
            file_path = os.path.join(path, file_name)
            identifier = Util.get_identifier(file_path, self._identifier_size)
            
            new_directory = self.get_node_directory(identifier)
            new_file_path = os.path.join(new_directory, file_name)

            shutil.move(file_path, new_file_path)
            self.add_file(new_file_path)

        # Remove its property file
        os.remove(path_of_leaf_prop_file)
