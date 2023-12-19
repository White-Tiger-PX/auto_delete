from os.path import exists, basename, join, getmtime
from time import localtime, strftime
from json import load, dump
from os import walk, makedirs


def update_dir_info(current_time, directory_with_scanned_directories, directory_path, directories_data): # Updating data about the contents of directories
    archive_data = {}

    if not(exists(directory_path)):
        return archive_data

    correct_directory_path = directory_path.replace('/', '_').replace(':', '')
    directory_log_path = f"{directory_with_scanned_directories}/{correct_directory_path}.json"

    if exists(directory_log_path):
        try:
            with open(directory_log_path, 'r', encoding = 'UTF-8') as file:
                archive_data = load(file)
        except Exception as err:
            print(err)

    directory_walk(current_time, directory_path, archive_data, directories_data)

    try:
        with open(directory_log_path, 'w+', encoding = 'UTF-8') as file:
            dump(directories_data, file, indent=4)
    except Exception as err:
        print(err)


def directory_walk(current_time, root_directory_path, archive_data, directories_data):
    for directory_path, sub_directories, file_names in walk(root_directory_path):
        try:
            archive_directory_data = archive_data.pop(directory_path)
            archive_directory_data = archive_directory_data['files']
        except Exception:
            archive_directory_data = {}

        directory_data = {
            'name': basename(directory_path),
            'files': {},
            'sub_directories': {}
        }

        update_files_info(current_time, directory_path, file_names, archive_directory_data, directory_data)

        for sub_directory_name in sub_directories:
            sub_directory_path = join(directory_path, sub_directory_name)
            directory_data['sub_directories'][sub_directory_path] = {}

        directories_data[directory_path] = directory_data


def update_files_info(current_time, directory_path, file_names, archive_directory_data, directory_data):
    files_data = {}

    for file_name in file_names:
        file_path = join(directory_path, file_name)

        try:
            archive_file_data = archive_directory_data.pop(file_path)
            file_first_seen_time = archive_file_data['file_first_seen_time']
        except Exception:
            file_first_seen_time = current_time

        try:
            file_modified_time = getmtime(file_path)
        except Exception:
            file_modified_time = current_time

        files_data[file_path] = {
            "name": file_name,
            "file_modified_time": file_modified_time,
            "file_first_seen_time": file_first_seen_time
        }

    directory_data['files'] = files_data


def save_directory(directories_data, directory_path):
    for sub_directory_path in directories_data[directory_path]['sub_directories'].keys():
        save_directory(directories_data, sub_directory_path)

    directories_data[directory_path]['action'] = False
    directories_data[directory_path]['files'] = {}
    directories_data[directory_path]['sub_directories'] = {}


def checking_the_condition_for_action(current_time, path_settings, file_name_exceptions, directory_name_exceptions, directories_data):
    time_limit_for_modified_time = current_time - path_settings['time_limit_for_modified_time']
    time_limit_for_first_seen = current_time - path_settings['time_limit_for_first_seen']
    action_by_last_modified = path_settings['action_by_last_modified']
    action_by_first_seen = path_settings['action_by_first_seen']

    for directory_path, directory_info in directories_data.items():
        if any(directory_name_exception in directory_info['name'] for directory_name_exception in directory_name_exceptions):
            save_directory(directories_data, directory_path)
        else:
            new_files_info = {}

            for file_path, file_info in directory_info['files'].items():
                new_files_info[file_path] = False

                is_file_exception = any(file_name_exception in file_info['name'] for file_name_exception in file_name_exceptions)
                is_modified_time_condition = file_info['file_modified_time'] < time_limit_for_modified_time
                is_first_seen_condition = file_info['file_first_seen_time'] < time_limit_for_first_seen

                if not is_file_exception:
                    if action_by_last_modified and action_by_first_seen and is_modified_time_condition and is_first_seen_condition:
                        new_files_info[file_path] = True
                    elif action_by_last_modified and is_modified_time_condition:
                        new_files_info[file_path] = True
                    elif action_by_first_seen and is_first_seen_condition:
                        new_files_info[file_path] = True

            directories_data[directory_path]['files'] = new_files_info


def save_logs(current_time, path_to_the_logs_folder, program_type, log):
    makedirs(path_to_the_logs_folder, exist_ok=True)

    log_path = join(
        path_to_the_logs_folder,
        f"{program_type}_log {strftime('%Y-%m-%d %H-%M-%S', localtime(current_time))}.json"
    )

    i = 2

    if exists(log_path):
        while exists(log_path):
            log_path = join(
                path_to_the_logs_folder,
                f"{program_type}_log {strftime('%Y-%m-%d %H-%M-%S', localtime(current_time))} - {i}.json"
            )

            i += 1

    try:
        with open(log_path, 'w+', encoding = 'UTF-8') as file:
            dump(log, file, indent = 4)

    except Exception as err:
        print(err)
