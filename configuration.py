"""
configuration.py
Author: Michael Pagliaro
A file to handle saving, loading, and the handling at runtime of configurations of files to backup and
their destinations.
"""

import os
import pickle
import util

# Static global variable for the name of the directory configs are saved to
CONFIG_DIRECTORY = "configs"


class Configuration:
    """
    Class for representing configurations. This holds data for which folders to backup and where
    to back them up to.
    """
    name = ""
    inputs = []
    outputs = []
    exclusions = []

    def __init__(self):
        """
        Create the Configuration object.
        """
        self.name = ""
        self.inputs = []
        self.outputs = []
        self.exclusions = []

    def force_update(self):
        """
        If any of the fields in the configuration doesn't exist, set it to a default value. This is useful
        when making configurations in one version of this script, but then it updates and a few field gets
        added. This will prevent any crashes by making sure any unused fields always have a default value.
        """
        if self.name is None:
            self.name = ""
        if self.inputs is None:
            self.inputs = []
        if self.outputs is None:
            self.outputs = []
        if self.exclusions is None:
            self.exclusions = []

    def new_entry(self, input_path):
        """
        Create a new entry in the configuration. This will add the given path as a new input and
        create a corresponding empty list of destinations.
        :param input_path: The path to a folder or file to backup.
        """
        self.inputs.append(input_path)
        self.outputs.append([])
        self.exclusions.append([])

    def new_destination(self, entry_number, output_path):
        """
        Append a new destination path to an entry.
        :param entry_number: The number of the index of the entry, starting at 1.
        :param output_path: The path to the folder where this entry should be backed up to.
        """
        self.outputs[entry_number-1].append(output_path)

    def new_exclusion(self, input_number, exclusion_type, exclusion_text):
        """
        Append a new exclusion to an entry.
        :param input_number: The number of the index of the entry, starting at 1.
        :param exclusion_type: The type of exclusion, defined in the should_exclude() function.
        :param exclusion_text: The text to exclude.
        """
        self.exclusions[input_number-1].append([exclusion_type, exclusion_text])

    def edit_entry_name(self, input_number, new_name):
        """
        Change the name of one of the inputs.
        :param input_number: The number of the index of the entry, starting at 1.
        :param new_name: The name to change it to.
        """
        self.inputs[input_number-1] = new_name

    def edit_destination(self, input_number, dest_number, new_name):
        """
        Change the name of a specified destination.
        :param input_number: The number of the index of the entry, starting at 1.
        :param dest_number: The number of the index of a destination for this entry, starting at 1.
        :param new_name: The name to change it to.
        """
        self.outputs[input_number-1][dest_number-1] = new_name

    def edit_exclusion(self, input_number, excl_number, new_name):
        """
        Change the data of a specified exclusion.
        :param input_number: The number of the index of the entry, starting at 1.
        :param excl_number: The number of the index of an exclusion for this entry, starting at 1.
        :param new_name: The data to change it to.
        """
        self.exclusions[input_number-1][excl_number-1][1] = new_name

    def entry_exists(self, input_path):
        """
        Checks if a given input path already exists in the configuration.
        :param input_path: The path to a folder or file to backup.
        :return: True if it already exists, false otherwise.
        """
        return input_path in self.inputs

    def output_exists_for_entry(self, input_number, output_path):
        """
        Checks if a given output path already exists in the list of outputs for an entry.
        :param input_number: The number of the index of the entry, starting at 1.
        :param output_path: The path to the folder where this entry should be backed up to.
        :return: True if it already exists for the given entry number, false otherwise.
        """
        return output_path in self.outputs[input_number-1]

    def all_entries_have_outputs(self):
        """
        Checks if all entries in the configuration have at least one output specified.
        :return: True if all entries have at least one destination, false otherwise.
        """
        for destination_list in self.outputs:
            if len(destination_list) == 0:
                return False
        return True

    def all_paths_are_valid(self):
        """
        Checks if any input or output path in this configuration is not valid.
        :return: True if every path is valid, false otherwise.
        """
        for input_path in self.inputs:
            if not os.path.exists(input_path):
                return False
        for output_list in self.outputs:
            for output_path in output_list:
                if not os.path.exists(output_path):
                    return False
        return True

    def get_input(self, input_number):
        """
        Given an index number, get the corresponding input path.
        :param input_number: The number of the index of the entry, starting at 1.
        :return: The path of the corresponding input path.
        """
        return self.inputs[input_number-1]

    def get_destinations(self, input_number):
        """
        Given an index number, get the corresponding destination paths.
        :param input_number: The number of the index of the entry, starting at 1.
        :return: A list of paths to this entry's destinations.
        """
        return self.outputs[input_number-1]

    def get_entries(self):
        """
        Get a list of entries, where each entry is a sublist where the first element is an
        input and the second element is a list of its corresponding outputs.
        :return: A zipped list of inputs and outputs.
        """
        return zip(self.inputs, self.outputs)

    def get_exclusions(self, input_number):
        """
        Get a list of exclusions for a given entry. Each exclusion in the list has its first element
        as a type of exclusion, then the second is the exclusion data.
        :param input_number: The number of the index of the entry, starting at 1.
        :return: A list of exclusions for this entry.
        """
        return self.exclusions[input_number-1]

    def get_name(self):
        """
        Get the name of this configuration.
        :return: This configuration's name as a string.
        """
        return self.name

    def set_name(self, new_name):
        """
        Set the name for this configuration.
        :param new_name: This configuration's new name as a string.
        """
        self.name = new_name

    def enumerate_entries(self):
        """
        Iterate through each input/outputs entry in this configuration and display them to the
        screen, prefaced by numbers.
        """
        for entry_idx in range(len(self.inputs)):
            print("{}: {} --> {}".format(entry_idx+1, self.inputs[entry_idx], self.outputs[entry_idx]))

    def enumerate_destinations(self, input_number):
        """
        Iterate through each destination of a given input and display them alongside numbers.
        :param input_number: The number of the index of the entry, starting at 1.
        """
        for dest_idx in range(len(self.outputs[input_number-1])):
            print("{}: {}".format(dest_idx+1, self.outputs[input_number-1][dest_idx]))

    def enumerate_exclusions(self, input_number):
        """
        Iterate through each exclusion of a given input and display them alongside numbers.
        :param input_number: The number of the index of the entry, starting at 1.
        """
        for excl_idx in range(len(self.exclusions[input_number-1])):
            print("{}: {} \"{}\"".format(excl_idx+1, self.exclusions[input_number-1][excl_idx][0],
                                         self.exclusions[input_number-1][excl_idx][1]))

    def entry_to_string(self, input_number, exclusion_mode=False):
        """
        Create a formatted string for a given entry, containing the input path and all its destination paths.
        :param input_number: The number of the index of the entry, starting at 1.
        :param exclusion_mode: True to display exclusions instead of destinations. False by default.
        :return: A string containing all necessary information about an entry.
        """
        entry_str = "INPUT: {}\n".format(self.inputs[input_number-1])
        if exclusion_mode:
            for exclusion in self.exclusions[input_number-1]:
                entry_str += "\tEXCLUSION: {} \"{}\"\n".format(exclusion[0], exclusion[1])
        else:
            for destination in self.outputs[input_number-1]:
                entry_str += "\tDESTINATION: {}\n".format(destination)
        return entry_str.strip()

    def num_entries(self):
        """
        Get the number of input/outputs entries this configuration is holding.
        :return: The number of entries.
        """
        return len(self.inputs)

    def num_destinations(self, input_number):
        """
        Get the number of destinations for a given entry in the configuration.
        :param input_number: The number of the index of the entry, starting at 1.
        :return: The number of destinations for that entry.
        """
        return len(self.outputs[input_number-1])

    def num_exclusions(self, input_number):
        """
        Get the number of exclusions for a given entry in the configuration.
        :param input_number: The number of the index of the entry, starting at 1.
        :return: The number of exclusions for that entry.
        """
        return len(self.exclusions[input_number-1])

    def delete_destination(self, input_number, destination_number):
        """
        Delete one destination path from a given entry.
        :param input_number: The number of the index of the entry, starting at 1.
        :param destination_number: The number of the index of the destination in that entry,
                                   starting at 1.
        """
        del self.outputs[input_number-1][destination_number-1]

    def delete_destinations(self, input_number):
        """
        Delete all the destination paths of a given input.
        :param input_number: The number of the index of the entry, starting at 1.
        """
        self.outputs[input_number-1] = []

    def delete_exclusion(self, input_number, exclusion_number):
        """
        Delete one exclusion from a given entry.
        :param input_number: The number of the index of the entry, starting at 1.
        :param exclusion_number: The number of the index of the exclusion in that entry,
                                 starting at 1.
        """
        del self.exclusions[input_number-1][exclusion_number-1]

    def delete_exclusions(self, input_number):
        """
        Delete all the exclusion entries of a given input.
        :param input_number: The number of the index of the entry, starting at 1.
        """
        self.exclusions[input_number-1] = []

    def delete_entry(self, input_number):
        """
        Delete an entry from the configuration. This removes its input path and all corresponding
        destination paths.
        :param input_number: The number of the index of the entry, starting at 1.
        """
        del self.inputs[input_number-1]
        del self.outputs[input_number-1]

    def should_exclude(self, input_number, path_to_exclude):
        """
        Checks if a given file path should be excluded, based on this entry's exclusions.
        :param input_number: The number of the index of the entry, starting at 1.
        :param path_to_exclude: A file path to a folder or file to check if it should be excluded.
        :return: True if this folder/file should be excluded, false otherwise.
        """
        for exclusion in self.exclusions[input_number-1]:
            if exclusion[0] == "startswith":
                if os.path.splitext(os.path.split(path_to_exclude)[1])[0].startswith(exclusion[1]):
                    if len(exclusion) == 3:
                        if util.path_is_in_directory(path_to_exclude, exclusion[2]):
                            return True
                    else:
                        return True
            elif exclusion[0] == "endswith":
                if os.path.splitext(os.path.split(path_to_exclude)[1])[0].endswith(exclusion[1]):
                    if len(exclusion) == 3:
                        if util.path_is_in_directory(path_to_exclude, exclusion[2]):
                            return True
                    else:
                        return True
            elif exclusion[0] == "ext":
                if os.path.splitext(path_to_exclude)[1] == exclusion[1]:
                    if len(exclusion) == 3:
                        if util.path_is_in_directory(path_to_exclude, exclusion[2]):
                            return True
                    else:
                        return True
            elif exclusion[0] == "directory":
                if os.path.realpath(path_to_exclude) == os.path.realpath(exclusion[1]):
                    return True
        return False

    def equals(self, other_config):
        """
        Check if this configuration is equal to another. For them to be equal, every field needs to be
        identical.
        :param other_config: A configuration to check if it's equal to this one.
        :return: True if they are equal, false otherwise.
        """
        if not isinstance(other_config, Configuration):
            return False
        # The names must be equal
        if not self.name == other_config.name:
            return False
        # They must have the same number of entries
        if not len(self.inputs) == len(other_config.inputs):
            return False
        for entry_idx in range(len(self.inputs)):
            # For this entry, the number of outputs and exclusions must be the same
            if not len(self.outputs[entry_idx]) == len(other_config.outputs[entry_idx]) or \
                    not len(self.exclusions[entry_idx]) == len(other_config.exclusions[entry_idx]):
                return False
            # For this entry, every output must be the same
            for output_idx in range(len(self.outputs[entry_idx])):
                if not self.outputs[entry_idx][output_idx] == other_config.outputs[entry_idx][output_idx]:
                    return False
            for excl_idx in range(len(self.exclusions[entry_idx])):
                # For this exclusion, the lengths of them must be equal
                if not len(self.exclusions[entry_idx][excl_idx]) == len(other_config.exclusions[entry_idx][excl_idx]):
                    return False
                # Each bit of data in the exclusions must be identical
                for data_idx in range(len(self.exclusions[entry_idx][excl_idx])):
                    if not self.exclusions[entry_idx][excl_idx][data_idx] == \
                           other_config.exclusions[entry_idx][excl_idx][data_idx]:
                        return False
        return True


