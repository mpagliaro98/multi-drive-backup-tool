"""
limitations.py
Author: Michael Pagliaro
A file containing all information about limitations and limitation types. Every type of limitation is defined
in this file, and changes to those only need to be made in this file to affect the entire program.
"""

import os
import util
import abc


class Limitation:
    """
    A class representing a limitation that is held within an exclusion. Each limitation only has a unique
    identifier called a code, and some data that is interpreted differently based on the code.
    """

    def __init__(self, code, data):
        """
        Create a new limitation object. All values are initialized at the start.
        :param code: A unique identifier corresponding to one of the limitation types.
        :param data: Some data for the limitation.
        """
        self._code = code
        self._data = data

    @property
    def code(self):
        """
        The code that identifies this limitation's type.
        :return: The limitation type code as a string.
        """
        return self._code

    @code.setter
    def code(self, new_code):
        """
        Change the code of this limitation. This should correspond with one of the limitation types defined
        in LIMITATION_TYPES.
        :param new_code: The new code for this limitation.
        """
        self._code = new_code

    @property
    def data(self):
        """
        The data relevant to this limitation and its type.
        :return: The limitation data.
        """
        return self._data

    @data.setter
    def data(self, new_data):
        """
        Change the data of this limitation.
        :param new_data: The new data for this limitation.
        """
        self._data = new_data

    def satisfied(self, path_to_exclude, path_destination):
        """
        Checks if this limitation is satisfied by a given file path. This will find the limitation type that
        corresponds to this limitation's code, then check if that limitation type's function returns true when
        given the path.
        :param path_to_exclude: A file path to check if it satisfies the limitation.
        :param path_destination: The path of where the folder or file would be in its output.
        :return: True if the limitation is satisfied, false otherwise.
        """
        for limitation_type in LIMITATION_TYPES:
            if self._code == limitation_type.code:
                if limitation_type.check_function(self, path_to_exclude, path_destination):
                    return True
        return False

    def get_proper_suffix(self, default_suffix=""):
        """
        Get the suffix string of the limitation type that corresponds to this limitation.
        :param default_suffix: The string to use by default if no suffix is found. This default value will also
                               be appended to the end of the suffix if it is found (allowing for things such as
                               new-lines). It is the empty string by default.
        :return: The proper suffix with default_suffix appended to the end of it if one exists, or just
                 default_suffix if none exists.
        """
        limit_mode = default_suffix
        for limitation_type in LIMITATION_TYPES:
            if self._code == limitation_type.code:
                limit_mode = limitation_type.suffix_string + default_suffix
        return limit_mode

    def equals(self, other_limitation):
        """
        Check if this limitation is equal to another. Two limitations are equal if their codes and data
        are the same.
        :param other_limitation: Another limitation to check if it's equal to this one.
        :return: True if they are equal, false otherwise.
        """
        if not isinstance(other_limitation, Limitation):
            return False
        # The codes and data must be equal
        if self._code == other_limitation._code and self._data == other_limitation._data:
            return True
        return False


class LimitationType(metaclass=abc.ABCMeta):
    """
    A class representing a type of limitation. Each type defines how it operates on data, and what kinds of
    data satisfy the limitation. They each have a unique code, a suffix string used for displaying, menu text
    for when each is selectable in menus, and a function that takes a limitation and a path and returns true
    or false if that path satisfies that limitation.
    """

    def __init__(self, code, suffix_string, menu_text, function):
        """
        Create the new limitation type object. All fields are initialized from the start.
        :param code: A unique string identifier for this type.
        :param suffix_string: A string that can be used to display how this limitation modifies an exclusion.
        :param menu_text: Text that should display in menus when selecting which type to choose.
        :param function: A function that takes a limitation object and a string file path. This will return true
                         if the file path satisfies the limitation based on the given limitation's data, and
                         false otherwise.
        """
        self._code = code
        self._suffix_string = suffix_string
        self._menu_text = menu_text
        self._function = function

    @property
    def code(self):
        """
        The unique string identifier for this limitation type.
        :return: The type code as a string.
        """
        return self._code

    @property
    def suffix_string(self):
        """
        Text that can be used to display how this limitation modifies an exclusion.
        :return: The suffix string as a string.
        """
        return self._suffix_string

    @property
    def menu_text(self):
        """
        Text that should display in menus when selecting which limitation type to use.
        :return: The menu text as a string.
        """
        return self._menu_text

    @property
    def function(self):
        """
        A function that takes a limitation object and a string file path. This will return true if the
        file path satisfies the limitation based on the given limitation's data, and false otherwise.
        :return: The limitation function.
        """
        return self._function

    @abc.abstractmethod
    def check_function(self, limitation, path_to_exclude, path_destination):
        """
        An abstract method that will call this limitation type's function. Each sub-class of LimitationType
        must define this in order to define which data is sent to the limitation type function.
        :param limitation: The limitation of this type that is being used.
        :param path_to_exclude: A path to a file that's being checked for exclusion.
        :param path_destination: A destination path of where the file will be sent during the backup process.
                                 This can be None.
        :return: True if the limitation type function passes, false otherwise.
        """
        pass


class LimitationTypeInput(LimitationType):
    """
    A sub-class of LimitationType that works only on the input path that is given to check_function().
    """

    def check_function(self, limitation, path_to_exclude, path_destination):
        """
        Implements this abstract method from LimitationType. This calls the limitation type's function, and
        only passes the limitation and the input path to it.
        :param limitation: The limitation of this type that is being used.
        :param path_to_exclude: A path to a file that's being checked for exclusion.
        :param path_destination: A destination path of where the file will be sent during the backup process.
                                 This can be None.
        :return: True if the limitation type function passes, false otherwise.
        """
        return self._function(limitation, path_to_exclude)


class LimitationTypeOutput(LimitationType):
    """
    A sub-class of LimitationType that works only on the output path that is given to check_function().
    """

    def check_function(self, limitation, path_to_exclude, path_destination):
        """
        Implements this abstract method from LimitationType. This calls the limitation type's function, and
        only passes the limitation and the output path to it. It will return false if the output path is None.
        :param limitation: The limitation of this type that is being used.
        :param path_to_exclude: A path to a file that's being checked for exclusion.
        :param path_destination: A destination path of where the file will be sent during the backup process.
                                 This can be None.
        :return: True if the limitation type function passes, false otherwise. False if the destination
                 path is None.
        """
        if path_destination is None:
            return False
        return self._function(limitation, path_destination)


"""
A global list of limitation types. This list should be referenced whenever creating menus to select a type
of limitation or create a new limitation. To add a new type of limitation, only a new element should be added
to this list.
"""
LIMITATION_TYPES = \
    [LimitationTypeInput(code="dir", suffix_string="only",
                         menu_text="This limitation should only affect the directory specified and no sub-directories",
                         function=lambda limit, path: util.path_is_in_directory(path, os.path.realpath(limit.data))),
     LimitationTypeInput(code="sub", suffix_string="and all sub-directories",
                         menu_text="This limitation should affect the specified directory and all of its " +
                                   "sub-directories",
                         function=lambda limit, path: path.startswith(os.path.realpath(limit.data) + os.sep))]
