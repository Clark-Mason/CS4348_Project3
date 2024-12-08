import os
import sys
from collections import OrderedDict

# Constants
MAGIC_NUMBER = b'4337PRJ3'
BLOCK_SIZE = 512
MIN_DEGREE = 10
MAX_KEYS = 2 * MIN_DEGREE - 1
MAX_CHILDREN = 2 * MIN_DEGREE

def to_bytes(n):
    return n.to_bytes(8, byteorder='big')

def from_bytes(b):
    return int.from_bytes(b, 'big')

class TreeNode:
    def __init__(self, block_id, parent_node_id=0, key_count=0, keys=None, values=None, children=None):
        self.block_id = block_id
        self.parent_node_id = parent_node_id
        self.key_count = key_count
        self.keys = keys if keys is not None else [0] * MAX_KEYS
        self.values = values if values is not None else [0] * MAX_KEYS
        self.children = children if children is not None else [0] * MAX_CHILDREN

    def is_leaf(self):
        return all(child_id == 0 for child_id in self.children)


class NodeCache:
    def __init__(self, cache_capacity, btree):
        self.cache_capacity = cache_capacity
        self.cache = OrderedDict()
        self.btree = btree

    def get(self, block_id):
        if block_id in self.cache:
            self.cache.move_to_end(block_id)
            return self.cache[block_id]
        node = self.btree.read_node_from_file(block_id)
        self.put(block_id, node)
        return node

    def put(self, block_id, node):
        if block_id in self.cache:
            self.cache.move_to_end(block_id)
        else:
            if len(self.cache) >= self.cache_capacity:
                evicted_block_id, evicted_node = self.cache.popitem(last=False)
                self.btree.write_node_to_file(evicted_node)
        self.cache[block_id] = node

    def clear(self):
        for _, node in self.cache.items():
            self.btree.write_node_to_file(node)
        self.cache.clear()


