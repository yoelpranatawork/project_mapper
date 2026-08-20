import copy
import os
import sys

import yaml


# These are the settings used when setting.yaml does not exist
# or cannot be loaded correctly.
DEFAULT_SETTING = {
    "result_filename": "result.txt",
    "show_log": True,
    "exclude": {
        "folders": [".venv", "venv"],
        "files": [".gitignore", "result.txt"]
    }
}


def read_setting(application_dir):
    # Start with a copy of the default settings.
    #
    # deepcopy() is important here because DEFAULT_SETTING contains
    # dictionaries and lists. A normal copy could cause changes to
    # affect DEFAULT_SETTING itself.
    return_value = copy.deepcopy(DEFAULT_SETTING)
    setting_file_path = os.path.join(application_dir, "setting.yaml")

    is_loaded_from_file = False

    try:
        # This message is shown before we know whether logging
        # is enabled because we need to read the setting first.
        print("Load and read setting file....")

        # "with" automatically closes the file after reading.
        with open(setting_file_path) as stream:
            yaml_dict = yaml.safe_load(stream)

            # safe_load() can return None when the YAML file is empty.
            if yaml_dict is not None:

                # We expect the top-level YAML structure
                # to be a dictionary.
                if isinstance(yaml_dict, dict):
                    # Update the default settings with values
                    # from setting.yaml.
                    #
                    # This means new default settings will still exist
                    # when they are missing from an older setting.yaml.
                    return_value.update(yaml_dict)

                    is_loaded_from_file = True

                    print("Done loading setting file.")

    except Exception:
        # For now, ignore errors and use the default settings.
        #
        # Later, we can make this more specific and show
        # the actual error.
        pass

    # If setting.yaml could not be loaded, create a new one
    # containing the default settings.
    if not is_loaded_from_file:
        with open(setting_file_path, "w") as file:
            yaml.safe_dump(return_value, file)

            print(
                "Setting was loaded with default value "
                "and setting file was rewritten."
            )

    return return_value


def log_message(setting, message):
    # Print the message only when screen logging is enabled.
    if setting["show_log"]:
        print(message)


def sort_dir_contents(content_path):
    # os.path.isfile() tells us whether the path points to a file.
    is_file = os.path.isfile(content_path)

    # lower() makes the alphabetical sorting case-insensitive.
    lower_case = content_path.lower()

    # The tuple is used as the sorting key.
    #
    # (False, "abc") comes before (True, "abc"), so directories
    # are placed before files when sorted normally.
    return (is_file, lower_case)


def read_dir_structure_recursive(setting, working_dir):
    # This function is currently not used.
    #
    # It will eventually contain a recursive version of
    # read_dir_structure_iterative().
    return_value = None

    return return_value


def is_excluded(excluded_folders, excluded_files, dir_item) -> bool:
    # Check whether the current item should be excluded.
    #
    # A folder is excluded when its name is in excluded_folders.
    # A file is excluded when its name is in excluded_files.
    if (
        dir_item.is_file()
        and dir_item.name in excluded_files
    ) or (
        dir_item.is_dir()
        and dir_item.name in excluded_folders
    ):
        return True

    return False


def read_dir_structure_iterative(setting, working_dir):
    return_value = []

    # Convert the exclusion lists into sets.
    #
    # Checking whether something exists in a set is generally
    # faster than checking in a list.
    excluded_folders = set(setting["exclude"]["folders"])
    excluded_files = set(setting["exclude"]["files"])

    # We use a stack to perform the directory traversal.
    #
    # A stack follows LIFO:
    # Last In, First Out.
    stack = [working_dir]

    log_message(setting, "Checking below items:")

    while stack:
        # Remove the last item from the stack.
        current_item = stack.pop()

        log_message(setting, current_item)

        if os.path.isfile(current_item):
            # Store the type together with the path.
            return_value.append(("file", current_item))

        elif os.path.isdir(current_item):
            # Store the directory itself.
            return_value.append(("dir", current_item))

            try:
                # os.scandir() gives us information about the
                # contents of the directory.
                dir_contents = list(os.scandir(current_item))

                # Sort the directory contents.
                #
                # reverse=True is intentional because we are using
                # a stack. The items are pushed in reverse order so
                # that they are later popped in the desired order.
                dir_contents.sort(
                    key=lambda item: sort_dir_contents(item.path),
                    reverse=True
                )

            except PermissionError:
                # Some directories may not be accessible.
                log_message(setting, f"Cannot access {current_item}")

            else:
                for dir_item in dir_contents:

                    # Do not put excluded items onto the stack.
                    if not is_excluded(excluded_folders, excluded_files, dir_item):
                        stack.append(dir_item.path)

    log_message(setting, "")

    return return_value


