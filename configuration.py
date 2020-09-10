"""
configuration.py
Author: Michael Pagliaro
A file to handle saving, loading, and the handling at runtime of configurations of files to backup and
their destinations.
"""

import os
import pickle
import util
import entry
import copy

# Static global variable for the name of the directory configs are saved to
CONFIG_DIRECTORY = "configs"


class Configuration:
    """
    Class for representing configurations. This holds the name of the current configuration (if it
    has one) as well as a list of Entry objects.
    """

    def __init__(self):
        """
        Create the Configuration object.
        """
        self._name = None
        self._entries = []

    @property
    def name(self):
        """
        Get the name of this configuration.
        :return: The name as a string. Returns None if no name was set.
        """
        return self._name

    @name.setter
    def name(self, new_name):
        """
        Set the name of this configuration to a new value.
        :param new_name: The new name to set.
        """
        self._name = new_name

    @property
    def entries(self):
        """
        The list of entries contained within this configuration.
        :return: A list of Entry objects.
        """
        return self._entries

    def new_entry(self, input_path):
        """
        Create a new entry in the configuration. This will add the given path as a new input as it
        creates a new Entry object and adds it to the list.
        :param input_path: The path to a folder or file to backup.
        """
        self._entries.append(entry.Entry(input_path))

    def get_all_entry_inputs(self):
        """
        Returns a list of all the "input" fields from each Entry in the list.
        :return: A list containing every input string.
        """
        return [item.input for item in self._entries]

    def get_all_entry_outputs(self):
        """
        Returns a list of all the "outputs" fields from each Entry in the list.
        :return: A list containing every outputs list, so each element is a list of strings.
        """
        return [item.outputs for item in self._entries]

    def entry_exists(self, input_path):
        """
        Checks if a given input path already exists in the configuration.
        :param input_path: The path to a folder or file to backup.
        :return: True if it already exists, false otherwise.
        """
        return input_path in self.get_all_entry_inputs()

    def all_entries_have_outputs(self):
        """
        Checks if all entries in the configuration have at least one output specified.
        :return: True if all entries have at least one destination, false otherwise.
        """
        for destination_list in self.get_all_entry_outputs():
            if len(destination_list) == 0:
                return False
        return True

    def all_paths_are_valid(self):
        """
        Checks if any input or output path in this configuration is not valid.
        :return: True if every path is valid, false otherwise.
        """
        # Loops through every input path and checks if it exists
        for input_path in self.get_all_entry_inputs():
            if not os.path.exists(input_path):
                return False
        # Loops through every output path and checks if it exists
        for output_list in self.get_all_entry_outputs():
            for output_path in output_list:
                if not os.path.exists(output_path):
                    return False
        return True

    def get_entry(self, entry_number):
        """
        Gets the entry at a specified point in the list, starting at 1.
        :param entry_number: The value corresponding to the entry's index, starting from 1. (so entry_number = 2
                             would get the entry at index 1)
        :return: The Entry object at the given position.
        """
        return self._entries[entry_number-1]

    def get_zipped_entries(self):
        """
        Get a list of inputs and outputs, where each element is a sublist where the first element is an
        input and the second element is a list of its corresponding outputs.
        :return: A zipped list of inputs and outputs.
        """
        return zip(self.get_all_entry_inputs(), self.get_all_entry_outputs())

    def enumerate_entries(self):
        """
        Iterate through each input/outputs entry in this configuration and write them to a
        string, prefaced by numbers.
        :return: A string containing every enumerated entry.
        """
        entry_inputs = self.get_all_entry_inputs()
        entry_outputs = self.get_all_entry_outputs()
        return_str = ""
        for entry_idx in range(len(entry_inputs)):
            return_str += "{}: {} --> {}\n".format(entry_idx+1, entry_inputs[entry_idx], entry_outputs[entry_idx])
        return return_str.strip()

    def num_entries(self):
        """
        Get the number of entries this configuration is holding.
        :return: The number of entries.
        """
        return len(self._entries)

    def delete_entry(self, entry_number):
        """
        Delete an entry from the configuration.
        :param entry_number: The number of the index of the entry, starting at 1.
        """
        del self._entries[entry_number-1]

    def check_for_cyclic_entries(self):
        """
        Detects cyclic entries in the configuration. A cyclic entry is defined as an entry who's input
        path contains the output of a previous entry. For example, if entry 1 takes the folder a/b/c/d and
        backs it up to m/n/o/p, then entry 2 wants to backup the folder m/n/o, that would be a cyclic entry
        since during the backup process, the size of the folder entry 2 would backup would grow. This throws
        off directory size calculations and gives the user a technically non-accurate size number.
        :return: True if this configuration contains at least one cyclic entry, false otherwise.
        """
        destination_list = []
        for config_entry in self._entries:
            for destination in config_entry.outputs:
                destination_list.append(destination)
            for destination in destination_list:
                output_absolute = os.path.join(destination, '')
                input_absolute = os.path.join(config_entry.input, '')
                if os.path.commonprefix([output_absolute, input_absolute]) == input_absolute:
                    return True
        return False

    def equals(self, other_config):
        """
        Check if this configuration is equal to another. For them to be equal, the names need to be
        equal, and every Entry needs to be equal.
        :param other_config: A configuration to check if it's equal to this one.
        :return: True if they are equal, false otherwise.
        """
        if not isinstance(other_config, Configuration):
            return False
        # The names must be equal
        if not self.name == other_config.name:
            return False
        # They must have the same number of entries
        if not len(self._entries) == len(other_config._entries):
            return False
        # Every entry must be equal
        for entry_idx in range(1, len(self._entries)+1):
            if not self.get_entry(entry_idx).equals(other_config.get_entry(entry_idx)):
                return False
        return True


