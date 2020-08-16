"""
limitations.py
Author: Michael Pagliaro
A file containing all information about limitations and limitation types. Every type of limitation is defined
in this file, and changes to those only need to be made in this file to affect the entire program.
"""

import os
import util


class Limitation:
    """
    A class representing a limitation that is held within an exclusion. Each limitation only has a unique
    identifier called a code, and some data that is interpreted differently based on the code.
    """
    code = ""
    data = ""

    def __init__(self, code, data):
        """
        Create a new limitation object. All values are initialized at the start.
        :param code: A unique identifier corresponding to one of the limitation types.
        :param data: Some data for the limitation.
        """
        self.code = code
        self.data = data

    def satisfied(self, path_to_exclude):
        """
        Checks if this limitation is satisfied by a given file path. This will find the limitation type that
        corresponds to this limitation's code, then check if that limitation type's function returns true when
        given the path.
        :param path_to_exclude: A file path to check if it satisfies the limitation.
        :return: True if the limitation is satisfied, false otherwise.
        """
        for limitation_type in LIMITATION_TYPES:
            if self.code == limitation_type.code:
                if limitation_type.function(self, path_to_exclude):
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
            if self.code == limitation_type.code:
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
        if self.code == other_limitation.code and self.data == other_limitation.data:
            return True
        return False


class LimitationType:
    """
    A class representing a type of limitation. Each type defines how it operates on data, and what kinds of
    data satisfy the limitation. They each have a unique code, a suffix string used for displaying, menu text
    for when each is selectable in menus, and a function that takes a limitation and a path and returns true
    or false if that path satisfies that limitation.
    """
    code = ""
    suffix_string = ""
    menu_text = ""
    function = None

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
        self.code = code
        self.suffix_string = suffix_string
        self.menu_text = menu_text
        self.function = function


"""
A global list of limitation types. This list should be referenced whenever creating menus to select a type
of limitation or create a new limitation. To add a new type of limitation, only a new element should be added
to this list.
"""
LIMITATION_TYPES = [LimitationType(code="dir", suffix_string="only",
                                   menu_text="This limitation should only affect the directory specified and no " +
                                   "sub-directories",
                                   function=lambda limit, path: util.path_is_in_directory(path, limit.data)),
                    LimitationType(code="sub", suffix_string="and all sub-directories",
                                   menu_text="This limitation should affect the specified directory and all of " +
                                   "its sub-directories",
                                   function=lambda limit, path: path.startswith(os.path.realpath(limit.data) + os.sep))]