def config_exists(config_name):
    """
    Checks the saved configuration folder to see if a configuration with a given name exists.
    :param config_name: The name of the configuration to check for.
    :return: True if it exists, False otherwise.
    """
    file_name = config_name + ".dat"
    file_path = os.path.join(os.getcwd(), CONFIG_DIRECTORY, file_name)
    return os.path.exists(file_path)


def config_was_modified(config):
    """
    Checks if the given configuration is different from the version of it that is saved. If this configuration
    has yet to be saved, this will return false.
    :param config: The configuration to check.
    :return: True if the given configuration and the one in the file are different, false otherwise.
    """
    if config_exists(config.get_name()):
        saved_config = load_config(config.get_name())
        if config.equals(saved_config):
            return False
        else:
            return True
    else:
        return False


def save_config(config, config_name):
    """
    Write a given configuration object to a file. This will overwrite a configuration file
    if the name given already exists.
    :param config: A configuration object.
    :param config_name: The name to give the configuration file.
    """
    file_name = config_name + ".dat"
    file_path = os.path.join(os.getcwd(), CONFIG_DIRECTORY, file_name)
    if not os.path.exists(os.path.join(os.getcwd(), CONFIG_DIRECTORY)):
        os.mkdir(os.path.join(os.getcwd(), CONFIG_DIRECTORY))
    if os.path.exists(file_path):
        os.remove(file_path)
    config_file = open(file_path, "wb")
    pickle.dump(config, config_file)
    config_file.close()
    print("{} was successfully saved to the {} directory.".format(file_name, CONFIG_DIRECTORY))


