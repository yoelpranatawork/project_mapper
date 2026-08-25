import copy
import os
import sys

import yaml


# Application name and version.
APPLICATION_NAME = "Project Mapper"
VERSION = "1.0.3"


# These are the settings used when project_mapper_setting.yaml does not exist
# or cannot be loaded correctly.
DEFAULT_SETTING = {
    "result_filename": "result.txt",
    "show_log": False,
    "exclude": {
        "folders": [".venv", "venv", ".git", "dist"],
        "files": [".gitignore", "result.txt", "README.md"],
        "extensions": [".pyc", ".log"]
    }
}

SETTING_FILENAME = "project_mapper_setting.yaml"


def load_setting_file(setting_file_path):
    # Read and parse the setting file.
    #
    # This function is only responsible for loading the YAML file.
    #
    # Validation and repair are handled separately by
    # validate_setting().
    #
    # None is returned when the file cannot be loaded correctly.
    # This allows read_setting() to decide whether all default
    # settings should be used.

    try:
        print("Load and read setting file....")

        # "with" automatically closes the file after reading.
        with open(setting_file_path, encoding="utf-8") as stream:
            yaml_dict = yaml.safe_load(stream)

        # safe_load() returns None when the YAML file is empty.
        #
        # An empty setting file is treated as an empty dictionary,
        # which means optional settings will later be repaired
        # by validate_setting().
        if yaml_dict is None:
            yaml_dict = {}

        # The top-level YAML structure must be a dictionary.
        #
        # A YAML file containing something such as:
        #
        #     - item1
        #     - item2
        #
        # is not a valid project mapper setting structure.
        if not isinstance(yaml_dict, dict):
            raise ValueError("Setting file must contain a dictionary.")

        return yaml_dict

    except (FileNotFoundError, yaml.YAMLError, OSError, ValueError):
        # Return None to tell read_setting() that the setting file
        # could not be loaded correctly.
        return None


def validate_setting(yaml_dict):
    # Start with a copy of the default settings.
    #
    # deepcopy() is important because DEFAULT_SETTING contains
    # dictionaries and lists.
    return_value = copy.deepcopy(DEFAULT_SETTING)

    # This tells read_setting() whether the setting file
    # needs to be rewritten.
    setting_changed = False

    # If the setting file could not be loaded, use all defaults.
    #
    # This case normally does not reach this function because
    # read_setting() handles a None value separately.
    if yaml_dict is None:
        return return_value, setting_changed

    # ------------------------------------------------------------
    # show_log
    # ------------------------------------------------------------

    # show_log is optional.
    #
    # If it is missing or invalid, use the default value.
    if "show_log" not in yaml_dict or not isinstance(yaml_dict["show_log"], bool):
        yaml_dict["show_log"] = DEFAULT_SETTING["show_log"]
        setting_changed = True

    # ------------------------------------------------------------
    # result_filename
    # ------------------------------------------------------------

    # result_filename is optional.
    #
    # If it is missing, invalid, or empty, use the default value.
    if (
        "result_filename" not in yaml_dict
        or not isinstance(yaml_dict["result_filename"], str)
        or not yaml_dict["result_filename"].strip()
    ):
        yaml_dict["result_filename"] = DEFAULT_SETTING["result_filename"]
        setting_changed = True

    # ------------------------------------------------------------
    # exclude
    # ------------------------------------------------------------

    # The exclude section belongs to the user.
    #
    # Each exclude member is validated independently.
    #
    # This is intentional. For example:
    #
    #     exclude:
    #       files:
    #         - .gitignore
    #       folders: invalid-value
    #
    # will preserve files and replace only folders with its
    # default value.
    #
    # Missing members are not added.
    #
    # For example:
    #
    #     exclude:
    #       files:
    #         - .gitignore
    #
    # remains exactly as it is.
    #
    # A completely missing exclude section is also allowed.

    if "exclude" in yaml_dict:

        # The exclude section itself must be a dictionary.
        #
        # If it is malformed, replace only the exclude section
        # with an empty dictionary.
        #
        # We intentionally do not replace it with the complete
        # DEFAULT_SETTING["exclude"] because missing categories
        # should mean that nothing is excluded.
        if not isinstance(yaml_dict["exclude"], dict):
            yaml_dict["exclude"] = {}
            setting_changed = True

        else:
            exclude = yaml_dict["exclude"]

            # ----------------------------------------------------
            # exclude.folders
            # ----------------------------------------------------

            # If folders is missing, leave it missing.
            #
            # If folders exists but is malformed, replace only
            # folders with the default folders.
            #
            # A list is considered structurally valid here.
            # Individual list values are handled later when the
            # exclusion list is normalized for directory traversal.
            if "folders" in exclude:
                if not isinstance(exclude["folders"], list):
                    exclude["folders"] = copy.deepcopy(DEFAULT_SETTING["exclude"]["folders"])
                    setting_changed = True

            # ----------------------------------------------------
            # exclude.files
            # ----------------------------------------------------

            # If files is missing, leave it missing.
            #
            # If files exists but is malformed, replace only
            # files with the default files.
            #
            # A valid list is preserved exactly as provided by
            # the user.
            if "files" in exclude:
                if not isinstance(exclude["files"], list):
                    exclude["files"] = copy.deepcopy(DEFAULT_SETTING["exclude"]["files"])
                    setting_changed = True

            # ----------------------------------------------------
            # exclude.extensions
            # ----------------------------------------------------

            # If extensions is missing, leave it missing.
            #
            # This is important because the user may intentionally
            # want to exclude no extensions.
            #
            # If extensions exists but is malformed, replace only
            # extensions with the default extensions.
            #
            # A valid list is preserved exactly as provided by
            # the user.
            if "extensions" in exclude:
                if not isinstance(exclude["extensions"], list):
                    exclude["extensions"] = copy.deepcopy(DEFAULT_SETTING["exclude"]["extensions"])
                    setting_changed = True

    # Use the validated and repaired settings.
    return_value = yaml_dict

    return return_value, setting_changed


