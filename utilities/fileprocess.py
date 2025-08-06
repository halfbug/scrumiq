import os
import shutil
import re
from bs4 import BeautifulSoup

def list_files(directory):
    try:
        # List all entries in the directory
        entries = os.listdir(directory)
        # Filter out directories, keeping only files
        files = [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]
        return files
    except FileNotFoundError:
        print(f"The directory {directory} does not exist.")
        return []
    except PermissionError:
        print(f"Permission denied to access the directory {directory}.")
        return []
def read_files(directory):
    files = list_files(directory)
    file_contents = {}
    for file in files:
        file_path = os.path.join(directory, file)
        try:
            with open(file_path, 'r') as f:
                file_contents[file] = f.read()
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return file_contents
def process_files(directory, callback):
    files = list_files(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            callback(file, content)
        except Exception as e:
            print(f"Error processing {file}: {e}")
def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} deleted successfully.")
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except PermissionError:
        print(f"Permission denied to delete the file {file_path}.")
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")

def upload_file(source_path, destination_directory):
    try:
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory)
        shutil.copy(source_path, destination_directory)
        print(f"File {source_path} uploaded to {destination_directory}.")
    except FileNotFoundError:
        print(f"The source file {source_path} does not exist.")
    except PermissionError:
        print(f"Permission denied to access {source_path} or {destination_directory}.")
    except Exception as e:
        print(f"Error uploading {source_path} to {destination_directory}: {e}")
def upload_multiple_files(source_directory, destination_directory):
    files = list_files(source_directory)
    for file in files:
        source_path = os.path.join(source_directory, file)
        upload_file(source_path, destination_directory)

def get_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Ignore any unwanted error characters when reading the file
            # content = f.read(encoding='utf-8', errors='ignore')
            # Remove HTML tags using a regular expression
            # clean_content = re.sub(r'<[^>]+>', '', content)
            clean_content = filter_html_from_text(content)
            return clean_content
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
        return None
    except PermissionError:
        print(f"Permission denied to access the file {file_path}.")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def filter_html_from_text(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text()
    except Exception as e:
        print(f"Error filtering HTML: {e}")
        return None

def filter_html_and_save(file_path):
    try:
        with open(file_path, 'r+', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            clean_content = filter_html_from_text(content)
            # print("clean_content",clean_content)
            f.seek(0)
            f.write(clean_content)
            f.truncate()
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except PermissionError:
        print(f"Permission denied to access the file {file_path}.")
    except Exception as e:
        print(f"Error filtering HTML and saving {file_path}: {e}")