def saved_config_display_string():
    """
    Go through each configuration file in the saved directory and build a string of the names
    of each valid configuration.
    :return: A string containing the names of all saved configurations.
    """
    if not os.path.exists(os.path.join(os.getcwd(), CONFIG_DIRECTORY)):
        return ""
    list_str = ""
    for filename in os.listdir(os.path.join(os.getcwd(), CONFIG_DIRECTORY)):
        if filename.endswith(".dat"):
            list_str += os.path.splitext(filename)[0] + "\n"
    return list_str


def load_config(config_name):
    """
    Load a configuration object from a file and return the object. The given configuration name
    must be a valid saved configuration.
    :param config_name: The name of the configuration file to load from.
    :return: The configuration object saved in that file.
    """
    file_name = config_name + ".dat"
    file_path = os.path.join(os.getcwd(), CONFIG_DIRECTORY, file_name)
    config_file = open(file_path, "rb")
    config = pickle.load(config_file)
    config_file.close()
    return config


def append_input_to_config(config, input_string):
    """
    Add the given input string, which should be a valid path to a file or directory, to the
    configuration as a new entry. The path will be checked to be valid and not already in the
    configuration.
    :param config: The configuration to add this path to.
    :param input_string: An absolute file path to a valid file or directory.
    :return: The configuration object with a new entry, and a boolean that is True when the
             given input path is valid, and false otherwise.
    """
    # Return false if this input already exists, or it's not a valid directory/file.
    if config.entry_exists(input_string):
        return config, False
    if not os.path.isdir(input_string) and not os.path.isfile(input_string):
        return config, False

    # Add the string as a new entry.
    config.new_entry(input_string)
    return config, True


