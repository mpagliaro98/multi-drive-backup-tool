"""
entry.py
Author: Michael Pagliaro
A file containing all information about configuration entries.
"""

import exclusions


class Entry:
    """
    The class representing a configuration entry. Each entry contains an input path, a list of output
    paths, and a list of exclusions that is allowed to be empty.
    """

    def __init__(self, new_input):
        """
        Initialize the new entry. Each new entry requires at least an input path. This entry's outputs and
        exclusions lists will be initialized to empty.
        :param new_input: The input path for this new entry.
        """
        self._input = new_input
        self._outputs = []
        self._exclusions = []

    @property
    def input(self):
        """
        Get this entry's input field.
        :return: The input as a string.
        """
        return self._input

    @input.setter
    def input(self, new_input):
        """
        Change the input path of this entry.
        :param new_input: The path to change it to.
        """
        self._input = new_input

    @property
    def outputs(self):
        """
        The list of destination paths for this entry.
        :return: A list of destination paths as strings.
        """
        return self._outputs

    @outputs.deleter
    def outputs(self):
        """
        Delete all the destination paths in this entry.
        """
        self._outputs = []

    @property
    def exclusions(self):
        """
        The list of optional exclusions for this entry.
        :return: A list of Exclusion objects.
        """
        return self._exclusions

    @exclusions.deleter
    def exclusions(self):
        """
        Delete all the exclusions in this entry.
        """
        self._exclusions = []

    def new_destination(self, output_path):
        """
        Append a new destination path to the entry.
        :param output_path: The path to the folder where this entry should be backed up to.
        """
        self._outputs.append(output_path)

    def new_exclusion(self, exclusion_code, exclusion_data):
        """
        Append a new exclusion to the entry.
        :param exclusion_code: The code for the type of exclusion, defined in the exclusions.EXCLUSION_TYPES list.
        :param exclusion_data: The data to exclude based on the type.
        :return: The number of the index of this added exclusion, starting at 1.
        """
        self._exclusions.append(exclusions.Exclusion(exclusion_code, exclusion_data))
        return len(self._exclusions)

    def get_destination(self, destination_number):
        """
        Gets the destination at a specified point in the list, starting at 1.
        :param destination_number: The value corresponding to the destination's index, starting from 1.
                                   (so destination_number = 2 would get the destination at index 1)
        :return: The destination path as a string at the given position.
        """
        return self._outputs[destination_number-1]

    def get_exclusion(self, exclusion_number):
        """
        Gets the exclusion object at a specified point in the list, starting at 1.
        :param exclusion_number: The value corresponding to the exclusion's index, starting from 1.
                                 (so exclusion_number = 2 would get the exclusion at index 1)
        :return: The Exclusion object at the given position.
        """
        return self._exclusions[exclusion_number-1]

    def edit_destination(self, dest_number, new_output):
        """
        Change one of the destinations in this entry.
        :param dest_number: The number of the index of a destination for this entry, starting at 1.
        :param new_output: The path to change it to.
        """
        self._outputs[dest_number-1] = new_output

    def output_exists(self, output_path):
        """
        Checks if a given output path already exists in the list of outputs for this entry.
        :param output_path: A path to a folder as a string.
        :return: True if output_path already exists for this entry, false otherwise.
        """
        return output_path in self._outputs

    def enumerate_destinations(self):
        """
        Iterate through each destination of this entry and return a string of them alongside numbers.
        :return: A string containing every enumerated destination.
        """
        return_str = ""
        for dest_idx in range(len(self._outputs)):
            return_str += "{}: {}\n".format(dest_idx+1, self._outputs[dest_idx])
        return return_str.strip()

    def enumerate_exclusions(self):
        """
        Iterate through each exclusion of this entry and return a string of them alongside numbers.
        :return: A string containing every enumerated exclusion and limitation.
        """
        return_str = ""
        for excl_idx in range(len(self._exclusions)):
            exclusion = self._exclusions[excl_idx]
            print_str = "{}: {}".format(excl_idx+1, exclusion.to_string())
            if exclusion.has_limitations():
                for limitation in exclusion.limitations:
                    print_str += "\n\tLimit to {}".format(limitation.to_string(self._input))
            return_str += print_str + "\n"
        return return_str.strip()

    def num_destinations(self):
        """
        Get the number of destinations for this entry.
        :return: The number of destinations this entry has.
        """
        return len(self._outputs)

    def num_exclusions(self):
        """
        Get the number of exclusions for this entry.
        :return: The number of exclusions this entry has.
        """
        return len(self._exclusions)

    def delete_destination(self, destination_number):
        """
        Delete one destination path from this entry.
        :param destination_number: The number of the index of the destination in this entry,
                                   starting at 1.
        """
        del self._outputs[destination_number-1]

    def delete_exclusion(self, exclusion_number):
        """
        Delete one exclusion from this entry.
        :param exclusion_number: The number of the index of the exclusion in this entry,
                                 starting at 1.
        """
        del self._exclusions[exclusion_number-1]

    def should_exclude(self, path_to_exclude, path_destination=None):
        """
        Checks if a given file path should be excluded, based on this entry's exclusions.
        :param path_to_exclude: A file path to a folder or file to check if it should be excluded.
        :param path_destination: The path of where the folder or file would be in its output. Is set to
                                 None if no path is specified.
        :return: True if this folder/file should be excluded, false otherwise.
        """
        for exclusion in self._exclusions:
            for exclusion_type in exclusions.EXCLUSION_TYPES:
                if exclusion.code == exclusion_type.code:
                    if exclusion_type.exclude_path(exclusion, path_to_exclude, path_destination):
                        return True
        return False

    def to_string(self, exclusion_mode=False):
        """
        Create a formatted string for this entry, containing the input path and all its destination paths.
        There's an optional parameter to display exclusions instead of destinations.
        :param exclusion_mode: True to display exclusions instead of destinations. False by default.
        :return: A string containing all necessary information about this entry.
        """
        entry_str = "INPUT: {}\n".format(self._input)
        if exclusion_mode:
            # Display each exclusion and if it contains a limitation
            for exclusion in self._exclusions:
                entry_str += "\tEXCLUSION: {}\n".format(exclusion.to_string())
                if exclusion.has_limitations():
                    for limitation in exclusion.limitations:
                        entry_str += "\t\tLIMITATION: {}\n".format(limitation.to_string(self._input))
                else:
                    entry_str += "\n"
        else:
            # Display each destination path
            for destination in self._outputs:
                entry_str += "\tDESTINATION: {}\n".format(destination)
        return entry_str.strip()

    def equals(self, other_entry):
        """
        Check if this entry is equal to another. Two entries are equal if their input paths are the same,
        they have the same number of outputs and exclusions, and each of those outputs and exclusions
        are the same.
        :param other_entry: An entry to check if it's equal to this one.
        :return: True if the two entries are equal, false otherwise.
        """
        if not isinstance(other_entry, Entry):
            return False
        # Both input paths must be the same
        if not self._input == other_entry._input:
            return False
        # The number of outputs and exclusions must be the same
        if not len(self._outputs) == len(other_entry._outputs) or \
                not len(self._exclusions) == len(other_entry._exclusions):
            return False
        # Every output must be the same
        for output_idx in range(len(self._outputs)):
            if not self._outputs[output_idx] == other_entry._outputs[output_idx]:
                return False
        # Every exclusion must be the same
        for excl_idx in range(len(self._exclusions)):
            if not self._exclusions[excl_idx].equals(other_entry._exclusions[excl_idx]):
                return False
        return True
