# project_mapper

A simple Python utility that creates a directory tree and concatenates
the contents of text files into a single result file.

## Features

- Generates a directory tree using tree characters.
- Lists folders before files.
- Sorts folders and files alphabetically.
- Allows folders, files, and file extensions to be excluded.
- Supports optional exclusion categories.
- Automatically excludes the configured result file.
- Concatenates file contents into the result.
- Configurable output filename.
- Optional screen logging.
- Uses the native path format of the operating system.
- Works on Windows, Linux, and macOS.
- Supports `--help` and `--version` command-line options.
- Can be compiled into a standalone executable.
- Can be run from any working directory.

## Requirements

### Running from Python source

- Python 3.x
- PyYAML

### Running the executable

No Python installation is required.

## Installation

### Python source

Install the required Python package:

    pip install pyyaml

### Standalone executable

A pre-built Windows executable can be downloaded from the
GitHub Releases page.

The release contains only the standalone `.exe` file.
The configuration YAML file does not need to be downloaded separately.

The executable is a single `.exe` file and does not require Python
or PyYAML to be installed.

## Usage

### Python source

Run the program with:

    python main.py

### Executable

Run the executable from any directory:

    project_mapper.exe

For example, if `project_mapper.exe` is available on the system PATH,
you can simply run:

    project_mapper

The program scans the current working directory and generates
a result file according to the settings in
`project_mapper_setting.yaml`.

### Command-line options

Display the help information:

    project_mapper --help

or:

    project_mapper -h

Display the application version:

    project_mapper --version

or:

    project_mapper -v

The version option displays the application name and version without
loading the settings or scanning the working directory.

## Working Directory and Application Directory

The program uses two different directories.

### Working directory

The working directory is the directory from which the program is launched.

This directory is used for:

- Traversing folders and files.
- Creating the result file.

For example, if you run:

    D:\Projects\MyProject> project_mapper

then `D:\Projects\MyProject` is the working directory.

The directory tree and file contents are based on this directory.

### Application directory

The application directory is the directory containing the executable.

This directory is used for:

- Reading `project_mapper_setting.yaml`.
- Creating `project_mapper_setting.yaml` if it does not exist.

For example, if the executable is located at:

    C:\Tools\project_mapper\project_mapper.exe

then:

    C:\Tools\project_mapper

is the application directory.

This separation allows `project_mapper.exe` to be placed on the system PATH
and used to scan different projects without copying the executable into
each project.

## Important: project_mapper_setting.yaml

`project_mapper_setting.yaml` belongs to the application directory, not the
working directory.

For example:

    C:\Tools\project_mapper\
    └── project_mapper.exe

On the first normal run, the program automatically creates:

    C:\Tools\project_mapper\project_mapper_setting.yaml

using the default settings.

Therefore, the configuration YAML file does not need to be included
with the executable when downloading a GitHub Release.

After the first run, you can edit the generated
`project_mapper_setting.yaml` file to customize the application.

If the executable is copied to another directory, a new
`project_mapper_setting.yaml` will be created there automatically
on the first normal run.

## Output

The result file is created in the working directory.

For example:

    D:\Projects\MyProject> project_mapper

The result will be created as:

    D:\Projects\MyProject\result.txt

The result contains two sections:

1. The directory tree.
2. The contents of the discovered text files.

For example:

    MyProject
    ├── data
    │   ├── code1.py
    │   └── file1.txt
    ├── library
    ├── old
    │   └── java
    │       └── test.java
    ├── main.py
    ├── main.py.bak
    ├── main2.py
    └── main2.py.bak

    ==================================================

    # data\code1.py
    ...
    ...
    ...

    # data\file1.txt
    ...
    ...
    ...

    # old\java\test.java
    ...
    ...
    ...