class BTree:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file = None
        self.root_id = 0
        self.next_block_id = 1
        self.cache = NodeCache(3, self)

    def open_file(self, mode='r+b'):
        try:
            self.file = open(self.file_path, mode)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {self.file_path} does not exist.")

    def close_file(self):
        if self.file:
            self.cache.clear()
            self.file.close()
            self.file = None

    def read_header(self):
        self.file.seek(0)
        data = self.file.read(BLOCK_SIZE)
        if len(data) < BLOCK_SIZE:
            raise ValueError("Invalid header size.")
        if data[:8] != MAGIC_NUMBER:
            raise ValueError("Invalid magic number.")
        self.root_id = from_bytes(data[8:16])
        self.next_block_id = from_bytes(data[16:24])

    def write_header(self):
        self.file.seek(0)
        header = MAGIC_NUMBER + to_bytes(self.root_id) + to_bytes(self.next_block_id)
        header += b'\x00' * (BLOCK_SIZE - len(header))
        self.file.write(header)
        self.file.flush()

    def read_node_from_file(self, block_id):
        self.file.seek(BLOCK_SIZE * block_id)
        data = self.file.read(BLOCK_SIZE)
        if len(data) < BLOCK_SIZE:
            raise ValueError(f"Block {block_id} does not exist.")

        offset = 0
        block_id = from_bytes(data[offset:offset + 8])
        offset += 8
        parent_node_id = from_bytes(data[offset:offset + 8])
        offset += 8
        key_count = from_bytes(data[offset:offset + 8])
        offset += 8

        keys = [from_bytes(data[offset + i*8:offset + (i+1)*8]) for i in range(MAX_KEYS)]
        offset += MAX_KEYS * 8

        values = [from_bytes(data[offset + i*8:offset + (i+1)*8]) for i in range(MAX_KEYS)]
        offset += MAX_KEYS * 8

        children = [from_bytes(data[offset + i*8:offset + (i+1)*8]) for i in range(MAX_CHILDREN)]

        return TreeNode(block_id, parent_node_id, key_count, keys, values, children)

    def write_node_to_file(self, node):
        self.file.seek(BLOCK_SIZE * node.block_id)
        data = to_bytes(node.block_id) + to_bytes(node.parent_node_id) + to_bytes(node.key_count)
        data += b''.join(to_bytes(k) for k in node.keys)
        data += b''.join(to_bytes(v) for v in node.values)
        data += b''.join(to_bytes(c) for c in node.children)
        data += b'\x00' * (BLOCK_SIZE - len(data))
        self.file.write(data)
        self.file.flush()

    def load_btree(self):
        if self.file is None:
            raise ValueError("File is not open.")
        self.cache.clear()
        self.read_header()

    def insert_non_full(self, node, key, value):
        while True:
            i = node.key_count - 1

            if node.is_leaf():
                # Shift keys/values to insert new key/value
                while i >= 0 and key < node.keys[i]:
                    node.keys[i + 1] = node.keys[i]
                    node.values[i + 1] = node.values[i]
                    i -= 1
                node.keys[i + 1] = key
                node.values[i + 1] = value
                node.key_count += 1
                self.cache.put(node.block_id, node)
                return
            else:
                # Move down to the appropriate child
                while i >= 0 and key < node.keys[i]:
                    i -= 1
                i += 1

                if node.children[i] == 0:
                    # Create new child if it doesn't exist
                    new_child = TreeNode(block_id=self.next_block_id, parent_node_id=node.block_id)
                    self.next_block_id += 1
                    self.cache.put(new_child.block_id, new_child)
                    node.children[i] = new_child.block_id
                    self.cache.put(node.block_id, node)
                    child = new_child
                else:
                    child = self.cache.get(node.children[i])

                if child.key_count == MAX_KEYS:
                    self.split_child(node, i, child)
                    # After splitting, the key to insert might go into the new node
                    if key > node.keys[i]:
                        i += 1
                node = self.cache.get(node.children[i])

    def split_child(self, parent, index, child):
        new_child = TreeNode(block_id=self.next_block_id)
        self.next_block_id += 1

        # Move the right half of the child's keys/values to new_child
        new_child.key_count = MIN_DEGREE - 1
        new_child.keys[:MIN_DEGREE - 1] = child.keys[MIN_DEGREE:]
        new_child.values[:MIN_DEGREE - 1] = child.values[MIN_DEGREE:]

        # If not leaf, move children
        if not child.is_leaf():
            new_child.children[:MIN_DEGREE] = child.children[MIN_DEGREE:]

        child.key_count = MIN_DEGREE - 1

        # Insert the new_child into the parent's children and keys/values
        # Using lists for clarity; originally fixed-size arrays are used.
        # We'll just use insert at specific indexes for logic clarity.
        parent.children.insert(index + 1, new_child.block_id)
        parent.keys.insert(index, child.keys[MIN_DEGREE - 1])
        parent.values.insert(index, child.values[MIN_DEGREE - 1])

        parent.key_count += 1

        # Remove extra elements to keep the length consistent (because we're using insert)
        parent.children = parent.children[:MAX_CHILDREN]
        parent.keys = parent.keys[:MAX_KEYS]
        parent.values = parent.values[:MAX_KEYS]

        child.keys[MIN_DEGREE - 1:] = [0]*(MAX_KEYS - (MIN_DEGREE - 1))
        child.values[MIN_DEGREE - 1:] = [0]*(MAX_KEYS - (MIN_DEGREE - 1))
        child.children[MIN_DEGREE:] = [0]*(MAX_CHILDREN - MIN_DEGREE)

        self.cache.put(parent.block_id, parent)
        self.cache.put(child.block_id, child)
        self.cache.put(new_child.block_id, new_child)

    def insert(self, key, value):
        if self.root_id == 0:
            # Tree is empty, create root
            root = TreeNode(block_id=1)
            root.key_count = 1
            root.keys[0] = key
            root.values[0] = value
            self.root_id = root.block_id
            self.cache.put(root.block_id, root)
            self.write_header()
        else:
            root = self.cache.get(self.root_id)
            if root.key_count == MAX_KEYS:
                # Root is full, split it first
                new_root = TreeNode(block_id=self.next_block_id)
                self.next_block_id += 1
                new_root.children[0] = root.block_id
                self.root_id = new_root.block_id
                self.split_child(new_root, 0, root)
                self.write_header()
                self.insert_non_full(new_root, key, value)
            else:
                self.insert_non_full(root, key, value)

    def traverse(self, result):
        def dfs(node):
            for i in range(node.key_count):
                if node.children[i] != 0:
                    dfs(self.cache.get(node.children[i]))
                result.append((node.keys[i], node.values[i]))
            if node.children[node.key_count] != 0:
                dfs(self.cache.get(node.children[node.key_count]))

        if self.root_id != 0:
            root = self.cache.get(self.root_id)
            dfs(root)

    def search_key(self, key):
        def search_node(node):
            i = 0
            while i < node.key_count and key > node.keys[i]:
                i += 1
            if i < node.key_count and key == node.keys[i]:
                return node.values[i]
            elif node.is_leaf():
                return None
            else:
                return search_node(self.cache.get(node.children[i]))

        if self.root_id == 0:
            return None
        root = self.cache.get(self.root_id)
        return search_node(root)

    def print_tree(self):
        def dfs(node):
            if node is None:
                return
            # Print the current node
            key_value_pairs = [(node.keys[i], node.values[i]) for i in range(node.key_count)]
            print(f"Node {node.block_id}: {key_value_pairs}")
            # Recursively print all child nodes
            for child_id in node.children[:node.key_count + 1]:
                if child_id != 0:
                    child = self.cache.get(child_id)
                    dfs(child)

        if self.root_id == 0:
            print("Empty Tree.")
            return

        # Start traversal from the root
        root = self.cache.get(self.root_id)
        dfs(root)

    def extract(self, filename):
        if os.path.exists(filename):
            overwrite = input(f"File {filename} exists. Overwrite? (yes/no): ").strip().lower()
            if overwrite != 'yes':
                print("Operation aborted.")
                return
        result = []
        self.traverse(result)
        with open(filename, 'w') as f:
            for key, value in result:
                f.write(f"{key},{value}\n")
        print(f"Data extracted to {filename}.")

    def load(self, filename):
        if not os.path.exists(filename):
            print(f"File {filename} does not exist.")
            return
        try:
            with open(filename, 'r') as f:
                for line_number, line in enumerate(f, start=1):
                    key_value = line.strip().split(',')
                    if len(key_value) != 2:
                        print(f"Skipping invalid line {line_number}: {line.strip()}")
                        continue
                    key, value = map(int, key_value)
                    self.insert(key, value)
        except ValueError as e:
            print(f"Error reading file {filename}: {e}")