def read_dir_structure(setting, working_dir):
    # Read the directory structure and return a list containing
    # folders and files.
    #
    # The iterative implementation is currently being used.
    return_value = read_dir_structure_iterative(setting, working_dir)

    # Later, we can switch to the recursive implementation:
    #
    # return_value = read_dir_structure_recursive(setting, working_dir)

    return return_value


def build_tree_string(setting, children, parent_dir, prefix, return_value, root_dir):
    # Get all direct children of the current directory.
    #
    # If the directory has no children, get() returns an empty list.
    parent_children = children.get(parent_dir, [])

    # Go through each child in the existing order.
    for index, (item_type, item_path) in enumerate(parent_children):

        # We need to know whether this is the last child.
        #
        # This determines whether we use:
        #
        #     ├──
        #
        # or:
        #
        #     └──
        is_last = index == len(parent_children) - 1

        if is_last:
            connector = "└── "
        else:
            connector = "├── "

        # Get only the final part of the path.
        #
        # Example:
        #     C:\project\data\file.txt
        #
        # becomes:
        #     file.txt
        base_name = os.path.basename(item_path)

        # Add the indentation/prefix, tree connector,
        # and item name to our result.
        return_value += prefix + connector + base_name + "\n"

        # Calculate how deep this item is below the root directory.
        #
        # os.sep is the path separator for the current OS:
        #
        # Windows -> \
        # Linux   -> /
        #
        # This keeps the calculation OS-independent.
        item_depth = item_path.count(os.sep) - root_dir.count(os.sep)

        log_message(setting, base_name + ", depth: " + str(item_depth))

        # Only directories can have children.
        if item_type == "dir":

            # The prefix for the next level depends on whether
            # the current item was the last child.
            #
            # If it was the last child, there is no vertical line
            # to continue below it:
            #
            #     └── folder
            #         └── file
            #
            # Otherwise, the vertical line continues:
            #
            #     ├── folder
            #     │   └── file
            if is_last:
                child_prefix = prefix + "    "
            else:
                child_prefix = prefix + "│   "

            # Build the tree for this directory's children.
            #
            # This is recursion:
            # build_tree_string() calls itself.
            return_value = build_tree_string(setting, children, item_path, child_prefix, return_value, root_dir)

    return return_value


def format_dir_to_tree_string(setting, dir_structure_data):
    # There is nothing to format if the list is empty.
    if not dir_structure_data:
        return ""

    # The first item is always our root directory.
    root_dir = dir_structure_data[0][1]

    # Build a mapping between a directory and its direct children.
    #
    # For example:
    #
    #     project
    #         -> data
    #         -> main.py
    #
    #     data
    #         -> code1.py
    #         -> file1.txt
    #
    # This makes it easier for build_tree_string() to find
    # the children of each directory.
    children = {}

    for item_type, item_path in dir_structure_data[1:]:

        # Find the directory containing this item.
        #
        # os.path.dirname() is OS-independent.
        parent_dir = os.path.dirname(item_path)

        # If this parent directory hasn't been seen before,
        # create an empty list for its children.
        if parent_dir not in children:
            children[parent_dir] = []

        # Add this item to its parent's children.
        #
        # The existing order is preserved.
        children[parent_dir].append((item_type, item_path))

    log_message(setting, "Walking through directory data to check the depth.")

    # Start the result with the root directory.
    return_value = os.path.basename(root_dir) + "\n"

    # Build the tree starting from the root directory.
    return_value = build_tree_string(setting, children, root_dir, "", return_value, root_dir)

    log_message(setting, "")

    return return_value


