from shutil import rmtree
from time import time
from os import remove
from common_functions import *


def main(settings):
    directory_with_scanned_directories = settings['directory_with_scanned_directories']
    path_to_the_logs_folder = settings['path_to_the_logs_folder']
    logs = []

    for path_settings in settings['directories']:
        if exists(path_settings['path']):
            current_time = time()
            file_name_exceptions = path_settings['file_name_exceptions']
            directory_name_exceptions = path_settings['directory_name_exceptions']

            directories_data = {}
            log = {
                "path": path_settings['path'],
                "deletion_messages": [],
                "error_messages": []
            }

            update_dir_info(current_time, directory_with_scanned_directories, path_settings['path'], directories_data)
            checking_the_condition_for_action(current_time, path_settings, file_name_exceptions, directory_name_exceptions, directories_data)

            if path_settings['delete_entire_folders']:
                deletion_with_entire_folders(path_settings, directories_data, log)
            else:
                deletion_only_files(directories_data, log)

            if path_settings['save_logs']:
                if log['deletion_messages'] or log['error_messages']:
                    if not log['deletion_messages']:
                        del log['deletion_messages']

                    if not log['error_messages']:
                        del log['error_messages']

                    logs.append(log)

    if logs:
        save_logs(current_time, path_to_the_logs_folder, 'auto_delete', logs)


def deletion_with_entire_folders(path_settings, directories_data, log):
    for directory_path in list(directories_data.keys())[::-1]:
        all_sub_directories_delete = all(list(directories_data[sub_directory_path]['action'] for sub_directory_path in directories_data[directory_path]['sub_directories'].keys()))
        all_file_delete = all(list(directories_data[directory_path]['files'].values()))

        if not('action' in directories_data[directory_path].keys()):
            directories_data[directory_path]['action'] = all_sub_directories_delete and all_file_delete


    directories_data[path_settings['path']]['action'] = False

    for directory_path, directory_info in directories_data.items():
        if directory_info['action']:
            try:
                rmtree(directory_path)
                save_directory(directories_data, directory_path)
                print(f"Delete directory {directory_path}")
                message = {"path": directory_path, "type": "directory"}
                log['deletion_messages'].append(message)
            except Exception as error:
                print(error)
                message = {"path": directory_path, "type": "directory", "error": str(error)}
                log['error_messages'].append(message)

                delete_files(directory_info, log)
        else:
            delete_files(directory_info, log)


def deletion_only_files(directories_data, log):
    for directory_path, directory_info in directories_data.items():
        delete_files(directory_info, log)


def delete_files(directory_info, log):
    for file_path, delete_file in directory_info['files'].items():
        if delete_file:
            try:
                remove(file_path)
                print(f"Delete file {file_path}")
                message = {"path": file_path, "type": "file"}
                log['deletion_messages'].append(message)
            except Exception as error:
                print(error)
                message = {"path": file_path, "type": "file", "error": str(error)}
                log['error_messages'].append(message)


SETTING_PATH = 'auto_delete_settings.json'

with open(SETTING_PATH, 'r', encoding = 'UTF-8') as json_file:
    settings = load(json_file)

main(settings)