def config_exists(config_name):
    """
    Checks the saved configuration folder to see if a configuration with a given name exists.
    :param config_name: The name of the configuration to check for.
    :return: True if it exists, False otherwise.
    """
    if config_name is None:
        return False
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
    if config_exists(config.name):
        saved_config = load_config(config.name)
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
    if config_name is None:
        return None
    file_name = config_name + ".dat"
    file_path = os.path.join(os.getcwd(), CONFIG_DIRECTORY, file_name)
    config_file = open(file_path, "rb")
    config = pickle.load(config_file)
    config_file.close()
    return config


def append_input_to_config(config, input_string):
    """
    Add the given input string, which should be a valid path to a file or directory, to the
    configuration as a new entry. The path will be checked to be valid and that it does not
    create a cyclic entry.
    :param config: The configuration to add this path to.
    :param input_string: An absolute file path to a valid file or directory.
    :return: A boolean that is True when the given input path is valid, and false otherwise.
    """
    # Return false if this input is not a valid directory/file.
    if not os.path.isdir(input_string) and not os.path.isfile(input_string):
        return False

    # Add the string as a new entry and check for cyclic entries, remove it if it creates one
    config.new_entry(os.path.realpath(input_string))
    if config.check_for_cyclic_entries():
        config.delete_entry(config.num_entries())
        return False
    return True


def append_output_to_config(config, entry_number, output_string):
    """
    Add a given string that points to a directory location as a destination for one of the
    entries in the given configuration. A number must be provided that corresponds to the
    index of the entry to modify in the configuration (starting at 1). If the input number is
    0, the given destination will be added to every entry. This will only append the
    destination to the configuration and will not overwrite any existing destinations.
    :param config: The configuration to add this path to.
    :param entry_number: The index in the configuration of the entry to add the destination to.
                         This starts at 1, not 0. If the number is 0, the destination will be
                         appended to every entry.
    :param output_string: An absolute directory path where this input should be backed-up to.
    :return: A boolean that is True when the given destination path is valid, and false otherwise.
    """
    if entry_number == 0:
        entry_numbers = range(1, config.num_entries()+1)
    else:
        entry_numbers = [entry_number]

    # Return false if the output isn't a valid directory or it's a sub-path of the input.
    if not os.path.isdir(output_string):
        return False
    for current_entry_number in entry_numbers:
        output_absolute = os.path.join(os.path.realpath(output_string), '')
        input_absolute = os.path.join(os.path.realpath(config.get_entry(current_entry_number).input), '')
        if os.path.commonprefix([output_absolute, input_absolute]) == input_absolute:
            return False

    # Copy the configuration and attempt to add the new output, return false if it creates cyclic entries
    copy_config = copy.deepcopy(config)
    for current_entry_number in entry_numbers:
        copy_config.get_entry(current_entry_number).new_destination(os.path.realpath(output_string))
    if copy_config.check_for_cyclic_entries():
        return False

    # Add the string as a new output for this entry.
    for current_entry_number in entry_numbers:
        config.get_entry(current_entry_number).new_destination(os.path.realpath(output_string))
    return True


