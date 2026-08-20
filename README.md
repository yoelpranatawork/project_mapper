# project_mapper

A simple Python utility that creates a directory tree and concatenates
the contents of text files into a single result file.

## Features

- Generates a directory tree using tree characters.
- Lists folders before files.
- Sorts folders and files alphabetically.
- Allows folders and files to be excluded.
- Concatenates file contents into the result.
- Configurable output filename.
- Optional screen logging.
- Uses the native path format of the operating system.
- Works on Windows, Linux, and macOS.

## Requirements

- Python 3.x
- PyYAML

## Installation

Install the required Python package:

    pip install pyyaml

## Usage

Run the program with:

    python main.py

The program scans the directory where it is running and generates
a result file according to the settings in `setting.yaml`.

The result contains two sections:

1. The directory tree.
2. The contents of the discovered text files.

For example:

    project_mapper
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
    ├── main2.py.bak
    └── setting.yaml

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

## Configuration

The program uses `setting.yaml` for configuration.

Example:

    result_filename: result.txt

    show_log: true

    exclude:
      folders:
        - .venv
        - venv
      files:
        - .gitignore
        - result.txt

### result_filename

Specifies the name of the generated result file.

Example:

    result_filename: result.txt

### show_log

Controls whether progress information is displayed on the screen.

Set it to `true` to show progress information:

    show_log: true

Set it to `false` to disable progress logging:

    show_log: false

The final success message is still displayed.

### exclude

Specifies folders and files that should not be included in the scan.

Example:

    exclude:
      folders:
        - .venv
        - venv
      files:
        - .gitignore
        - result.txt

## Version

1.0.0
