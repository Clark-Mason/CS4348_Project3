from index_file import IndexFile

class GUI:
    def __init__(self):
        self.index_file = None
        self.is_running = True

    def run(self):
        while self.is_running:
            self.print_menu()
            command = input("Enter command: ").strip().lower()
            self.handle_command(command)

    def print_menu(self):
        print("\nMenu:")
        print("1. create - Create a new index file")
        print("2. open - Open an existing index file")
        print("3. quit - Exit the program")

    def handle_command(self, command):
        if command in {"create", "1"}:
            self.create_file()
        elif command in {"open", "2"}:
            self.open_file()
        elif command in {"quit", "3"}:
            self.quit_program()
        else:
            print("Invalid command. Please try again.")

    def create_file(self):
        file_path = input("Enter the file name to create: ").strip()
        try:
            self.index_file = IndexFile()
            self.index_file.create_index_file(file_path)
            print(f"File {file_path} created successfully.")
        except Exception as e:
            print(f"Error creating file: {e}")

    def open_file(self):
        file_path = input("Enter the file name to open: ").strip()
        try:
            self.index_file = IndexFile()
            self.index_file.open_index_file(file_path)
            print(f"File {file_path} opened successfully.")
        except Exception as e:
            print(f"Error opening file: {e}")

    def quit_program(self):
        if self.index_file:
            self.index_file.close()
        self.is_running = False
        print("Quitting Program")

if __name__ == "__main__":
    gui = GUI()
    gui.run()