def append_output_to_config(config, input_number, output_string):
    """
    Add a given string that points to a directory location as a destination for one of the
    entries in the given configuration. A number must be provided that corresponds to the
    index of the entry to modify in the configuration (starting at 1). If the input number is
    0, the given destination will be added to every entry. This will only append the
    destination to the configuration and will not overwrite any existing destinations.
    :param config: The configuration to add this path to.
    :param input_number: The index in the configuration of the entry to add the destination to.
                         This starts at 1, not 0. If the number is 0, the destination will be
                         appended to every entry.
    :param output_string: An absolute directory path where this input should be backed-up to.
    :return: The configuration object with a new destination, and a boolean that is True when the
             given destination path is valid, and false otherwise.
    """
    if input_number == 0:
        input_numbers = range(1, config.num_entries()+1)
    else:
        input_numbers = [input_number]

    # Return false if the output isn't a valid directory or it's a sub-path of the input.
    if not os.path.isdir(output_string):
        return config, False
    for input_num in input_numbers:
        output_absolute = os.path.join(os.path.realpath(output_string), '')
        input_absolute = os.path.join(os.path.realpath(config.get_input(input_num)), '')
        if os.path.commonprefix([output_absolute, input_absolute]) == input_absolute:
            return config, False

    # Add the string as a new output for this entry.
    for input_num in input_numbers:
        config.new_destination(input_num, output_string)
    return config, True