def main():
    index_file = None

    menu = """
    Please choose a command:
    1. Create - Create a new index file
    2. Open   - Open an existing index file
    3. Insert - Insert a key-value pair
    4. Search - Search for a key in the index
    5. Load   - Load key-value pairs from a file
    6. Print  - Print all key-value pairs in the index
    7. Extract- Save all key-value pairs to a file
    8. Quit   - Exit the program
    """

    while True:
        print(menu)
        command = input("Enter your choice (number or command): ").strip().lower()

        if command in {'1', 'create'}:
            filename = input("Enter index file name: ").strip()
            if os.path.exists(filename):
                overwrite = input(f"File '{filename}' exists. Overwrite? (yes/no): ").strip().lower()
                if overwrite != 'yes':
                    print("Operation aborted.")
                    continue
            with open(filename, 'wb') as f:
                f.write(b'\x00' * BLOCK_SIZE)
            index_file = BTree(filename)
            index_file.open_file('r+b')
            index_file.write_header()
            print(f"Created and opened index file '{filename}'.")

        elif command in {'2', 'open'}:
            filename = input("Enter index file name: ").strip()
            try:
                if index_file:
                    index_file.close_file()
                index_file = BTree(filename)
                index_file.open_file()
                index_file.load_btree()
                print(f"Opened and loaded index file '{filename}'.")
            except (FileNotFoundError, ValueError) as e:
                print(e)
                index_file = None

        elif command in {'3', 'insert'}:
            if not index_file:
                print("No index file is open.")
                continue
            try:
                key = int(input("Enter key (unsigned integer): "))
                value = int(input("Enter value (unsigned integer): "))
                if key < 0 or value < 0:
                    raise ValueError
            except ValueError:
                print("Invalid input. Please enter unsigned integers.")
                continue
            index_file.insert(key, value)

        elif command in {'4', 'search'}:
            if not index_file:
                print("No index file is open.")
                continue
            try:
                key = int(input("Enter key (unsigned integer): "))
                if key < 0:
                    raise ValueError
            except ValueError:
                print("Invalid input. Please enter an unsigned integer.")
                continue
            value = index_file.search_key(key)
            if value is not None:
                print(f"Found key {key} with value {value}.")
            else:
                print("Key not found.")

        elif command in {'5', 'load'}:
            if not index_file:
                print("No index file is open.")
                continue
            load_file = input("Enter filename to load data from: ").strip()
            index_file.load(load_file)

        elif command in {'6', 'print'}:
            if not index_file:
                print("No index file is open.")
                continue
            index_file.print_tree()

        elif command in {'7', 'extract'}:
            if not index_file:
                print("No index file is open.")
                continue
            extract_file = input("Enter filename to extract data to: ").strip()
            index_file.extract(extract_file)

        elif command in {'8', 'quit'}:
            print("Exiting program.")
            if index_file:
                index_file.close_file()
            sys.exit()

        else:
            print("Invalid command. Please try again.")

if __name__ == "__main__":
    main()