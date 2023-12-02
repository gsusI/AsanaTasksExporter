import csv
import json
import os
import re
from getpass import getpass
from tqdm import tqdm
import yaml
from cryptography.fernet import Fernet
import asana
import inquirer
import logging

# Function to generate and save an encryption key
def generate_key():
    key = Fernet.generate_key()
    with open('secret.key', 'wb') as key_file:
        key_file.write(key)

# Function to load the saved key
def load_key():
    return open('secret.key', 'rb').read()

# Function to encrypt a message
def encrypt_message(message, key):
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message

# Function to decrypt a message
def decrypt_message(encrypted_message, key):
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)
    return decrypted_message.decode()

# Function to save encrypted API key
def save_api_key(api_key):
    key = load_key()
    encrypted_api_key = encrypt_message(api_key, key)
    with open('api_key.txt', 'wb') as file:
        file.write(encrypted_api_key)

# Function to load and decrypt API key
def load_api_key():
    key = load_key()
    with open('api_key.txt', 'rb') as file:
        encrypted_api_key = file.read()
    return decrypt_message(encrypted_api_key, key)

# Function to combine task details, including subtasks and comments
def combine_task_details(task):
    """ Combine details of a task including subtasks and comments. """
    task_details = client.tasks.find_by_id(task['gid'])
    task_details['subtasks'] = get_all_subtasks(task['gid'])

    comments = client.stories.get_stories_for_task(task['gid'], {'resource_subtype': 'comment'})
    task_details['comments'] = [comment for comment in comments]

    return task_details

# Function to ask for API key decision
def ask_for_api_key_decision():
    if os.path.exists('api_key.txt'):
        use_existing_key = inquirer.prompt([
            inquirer.Confirm('use_existing', message="An API key is already saved. Would you like to use it?", default=True)
        ])['use_existing']

        if use_existing_key:
            return load_api_key()
        else:
            os.remove('api_key.txt')  # Remove the existing key file

    # If no existing key or user chooses not to use it, ask for a new one
    new_api_key = getpass('Enter your Asana API Key: ')
    save_api_key(new_api_key)
    return new_api_key

# Check if encryption key exists, if not, generate one
if not os.path.exists('secret.key'):
    generate_key()

api_key = ask_for_api_key_decision()

# Create Asana client
client = asana.Client.access_token(api_key)
client.headers = {'asana-enable': 'new_user_task_lists'}

# Function to set up logging
def setup_logging(level):
    logging.basicConfig(level=level,
                        format='%(asctime)s - %(levelname)s - %(message)s')

# Prompt for logging verbosity level
verbosity_level = inquirer.prompt([
    inquirer.List('level',
                  message="Select logging verbosity level",
                  choices=['INFO', 'DEBUG', 'WARNING', 'ERROR'],
                  )])['level']

# Set up logging based on user selection
setup_logging(getattr(logging, verbosity_level))

# Continuation of the script focusing on data fetching and exporting functionality
def get_all_subtasks(task_gid):
    """ Retrieve all subtasks recursively for a given task. """
    subtasks = list(client.tasks.subtasks(task_gid))
    for subtask in subtasks:
        subtask['subtasks'] = get_all_subtasks(subtask['gid'])
    return subtasks

def get_project_name(project):
    """ Format project name to be file-system friendly. """
    return re.sub('_+', '_', re.sub('[^0-9a-zA-Z]+', '_', project.lower().replace(' ', '_')))

def export_tasks(all_tasks, format_choice, project_name):
    """ Export tasks to a file in the chosen format. """
    filename = f'asana_tasks_{project_name}.{format_choice.lower()}'
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            if format_choice == 'YAML':
                yaml.dump(all_tasks, file)
            elif format_choice == 'CSV':
                writer = csv.writer(file)
                # Assuming all tasks have the same structure
                headers = all_tasks[0].keys()
                writer.writerow(headers)
                for task in all_tasks:
                    writer.writerow([task.get(key, '') for key in headers])
            elif format_choice == 'JSON':
                json.dump(all_tasks, file, indent=4)
            logging.info(f"Tasks exported successfully to {filename}")
    except Exception as e:
        logging.error(f"Error exporting tasks: {e}")

def main():
    """ Main function to handle user interaction and orchestrate data fetching and exporting. """
    # Set up logging based on user selection
    setup_logging(getattr(logging, verbosity_level))

    # Prompt for output format first
    format_choice = inquirer.prompt([
        inquirer.List('format',
                      message="Select an output format",
                      choices=['YAML', 'CSV', 'JSON'],
                      )])['format']

    # Fetch workspaces and projects
    workspaces = list(client.workspaces.find_all())
    workspace_choice = inquirer.prompt([
        inquirer.List('workspace',
                      message="Select a workspace",
                      choices=[workspace['name'] for workspace in workspaces],
                      )])['workspace']
    selected_workspace = next(workspace for workspace in workspaces if workspace['name'] == workspace_choice)

    projects = list(client.projects.find_by_workspace(selected_workspace['gid']))
    project_choice = inquirer.prompt([
        inquirer.List('project',
                      message="Select a project",
                      choices=[project['name'] for project in projects],
                      )])['project']
    selected_project = next(project for project in projects if project['name'] == project_choice)

    # Fetch tasks and export
    tasks_generator = client.tasks.find_by_project(selected_project['gid'])
    tasks = list(tasks_generator)  # Convert generator to a list

    all_tasks = []

    with tqdm(total=len(tasks), desc="Exporting tasks", unit="task") as pbar:
        for task in tasks:
            all_tasks.append(combine_task_details(task))
            pbar.update(1)  # Update the progress bar for each task processed

    project_name = get_project_name(selected_project['name'])
    export_tasks(all_tasks, format_choice, project_name)

if __name__ == "__main__":
    main()