The path separator shown in the result follows the operating system.
For example, Windows uses `\`, while Linux and macOS use `/`.

The configured result filename is automatically excluded from the scan.
This prevents the generated result file from being included in the next
project mapping.

## Configuration

The program uses `project_mapper_setting.yaml` for configuration.

Example:

    result_filename: result.txt

    show_log: true

    exclude:
      folders:
        - .venv
        - venv
      files:
        - .gitignore
        - README.md
      extensions:
        - .pyc
        - .log

The configuration file is created automatically with default values
if it does not exist or cannot be loaded correctly.

### result_filename

Specifies the name of the generated result file.

Example:

    result_filename: result.txt

The result file is always created in the working directory.

The configured result filename is automatically excluded from the scan.
It does not need to be added manually to `exclude.files`.

If `result_filename` is missing, invalid, or empty, the default value
is automatically used:

    result.txt

### show_log

Controls whether progress information is displayed on the screen.

Set it to `true` to show progress information:

    show_log: true

Set it to `false` to disable progress logging:

    show_log: false

If `show_log` is missing or invalid, the default value is automatically
used:

    false

The final success message is still displayed.

### exclude

Specifies folders, files, and file extensions that should not be
included in the scan.

The `exclude` section is optional.

Each child of `exclude` is also optional:

- `folders`
- `files`
- `extensions`

Missing exclude categories mean that nothing is excluded for that
category.

The entire `exclude` section can also be omitted.

For example, this is valid:

    result_filename: result.txt
    show_log: false

In this case, no additional folders, files, or extensions are excluded.

### Excluded folders

Folders can be excluded by their exact folder name.

Example:

    exclude:
      folders:
        - .venv
        - venv
        - .git

Excluded folders are skipped entirely, including all of their contents.

Folder names are compared case-insensitively.

### Excluded files

Files can be excluded by their exact file name.

Example:

    exclude:
      files:
        - .gitignore
        - README.md

Excluded files are not included in the directory tree or file contents.

The configured `result_filename` is automatically excluded even when
it is not listed here.

File names are compared case-insensitively.

### Excluded extensions

Files can be excluded by their file extension.

Example:

    exclude:
      extensions:
        - .pyc
        - .log

Extensions can be written in several forms.

For example:

    .py

    py

    *.py

All of these forms are normalized and treated as:

    .py

Extension comparisons are case-insensitive.

### Combining exclude categories

The exclude categories can be used independently or together.

For example:

    exclude:
      folders:
        - .git
      files:
        - .gitignore
      extensions:
        - .pyc
        - .log

Only the categories specified by the user are applied.

For example:

    exclude:
      folders:
        - .git

In this case, only `.git` folders are excluded.

No additional files or extensions are excluded.

## Setting Validation and Repair

The program validates the contents of
`project_mapper_setting.yaml` when it is loaded.

If a setting is missing or invalid, the program uses the appropriate
default value and repairs the configuration file when necessary.

For example, an invalid `show_log` value is replaced with:

    show_log: false

An invalid `result_filename` is replaced with:

    result_filename: result.txt

The `exclude` categories are validated independently.

This means an invalid category does not automatically replace the
other valid categories.

For example:

    exclude:
      files:
        - .gitignore
      folders: invalid-value

The valid `files` configuration is preserved while `folders` is repaired.

## Example: Using the Executable on Multiple Projects

Assume the executable is installed in:

    C:\Tools\project_mapper\project_mapper.exe

and this directory is available through the system PATH.

You can then run:

    D:\Projects\ProjectA> project_mapper

and:

    D:\Projects\ProjectB> project_mapper

The same executable and application configuration are used for both
projects.

The output is created separately in each working directory:

    D:\Projects\ProjectA\result.txt
    D:\Projects\ProjectB\result.txt

## Building the Executable

The executable can be built using PyInstaller.

Install PyInstaller:

    python -m pip install pyinstaller

Build a single executable:

    python -m PyInstaller --clean --onefile --name project_mapper main.py

The resulting executable will be created at:

    dist\project_mapper.exe

The `--onefile` option creates a single executable instead of a directory
containing the executable and supporting files.

The generated executable does not contain
`project_mapper_setting.yaml`. The configuration file is created
automatically in the application directory when the executable is
first run normally.

## GitHub Release

Stable versions are published as GitHub Releases.

The current stable version is:

    v1.0.3

The standalone Windows executable can be attached to the corresponding
GitHub Release.

Only the executable needs to be included in the release.

The configuration file is created automatically when the executable
is run for the first time.

## Version

1.0.3
