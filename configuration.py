"""
configuration.py
Author: Michael Pagliaro
A file to handle saving, loading, and the handling at runtime of configurations of files to backup and
their destinations.
"""


class Configuration:
    """
    Class for representing configurations. This holds data for which folders to backup and where
    to back them up to.
    """
    inputs = []
    outputs = []

    def __init__(self):
        """
        Create the Configuration object.
        """
        self.inputs = []
        self.outputs = []

    def new_entry(self, input_path):
        """
        Create a new entry in the configuration. This will add the given path as a new input and
        create a corresponding empty list of destinations.
        :param input_path: The path to a folder or file to backup.
        """
        self.inputs.append(input_path)
        self.outputs.append([])

    def new_destination(self, entry_number, output_path):
        """
        Append a new destination path to an entry.
        :param entry_number: The number of the index of the entry, starting at 1.
        :param output_path: The path to the folder where this entry should be backed up to.
        """
        self.outputs[entry_number-1].append(output_path)

    def enumerate_entries(self):
        """
        Iterate through each input/outputs entry in this configuration and display them to the
        screen, prefaced by numbers.
        """
        for entry_idx in range(len(self.inputs)):
            print("{}: {} --> {}".format(entry_idx+1, self.inputs[entry_idx], self.outputs[entry_idx]))

    def num_entries(self):
        """
        Get the number of input/outputs entries this configuration is holding.
        :return: The number of entries.
        """
        return len(self.inputs)


def config_exists(config_name):
    """
    Checks the saved configuration folder to see if a configuration with a given name exists.
    :param config_name: The name of the configuration to check for.
    :return: True if it exists, False otherwise.
    """
    return False


def save_config(config, config_name):
    """
    Write a given configuration object to a file. This will overwrite a configuration file
    if the name given already exists.
    :param config: A configuration object.
    :param config_name: The name to give the configuration file.
    """
    print("stub")


def display_saved_configs():
    """
    Go through each configuration file in the saved directory and build a string of the names
    of each valid configuration.
    :return: A string containing the names of all saved configurations.
    """
    return ""


def load_config(config_name):
    """
    Load a configuration object from a file and return the object. The given configuration name
    must be a valid saved configuration.
    :param config_name: The name of the configuration file to load from.
    :return: The configuration object saved in that file.
    """
    return Configuration()


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
    return config, True


def append_output_to_config(config, input_number, output_name):
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
    :param output_name: An absolute directory path where this input should be backed-up to.
    :return: The configuration object with a new destination, and a boolean that is True when the
             given destination path is valid, and false otherwise.
    """
    return config, True


def display_config(config):
    """
    Builds a string that contains all relevant information about a given configuration.
    :param config: The configuration object to display information about.
    :return: A string containing formatted information about the configuration.
    """
    return ""