def write_setting_file(setting_file_path, setting):
    # Write the setting dictionary to the YAML file.
    #
    # This function is only responsible for writing the setting file.
    #
    # read_setting() decides whether writing is necessary.

    with open(setting_file_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(setting, file, sort_keys=False)


def read_setting(application_dir):
    # Build the full path to the setting file.
    setting_file_path = os.path.join(application_dir, SETTING_FILENAME)

    # Load the setting file.
    #
    # None means the file does not exist or could not be loaded.
    yaml_dict = load_setting_file(setting_file_path)

    # If the setting file could not be loaded, create a new one
    # using all default settings.
    if yaml_dict is None:
        setting = copy.deepcopy(DEFAULT_SETTING)

        write_setting_file(setting_file_path, setting)

        print("Setting was loaded with default value and setting file was rewritten.")

        return setting

    # Validate and repair the loaded settings.
    #
    # setting_changed tells us whether validation actually changed
    # anything in the setting data.
    setting, setting_changed = validate_setting(yaml_dict)

    # Rewrite the YAML file only when validation changed something.
    #
    # If the setting was already valid, the original file is left
    # completely untouched.
    if setting_changed:
        write_setting_file(setting_file_path, setting)

        print("Setting was repaired and setting file was rewritten.")

    else:
        print("Done loading setting file.")

    return setting


def log_message(setting, message):
    # Print the message only when screen logging is enabled.
    if setting["show_log"]:
        print(message)


def sort_dir_contents(content_path):
    # os.path.isfile() tells us whether the path points to a file.
    #
    # A filesystem error can occur while checking the path.
    # Returning a safe default keeps sorting from terminating
    # the whole application.
    try:
        is_file = os.path.isfile(content_path)

    except OSError:
        is_file = False

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
    #
    # It remains as a placeholder for a future implementation.
    return_value = None

    return return_value


def is_excluded(excluded_folders, excluded_files, excluded_extensions, dir_item, setting):
    # Check whether the current item should be excluded.
    #
    # A folder is excluded when its name is in excluded_folders.
    # A file is excluded when its name is in excluded_files.
    #
    # All names have already been normalized to lowercase.

    try:
        # Normalize the item name once so all comparisons are
        # case-insensitive.
        item_name = dir_item.name.lower()

        # Exclude folders by their exact name.
        if dir_item.is_dir() and item_name in excluded_folders:
            return True

        # Exclude files by their exact name.
        if dir_item.is_file() and item_name in excluded_files:
            return True

        # Exclude files by their extension.
        if dir_item.is_file():
            file_extension = os.path.splitext(item_name)[1]

            if file_extension in excluded_extensions:
                return True

    except OSError as error:
        # The filesystem may no longer allow us to inspect this item.
        #
        # This can happen when a file is deleted, permissions change,
        # or another filesystem problem occurs while scanning.
        log_message(setting, f"Cannot inspect {dir_item.path}: {error}")

        # Returning True means the item will not be added to the
        # traversal stack.
        #
        # Since we cannot safely inspect the item, skipping it is
        # safer than accidentally processing it.
        return True

    return False


def read_dir_structure_iterative(setting, working_dir):
    return_value = []

    # Get the exclude section.
    #
    # If exclude does not exist, use an empty dictionary.
    #
    # This means the following is valid:
    #
    # show_log: false
    # result_filename: result.txt
    #
    # with no exclude section at all.
    exclude = setting.get("exclude") or {}

    # Get the excluded folders.
    #
    # Missing folders or an empty value means nothing is excluded.
    #
    # Names are normalized so, for example:
    #
    #     .GIT
    #
    # is treated the same as:
    #
    #     .git
    excluded_folders = {
        folder.strip().lower()
        for folder in exclude.get("folders", []) or []
        if isinstance(folder, str)
    }

    # Get the excluded files.
    #
    # Names are normalized for case-insensitive comparison.
    excluded_files = {
        file.strip().lower()
        for file in exclude.get("files", []) or []
        if isinstance(file, str)
    }

    # The configured result filename is always excluded.
    #
    # This prevents the generated result file from being read
    # and included in the next project mapping.
    #
    # The user does not need to manually add the result filename
    # to exclude.files.
    result_filename = setting.get("result_filename")

    if isinstance(result_filename, str) and result_filename.strip():
        excluded_files.add(result_filename.strip().lower())

    # Get the excluded extensions.
    #
    # The user can write:
    #
    #     .py
    #
    # or:
    #
    #     py
    #
    # or:
    #
    #     *.py
    #
    # They all become:
    #
    #     .py
    excluded_extensions = set()

    for extension in exclude.get("extensions", []) or []:
        if not isinstance(extension, str):
            continue

        extension = extension.strip().lower()

        if extension.startswith("*"):
            extension = extension[1:]

        if not extension.startswith("."):
            extension = "." + extension

        excluded_extensions.add(extension)

    # We use a stack to perform the directory traversal.
    #
    # A stack follows LIFO:
    # Last In, First Out.
    #
    # The iterative approach avoids using Python's call stack for
    # directory traversal, which is useful when a project contains
    # many nested directories.
    stack = [working_dir]

    log_message(setting, "Checking below items:")

    while stack:
        # Remove the last item from the stack.
        current_item = stack.pop()

        log_message(setting, current_item)

        # Check whether the current item is a file.
        #
        # os.path.isfile() can raise filesystem-related errors
        # in some situations, so handle them explicitly.
        try:
            current_is_file = os.path.isfile(current_item)

        except OSError as error:
            log_message(setting, f"Cannot inspect {current_item}: {error}")
            continue

        if current_is_file:
            # Store the type together with the path.
            return_value.append(("file", current_item))

            continue

        # Check whether the current item is a directory.
        #
        # This is kept separate from the file check so a filesystem
        # problem can be handled without terminating traversal.
        try:
            current_is_dir = os.path.isdir(current_item)

        except OSError as error:
            log_message(setting, f"Cannot inspect {current_item}: {error}")
            continue

        if current_is_dir:
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
                dir_contents.sort(key=lambda item: sort_dir_contents(item.path), reverse=True)

            except PermissionError:
                # Some directories may not be accessible.
                log_message(setting, f"Cannot access {current_item}")

            except OSError as error:
                # Other filesystem errors should not terminate the
                # entire traversal.
                log_message(setting, f"Cannot read directory {current_item}: {error}")

            else:
                for dir_item in dir_contents:

                    # Do not put excluded items onto the stack.
                    #
                    # If the item cannot be inspected, is_excluded()
                    # will skip it and log the filesystem error.
                    if not is_excluded(excluded_folders, excluded_files, excluded_extensions, dir_item, setting):
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

        # item_depth is currently used only for logging.
        #
        # It provides a simple visual check of the calculated
        # directory depth when show_log is enabled.
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
            #
            # This application is currently intended to consolidate
            # source code and text files for use with AI tools.
            # UTF-8 is therefore the expected text encoding.
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
            #
            # At this stage, the application does not attempt to
            # detect other encodings. It records the problem and
            # continues processing the remaining files.
            dir_tree_str += "[Cannot read file as UTF-8]\n\n"

            log_message(setting, f"Cannot read file as UTF-8: {relative_path}")

        except PermissionError:
            # The file exists but cannot be read.
            #
            # Skip this file's contents and continue with the
            # remaining files.
            dir_tree_str += "[Cannot access file]\n\n"

            log_message(setting, f"Cannot access file: {relative_path}")

        except OSError as error:
            # Other filesystem errors should not terminate the
            # entire file-reading process.
            #
            # The specific error is written to the log while the
            # output receives a simple, readable message.
            dir_tree_str += "[Cannot access file]\n\n"

            log_message(setting, f"Cannot read file {relative_path}: {error}")

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


def print_help():
    # Display the command-line help information.
    #
    # Help is handled before the screen is cleared or the setting
    # file is loaded, so it can be used independently of a project.
    print(f"{APPLICATION_NAME}")
    print()
    print("Usage:")
    print(f"  {APPLICATION_NAME.lower().replace(' ', '_')} [OPTIONS]")
    print()
    print("Options:")
    print("  -h, --help       Show this help message and exit.")
    print("  -v, --version    Show the application version and exit.")


def handle_command_line_arguments():
    # Check the command-line arguments before doing any other
    # application work.
    #
    # This means --help and --version do not:
    #
    # - clear the screen
    # - load the setting file
    # - scan the working directory
    # - create the result file
    arguments = sys.argv[1:]

    # Show help information.
    if "-h" in arguments or "--help" in arguments:
        print_help()
        return True

    # Show the application version.
    if "-v" in arguments or "--version" in arguments:
        print(f"{APPLICATION_NAME} {VERSION}")
        return True

    # No recognized command-line option was requested.
    #
    # Returning False tells main() to continue with normal
    # project-mapping behavior.
    return False


def main():
    # Handle command-line options before doing any other work.
    #
    # If the function returns True, the requested command has
    # already been handled and the application can exit normally.
    if handle_command_line_arguments():
        return

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
    # - create the result file
    #
    # The application directory and working directory are
    # intentionally different concepts:
    #
    # application_dir -> where Project Mapper is installed
    # working_dir     -> project being mapped
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