def edit_input_in_config(config, entry_number, new_input):
    """
    Edit the name of an input in the configuration. This will be checked to ensure it's a valid
    directory/file path and doesn't create a cyclic entry.
    :param config: The configuration to edit a path in.
    :param entry_number: The number of the index of the entry, starting at 1.
    :param new_input: The new input path.
    :return: A boolean that is True when the given input path is valid, and false otherwise.
    """
    # Return false if this input is not a valid directory/file.
    if not os.path.isdir(new_input) and not os.path.isfile(new_input):
        return False

    # Ensure the input can't be changed to that one of its outputs becomes a sub-folder.
    for destination in config.get_entry(entry_number).outputs:
        output_absolute = os.path.join(os.path.realpath(destination), '')
        input_absolute = os.path.join(os.path.realpath(new_input), '')
        if os.path.commonprefix([output_absolute, input_absolute]) == input_absolute:
            return False

    # Overwrite the name of the original entry and check for cyclic entries.
    old_input = config.get_entry(entry_number).input
    config.get_entry(entry_number).input = os.path.realpath(new_input)
    if config.check_for_cyclic_entries():
        config.get_entry(entry_number).input = old_input
        return False
    return True


def edit_destination_in_config(config_entry, destination_number, new_output, config):
    """
    Edit the name of a destination path within an entry of the configuration. This will be checked
    to ensure it's a valid directory path and not already in this entry.
    :param config_entry: An entry from the configuration that's currently being edited.
    :param destination_number: The number of the index of the destination in this entry, starting at 1.
    :param new_output: The new destination path.
    :param config: The current configuration, needed to check for cyclic entries.
    :return: A boolean that is True when the given destination path is valid, and false otherwise.
    """
    # Return false if the output isn't a valid directory or it's a sub-path of the input.
    if not os.path.isdir(new_output):
        return False
    output_absolute = os.path.join(os.path.realpath(new_output), '')
    input_absolute = os.path.join(os.path.realpath(config_entry.input), '')
    if os.path.commonprefix([output_absolute, input_absolute]) == input_absolute:
        return False

    # Overwrite the original destination and check for cyclic entries, if one exists then revert the change.
    old_destination = config_entry.get_destination(destination_number)
    config_entry.edit_destination(destination_number, os.path.realpath(new_output))
    if config.check_for_cyclic_entries():
        config_entry.edit_destination(destination_number, old_destination)
        return False
    return True


def config_display_string(config, show_exclusions=False):
    """
    Builds a string that contains all relevant information about a given configuration.
    :param config: The configuration object to display information about.
    :param show_exclusions: True if detailed exclusion information should be shown. False by default.
    :return: A string containing formatted information about the configuration.
    """
    # Display this message if there is nothing in the configuration yet
    if config.num_entries() == 0:
        return "NO FOLDERS/FILES SELECTED TO BACKUP"

    # Header: show the configuration name if it exists
    if config.name is None:
        return_str = "CURRENT CONFIGURATION         \n"
    else:
        return_str = "CURRENT CONFIGURATION ({})    \n".format(config.name)

    # Loop through every entry and show information about each
    entry_number = 1
    for input_str, outputs_list in config.get_zipped_entries():
        # Display the size of this entry's input
        total_size, total_files = util.directory_size_with_exclusions(input_str, config, entry_number)
        return_str += "\tBACKUP: {} ({}, {} files)".format(input_str, util.bytes_to_string(total_size, 2), total_files)

        # If this entry has exclusions, show them
        if config.get_entry(entry_number).num_exclusions() > 0:
            # If show_exclusions is true, show all information, otherwise just show that exclusions exist here
            if show_exclusions:
                return_str += "\n\t\tEXCLUSIONS:\n"
                for exclusion in config.get_entry(entry_number).exclusions:
                    return_str += "\t\t\t{}\n".format(exclusion.to_string())
                    if exclusion.has_limitations():
                        for limitation in exclusion.limitations:
                            return_str += "\t\t\t\tLimit to {}\n".format(limitation.to_string(
                                config.get_entry(entry_number).input))
                    else:
                        return_str += "\n"
            else:
                return_str += " [Contains exclusions]\n"
        else:
            return_str += "\n"

        # Display every output path below the previously displayed input
        for output_str in outputs_list:
            return_str += "\t\tCOPY TO: {}\n".format(output_str)
        entry_number += 1
    return return_str.strip()
