import os
import time
import json
import shutil


def main(settings):
    directory_with_scanned_directories = settings['directory_with_scanned_directories']
    current_time = time.time()

    for path_settings in settings['directories']:
        directory_data = update_dir_info(current_time, directory_with_scanned_directories, path_settings['path'])
        directory_data = checking_the_condition_for_deletion(current_time, path_settings, directory_data)
        deletion(current_time, path_settings, directory_data)


def update_dir_info(current_time, directory_with_scanned_directories, directory_path): # Updating data about the contents of directories
    if not(os.path.exists(directory_path)):
        return {}

    correct_directory_path = directory_path.replace('/', '_').replace(':', '')
    directory_log_path = f"{directory_with_scanned_directories}/{correct_directory_path}.json"

    if os.path.exists(directory_log_path):
        try:
            with open(directory_log_path, 'r', encoding='utf-8') as file:
                archive_data = json.load(file)
        except Exception as err:
            print(err)
            archive_data = {}
    else:
        archive_data = {}

    new_data = directory_walk(current_time, directory_path, archive_data)

    try:
        with open(directory_log_path, 'w+', encoding='utf-8') as file:
            json.dump(new_data, file, indent=4)
    except Exception as err:
        print(err)

    return new_data


def directory_walk(current_time, root_directory_path, archive_data):
    new_data = {}

    for directory_path, sub_directories, file_names in os.walk(root_directory_path):
        try:
            archive_directory_data = archive_data.pop(directory_path)
            archive_directory_data = archive_directory_data['files']
        except Exception:
            archive_directory_data = {}

        new_directory_data = {
            'name': os.path.basename(directory_path),
            'files': {},
            'sub_directories': {}
        }

        new_directory_data['files'] = update_files_info(current_time, directory_path, file_names, archive_directory_data)

        for sub_directory_name in sub_directories:
            sub_directory_path = os.path.join(directory_path, sub_directory_name)
            new_directory_data['sub_directories'][sub_directory_path] = {}

        new_data[directory_path] = new_directory_data

    return new_data


def update_files_info(current_time, directory_path, file_names, archive_directory_data):
    new_files_data = {}

    for file_name in file_names:
        file_path = os.path.join(directory_path, file_name)

        try:
            archive_file_data = archive_directory_data.pop(file_path)
            file_first_seen_time = archive_file_data['file_first_seen_time']
        except Exception:
            file_first_seen_time = current_time

        try:
            file_modified_time = os.path.getmtime(file_path)
        except:
            file_modified_time = current_time

        new_files_data[file_path] = {
            "name": file_name,
            "file_modified_time": file_modified_time,
            "file_first_seen_time": file_first_seen_time
        }

    return new_files_data


def checking_the_condition_for_deletion(current_time, path_settings, directory_data):
    file_name_exceptions = path_settings['file_name_exceptions']
    directory_name_exceptions = path_settings['directory_name_exceptions']
    time_limit_for_modified_time = current_time - path_settings['time_limit_for_modified_time']
    time_limit_for_first_seen = current_time - path_settings['time_limit_for_first_seen']
    delete_by_last_modified = path_settings['delete_by_last_modified']
    delete_by_first_seen = path_settings['delete_by_first_seen']

    for directory_path, directory_info in directory_data.items():
        if any(directory_name_exception in directory_info['name'] for directory_name_exception in directory_name_exceptions):
            directory_data = save_directory(directory_data, directory_path)
        else:

            new_files_info = {}

            for file_path, file_info in directory_info['files'].items():
                new_files_info[file_path] = False

                is_file_exception = any(file_name_exception in file_info['name'] for file_name_exception in file_name_exceptions)
                is_modified_time_condition = file_info['file_modified_time'] < time_limit_for_modified_time
                is_first_seen_condition = file_info['file_first_seen_time'] < time_limit_for_first_seen

                if not is_file_exception:
                    if delete_by_last_modified and delete_by_first_seen and is_modified_time_condition and is_first_seen_condition:
                        new_files_info[file_path] = True
                    elif delete_by_last_modified and is_modified_time_condition:
                        new_files_info[file_path] = True
                    elif delete_by_first_seen and is_first_seen_condition:
                        new_files_info[file_path] = True

            directory_data[directory_path]['files'] = new_files_info

    return directory_data


