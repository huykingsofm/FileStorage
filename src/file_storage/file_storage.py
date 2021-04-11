import os
import random

from file_storage.util import Util
from file_storage.storage_structure import StorageStructure

class FileStorageException(Exception): ...
class NotReadInfoYet(FileStorageException): ...
class WrongPath(FileStorageException): ...


class FileStorage(object):
    def __init__(self,
            directory: str,
            n_splits: int = 100,
            identifier_size: int = 100,
            name_of_leaf_prop_file: str = ".files",
            name_of_root_prop_file: str = ".storage",
            force_reinitialize: bool = False
        ):

        self._storage_structure = StorageStructure(
            directory=directory,
            n_splits=n_splits,
            identifier_size=identifier_size,
            name_of_leaf_prop_file=name_of_leaf_prop_file,
            name_of_root_prop_file=name_of_root_prop_file,
            force_reinitilize=force_reinitialize
        )
        
        self._directory = directory
        
        self._n_splits = n_splits
        
        self._name_of_leaf_prop_file = name_of_leaf_prop_file
        
        self._name_of_root_prop_file = name_of_root_prop_file
        
        if not os.path.isdir(self._directory):
            print("Create dir {}".format(self._directory))
            os.mkdir(self._directory)

    def create_new_path(self, identifier):
        self._storage_structure.read()
        file_name = str(random.randint(10 ** 20, 10 ** 21 - 1))
        directory = self._storage_structure.get_node_directory(identifier)
        return os.path.join(directory, file_name)

    def save_info(self, file_path):
        directory, _ = os.path.split(file_path)

        self._storage_structure.read()
        self._storage_structure.add_file(file_path)

        leaf_prop_file = os.path.join(directory, self._name_of_leaf_prop_file)
        if len(tuple(Util.readlines(leaf_prop_file))) >= self._n_splits:
            self._storage_structure.reconstruct(directory)

        self._storage_structure.write()

    def iter(self, identifier):
        self._storage_structure.read()
        node_directory = self._storage_structure.get_node_directory(identifier)
        
        leaf_prop_file = os.path.join(node_directory, self._name_of_leaf_prop_file)
        to_full_path = lambda file_name: os.path.join(node_directory, file_name)
        
        for file in map(to_full_path, Util.readlines(leaf_prop_file)):
            if Util.get_identifier(file, len(identifier)) == identifier:
                yield file
