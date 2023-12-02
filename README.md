### README.md

# Asana Task Exporter

## Overview
This project is a Python-based tool for fetching and exporting tasks from Asana. It supports various data formats and includes features like API key encryption for enhanced security.

## Features
- Fetch tasks from Asana using API.
- Encrypt and securely store Asana API keys.
- Export tasks in YAML, CSV, or JSON format.
- Recursively fetch subtasks.
- Configurable logging levels.

## Installation
To use this tool, clone the repository and install the required dependencies:

```bash
git clone https://github.com/gsusI/AsanaTasksExporter
cd AsanaTasksExporter
pip install -r requirements.txt
```

## Usage

Run the script to start the interactive process:

```bash
python asana-export.py
```

Follow the on-screen prompts to select your workspace, project, and export format.

## Contributing

Contributions are welcome! Please follow these guidelines:

- Fork the repository and create a new branch.
- Write clear and descriptive commit messages.
- Add comments to your code where necessary.
- Update the README.md with relevant changes.
- Open a pull request with a comprehensive description of changes.

## Security

This tool uses `cryptography` for encryption. Store your `secret.key` and `api_key.txt` securely.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