def edit_input_in_config(config, input_number, new_name):
    """
    Edit the name of an input in the configuration. This will be checked to ensure it's a valid
    directory/file path, and not already in the configuration.
    :param config: The configuration to edit a path in.
    :param input_number: The number of the index of the entry, starting at 1.
    :param new_name: The new input path.
    :return: The configuration object with an edited entry, and a boolean that is True when the
             given input path is valid, and false otherwise.
    """
    # Return false if this input already exists, or it's not a valid directory/file.
    if config.entry_exists(new_name):
        return config, False
    if not os.path.isdir(new_name) and not os.path.isfile(new_name):
        return config, False

    # Ensure the input can't be changed to that one of its outputs becomes a sub-folder.
    for destination in config.get_destinations(input_number):
        output_absolute = os.path.join(os.path.realpath(destination), '')
        input_absolute = os.path.join(os.path.realpath(new_name), '')
        if os.path.commonprefix([output_absolute, input_absolute]) == input_absolute:
            return config, False

    # Overwrite the name of the original entry.
    config.edit_entry_name(input_number, new_name)
    return config, True


def edit_destination_in_config(config, input_number, destination_number, new_name):
    """
    Edit the name of a destination path within an entry of the configuration. This will be checked
    to ensure it's a valid directory path and not already in this entry.
    :param config: The configuration to edit a path in.
    :param input_number: The number of the index of the entry, starting at 1.
    :param destination_number: The number of the index of the destination in this entry, starting at 1.
    :param new_name: The new destination path.
    :return: The configuration object with an edited destination, and a boolean that is True when the
             given destination path is valid, and false otherwise.
    """
    # Return false if the output isn't a valid directory or it's a sub-path of the input.
    if not os.path.isdir(new_name):
        return config, False
    output_absolute = os.path.join(os.path.realpath(new_name), '')
    input_absolute = os.path.join(os.path.realpath(config.get_input(input_number)), '')
    if os.path.commonprefix([output_absolute, input_absolute]) == input_absolute:
        return config, False

    # Overwrite the original destination.
    config.edit_destination(input_number, destination_number, new_name)
    return config, True


def config_display_string(config, show_exclusions=False):
    """
    Builds a string that contains all relevant information about a given configuration.
    :param config: The configuration object to display information about.
    :param show_exclusions: True if detailed exclusion information should be shown. False by default.
    :return: A string containing formatted information about the configuration.
    """
    if config.num_entries() == 0:
        return "NO FOLDERS/FILES SELECTED TO BACKUP"
    if config.get_name() == "":
        return_str = "CURRENT CONFIGURATION         \n"
    else:
        return_str = "CURRENT CONFIGURATION ({})    \n".format(config.get_name())
    input_number = 1
    for input_str, outputs_list in config.get_entries():
        total_size, total_files = util.directory_size_with_exclusions(input_str, config, input_number)
        input_size = total_size / (2**30)
        return_str += "\tBACKUP: {} ({:.2f} GiB, {} files)".format(input_str, input_size, total_files)
        if config.num_exclusions(input_number) > 0:
            if show_exclusions:
                return_str += "\n\t\tEXCLUSIONS:\n"
                for exclusion in config.get_exclusions(input_number):
                    return_str += "\t\t\t" + exclusion[0] + " \"" + exclusion[1] + "\"\n"
            else:
                return_str += " [Contains exclusions]\n"
        else:
            return_str += "\n"
        for output_str in outputs_list:
            return_str += "\t\tCOPY TO: " + output_str + "\n"
        input_number += 1
    return return_str.strip()