def append_file_contents_to_tree_string(setting, dir_structure_data, dir_tree_str, root_dir):
    # Add a separator between the directory tree
    # and the file contents.
    dir_tree_str += "\n"
    dir_tree_str += "=" * 50
    dir_tree_str += "\n"

    # Go through all items in the directory structure.
    #
    # The order is already correct because dir_structure_data
    # was created by read_dir_structure().
    for item_type, item_path in dir_structure_data:

        # We only want to read files.
        if item_type != "file":
            continue

        # Get the path relative to the root directory.
        #
        # The path separator will follow the current OS.
        relative_path = os.path.relpath(item_path, root_dir)

        log_message(setting, f"Reading file: {relative_path}")

        # Add the file name as a heading.
        #
        # The space after "#" makes the heading easier to read.
        dir_tree_str += f"# {relative_path}\n"

        try:
            # Read the file using UTF-8.
            with open(item_path, "r", encoding="utf-8") as file:
                file_content = file.read()

            dir_tree_str += file_content

            # Make sure the next file heading starts
            # on a new line.
            if not file_content.endswith("\n"):
                dir_tree_str += "\n"

            # Add an empty line between files.
            dir_tree_str += "\n"

            log_message(setting, f"Done reading file: {relative_path}")

        except UnicodeDecodeError:
            # The file may not be a UTF-8 text file.
            dir_tree_str += "[Cannot read file as UTF-8]\n\n"

            log_message(setting, f"Cannot read file as UTF-8: {relative_path}")

        except PermissionError:
            # The file exists but cannot be read.
            dir_tree_str += "[Cannot access file]\n\n"

            log_message(setting, f"Cannot access file: {relative_path}")

    return dir_tree_str


def write_dir_structure_tree_to_file(setting, working_dir, dir_tree_str):
    return_value = None

    # Get the result filename from the setting.
    result_filename = setting["result_filename"]

    # Create the full path for the result file.
    #
    # os.path.join() handles the path separator correctly
    # for Windows, Linux, and macOS.
    result_file_path = os.path.join(working_dir, result_filename)

    # Write the directory tree string into the result file.
    #
    # UTF-8 is used because the tree contains Unicode characters
    # such as ├, └, and │.
    with open(result_file_path, "w", encoding="utf-8") as file:
        file.write(dir_tree_str)

    log_message(setting, f"Directory tree was written to: {result_file_path}")

    return_value = result_file_path

    return return_value


def clear_screen():
    # Windows uses "cls".
    #
    # Linux and macOS use "clear".
    #
    # os.name is "nt" on Windows.
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def main():
    # Clear the console in an OS-independent way.
    clear_screen()

    # Find the directory where the application executable is located.
    #
    # When the program has been packaged into an executable,
    # sys.executable points to that executable.
    #
    # Otherwise, __file__ points to this Python source file.
    if getattr(sys, "frozen", False):
        application_dir = os.path.dirname(sys.executable)
    else:
        application_dir = os.path.dirname(os.path.abspath(__file__))

    # This is the current working directory.
    #
    # This is where we want to:
    # - traverse folders and files
    # - create result.txt
    working_dir = os.getcwd()

    # Read the application settings.
    setting = read_setting(application_dir)

    log_message(setting, f"Program directory: {application_dir}")

    # Read the folder/file structure.
    log_message(setting, "Reading directory structure...")

    dir_structure_data = read_dir_structure(setting, working_dir)

    log_message(setting, "Done reading directory structure.")

    # Convert the structure into a tree-shaped string.
    log_message(setting, "Formatting directory tree...")

    dir_tree_str = format_dir_to_tree_string(setting, dir_structure_data)

    log_message(setting, "Done formatting directory tree.")

    # Read the contents of all files and append them
    # to the directory tree string.
    log_message(setting, "Reading file contents...")

    dir_tree_str = append_file_contents_to_tree_string(setting, dir_structure_data, dir_tree_str, working_dir)

    log_message(setting, "Done reading file contents.")

    # Display the resulting tree and file contents.
    log_message(setting, f"Directory tree result:\n{dir_tree_str}")

    # Save the result to the output file.
    result_file_path = write_dir_structure_tree_to_file(setting, working_dir, dir_tree_str)

    print(f"Success! Result was saved to: {result_file_path}")


if __name__ == "__main__":
    main()