def save_directory(directory_data, directory_path):
    directory_data[directory_path]['delete'] = False
    directory_data[directory_path]['files'] = {}

    for sub_directory_path in directory_data[directory_path]['sub_directories'].keys():
        directory_data = save_directory(directory_data, sub_directory_path)

    return directory_data


def deletion(current_time, path_settings, directory_data):
    deletion_messages, error_messages = [], []

    if path_settings['delete_entire_folders']:
        deletion_messages, error_messages = deletion_with_entire_folders(path_settings, directory_data)
    else:
        deletion_messages, error_messages = deletion_only_files(directory_data)

    save_logs(current_time, path_settings, deletion_messages, error_messages)


def deletion_with_entire_folders(path_settings, directory_data):
    deletion_messages, error_messages = [], []

    for directory_path in list(directory_data.keys())[::-1]:
        all_sub_directories_delete = all(list(
            directory_data[sub_directory_path]['delete']
            for sub_directory_path in directory_data[directory_path]['sub_directories'].keys()
        ))
        all_file_delete = all(list(directory_data[directory_path]['files'].values()))

        if not('delete' in directory_data[directory_path].keys()):
            directory_data[directory_path]['delete'] = all_sub_directories_delete and all_file_delete

    directory_data[path_settings['path']]['delete'] = False

    for directory_path, directory_info in directory_data.items():
        if directory_info['delete']:
            try:
                shutil.rmtree(directory_path)
                save_directory(directory_data, directory_path)
                message = f"Delete directory {directory_path}"
                deletion_messages.append(message)
                print(message)
            except Exception as error_message:
                error_messages.append(str(error_message))
                print(error_message)

                for file_path, delete_file in directory_info['files'].items():
                    if delete_file:
                        try:
                            os.remove(file_path)
                            message = f"Delete file {file_path}"
                            deletion_messages.append(message)
                            print(message)
                        except Exception as file_error_message:
                            error_messages.append(str(file_error_message))
                            print(file_error_message)
        else:
            for file_path, delete_file in directory_data[directory_path]['files'].items():
                if delete_file:
                    try:
                        os.remove(file_path)
                        message = f"Delete file {file_path}"
                        deletion_messages.append(message)
                        print(message)
                    except Exception as error_message:
                        error_messages.append(str(error_message))
                        print(error_message)

    return deletion_messages, error_messages


def deletion_only_files(directory_data):
    deletion_messages, error_messages = [], []

    for directory_path, directory_info in directory_data.items():
        for file_path, delete_file in directory_info['files'].items():
            if delete_file:
                try:
                    os.remove(file_path)
                    message = f"Delete file {file_path}"
                    deletion_messages.append(message)
                    print(message)
                except Exception as error_message:
                    error_messages.append(str(error_message))
                    print(error_message)

    return deletion_messages, error_messages


def save_logs(current_time, path_settings, deletion_messages, error_messages):
    if deletion_messages:
        if path_settings['saved_deleted_files_info_to_text']:
            save_results_to_files(
                os.path.join(settings['path_to_the_logs_folder'],
                f"automatic_deletion_log {time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(current_time))}.txt"),
                path_settings['path'], deletion_messages
            )

    if error_messages:
        if path_settings['saved_error_message_directory_to_text'] :
            save_results_to_files(
                os.path.join(settings['path_to_the_logs_folder'],
                f"automatic_deletion_error_log {time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(current_time))}.txt"),
                path_settings['path'], error_messages
            )


def save_results_to_files(path, directory_path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'a+', encoding = 'utf-8') as file:
        file.write(os.path.basename(directory_path) + '\n')

        for row in data:
            file.write(row + '\n')

        file.write('\n')


if __name__ == '__main__':
    SETTING_PATH = ''

    with open(SETTING_PATH, 'r', encoding='utf-8') as json_file:
        settings = json.load(json_file)

    main(settings)
