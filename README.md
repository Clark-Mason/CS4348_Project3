# CS4348_Project3
##Overview
    This program provides an interactive interface to create and manage index files backed by a B-Tree data structure. It allows you to:

    Create a new index file
    Open an existing index file
    Insert key-value pairs
    Search for a specific key
    Load bulk key-value pairs from a file
    Print all key-value pairs in sorted order
    Extract all key-value pairs to a CSV file
    Quit the program
    The B-Tree nodes are stored on disk in a custom binary format. The program ensures that no more than three nodes are in memory at once by using an LRU cache. The tree has a minimum degree of 10, allowing for up to 19 keys per node and 20 children.

##Files and Their Roles
    main.py:
    This is the main Python script containing the entire implementation of the B-Tree index management tool.
    It provides all commands as described in the project requirements, including file handling, B-Tree operations (create, insert, search, load, print, extract), and a command-line menu-driven interface.

    README.md (this file):
    Provides an overview of the program, instructions for running it, and additional notes for the teaching assistant.

##How to Compile/Run the Program
    Environment Requirements:

    Python 3.x
    No external libraries are required beyond the Python standard library.
    Running the Program:

    From the command line, navigate to the directory containing main.py
    Run the program:
    bash
    Copy code
    python3 main.py
    This will start the interactive menu. You can type the number or command corresponding to the desired action:
    create
    open
    insert
    search
    load
    print
    extract
    quit
    Commands Usage:

    create: Prompts for a filename, allows overwrite if it already exists, and creates a new empty B-Tree.
    open: Prompts for a filename. If valid and correct format, loads the existing B-Tree.
    insert: Prompts for a key and value (both unsigned integers), and inserts them into the B-Tree.
    search: Prompts for a key and prints the corresponding value if found, otherwise an error message.
    load: Prompts for a filename containing comma-separated key-value pairs. Loads all valid pairs into the B-Tree.
    print: Prints all key-value pairs stored in the B-Tree in ascending order by key.
    extract: Prompts for a filename and writes all key-value pairs out to a CSV file.
    quit: Exits the program, ensuring all changes are saved and the file is closed.

##Notes for the Teaching Assistant
    Project Context and Challenges: This semester has been exceptionally challenging. The workload included multiple extensive homework assignments and projects from various courses scheduled very close together. Additionally, finals week coincided with due dates for multiple assignments. To compound these difficulties, I caught COVID during the final stretch, which severely disrupted my health, schedule, and ability to stay on top of all tasks simultaneously.

    Despite these setbacks, I’ve done my best to meet the project requirements. Please be aware that some aspects might be less polished than intended due to time and health constraints. Your understanding and patience are greatly appreciated.

