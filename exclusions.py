"""
exclusions.py
Author: Michael Pagliaro
A file to handle all data about exclusions and exclusion types. Every type of exclusion is defined in this
file, and changes only need to be made here to add additional types of exclusions.
"""

import os
from os.path import realpath as rpath
import limitations


class Exclusion:
    """
    A class representing an exclusion that is held within an entry. Every exclusion has a code and some
    data (the meaning of the data is different depending on each code), and an optional limitation.
    """

    def __init__(self, code, data):
        """
        Create the exclusion object. This requires a code and some data for all exclusions. The optional
        limitation is initialized to None, but can be set later.
        :param code: The code of the exclusion type this exclusion uses.
        :param data: The exclusion data.
        """
        self._code = code
        self._data = data
        self._limitations = []

    @property
    def code(self):
        """
        The code that identifies this exclusion's type.
        :return: The exclusion type code as a string.
        """
        return self._code

    @code.setter
    def code(self, new_code):
        """
        Change the code of this exclusion so it corresponds to a different type. If the code is changed to a
        type that does not accept limitations, all limitations on this exclusion that aren't always applicable
        will be deleted.
        :param new_code: The code to change it to.
        """
        self._code = new_code
        for exclusion_type in EXCLUSION_TYPES:
            if self._code == exclusion_type.code:
                for limitation_idx in range(len(self._limitations)):
                    limitation = self._limitations[limitation_idx]
                    if not exclusion_type.accepts_limitations and not limitation.always_applicable():
                        self.delete_limitation(limitation_idx+1)

    @property
    def data(self):
        """
        The data relevant to this exclusion and its type.
        :return: The exclusion data.
        """
        return self._data

    @data.setter
    def data(self, new_data):
        """
        Change the data of this exclusion.
        :param new_data: The data to change it to.
        """
        self._data = new_data

    @property
    def limitations(self):
        """
        The list of limitations this exclusion has.
        :return: The list of limitation objects.
        """
        return self._limitations

    def get_limitation(self, limitation_number):
        """
        Get a limitation attached to this exclusion.
        :param limitation_number: The index of the limitation to get, starting at 1.
        :return: The limitation as a Limitation object.
        """
        return self._limitations[limitation_number-1]

    def delete_limitation(self, limitation_number):
        """
        Remove a limitation from this exclusion.
        :param limitation_number: The index of the limitation to get, starting at 1.
        """
        del self._limitations[limitation_number-1]

    def delete_limitations(self):
        """
        Delete all limitations from this exclusion.
        """
        self._limitations = []

    def add_limitation(self, limitation_code, limitation_data):
        """
        Add a limitation to this exclusion. This will cause this exclusion to be limited by an additional check.
        Limitation types that can apply are specified in the LIMITATION_TYPES list in limitations.py.
        :param limitation_code: The code of the limitation type this limitation uses.
        :param limitation_data: The limitation data.
        """
        self._limitations.append(limitations.Limitation(limitation_code, limitation_data))

    def accepts_limitations(self):
        """
        Checks if this exclusion accepts limitations. Each exclusion type specifies whether or not limitations
        can be used with it, so this checks if the type corresponding to this exclusion's code accepts
        limitations or not.
        :return: True if this exclusion accepts limitations, false otherwise.
        """
        for exclusion_type in EXCLUSION_TYPES:
            if self._code == exclusion_type.code:
                if exclusion_type.accepts_limitations:
                    return True
        return False

    def has_limitations(self):
        """
        Checks if this exclusion has at least one limitation applied to it.
        :return: True if a limitation exists on this exclusion, false otherwise.
        """
        return len(self._limitations) > 0

    def limitation_check(self, path_to_exclude, path_destination):
        """
        This limitation check is done every time a file is checked to be excluded and the exclusion alone
        returns true. This checks if this exclusion has limitations, then if its exclusion type accepts limitations or
        the limitation is always applicable. If both cases are true, it will check if the limitation is satisfied.
        This is checked for every limitation on this exclusion. If one limitation is satisfied, then this whole
        function returns true.
        :param path_to_exclude: The path to a folder or file that is being checked if it satisfies this exclusion.
        :param path_destination: The path of where the folder or file would be in its output.
        :return: True if this exclusion type accepts limitations, this exclusion has a limitation, and the given
                 path satisfies at least one limitation. This also returns true if the type doesn't accept limitations
                 or there is no limitation. Will return false if it checks a limitation and it's not satisfied.
        """
        if self.has_limitations():
            for limitation in self._limitations:
                limitation_type = limitations.get_limitation_type(limitation)
                if self.accepts_limitations() or limitation_type.always_applicable:
                    if limitation.satisfied(path_to_exclude, path_destination):
                        return True
                else:
                    # Should be an impossible state
                    return True
            return False
        else:
            return True

    def to_string(self):
        """
        Creates a string representation of this exclusion, not including limitations.
        :return: This exclusion's code and data as a string.
        """
        return "{} \"{}\"".format(self._code, self._data)

    def equals(self, other_exclusion):
        """
        Check if this exclusion is equal to another. Two exclusions are equal if their code and data are
        both the same, and if they have the same limitations or both have no limitations.
        :param other_exclusion: An exclusion to check if it's equal to this one.
        :return: True if the two exclusions are equal, false otherwise.
        """
        if not isinstance(other_exclusion, Exclusion):
            return False
        # Both codes and data must be the same
        if not self._code == other_exclusion._code or not self._data == other_exclusion._data:
            return False
        # Both exclusions must have the same number of limitations
        if len(self._limitations) != len(other_exclusion._limitations):
            return False
        # Every limitation in both exclusions must be identical
        for limitation_idx in range(len(self._limitations)):
            if not self._limitations[limitation_idx].equals(other_exclusion._limitations[limitation_idx]):
                return False
        return True


class ExclusionType:
    """
    A class representing an exclusion type. Each type defines everything about how a type of exclusion
    operates on data. They each must have a unique code, some menu and input text that describes them to the
    user, a boolean to say if they accept limitations or not, and a boolean function that shows if a given
    path should be excluded based on a given exclusion.
    """

    def __init__(self, code, menu_text, input_text, function, accepts_limitations=True):
        """
        Create a new exclusion type object. This initializes all the values at once.
        :param code: The unique identifier for each exclusion.
        :param menu_text: Text that appears on menus for selecting this type.
        :param input_text: Text that appears in input prompts when entering data for this exclusion type.
        :param accepts_limitations: True if this type can use optional limitations, false if it shouldn't.
        :param function: A function that returns true or false if a given path should be excluded when given
                         an exclusion. This function's first argument should be an exclusion object, and the
                         second should be a file path as a string. It should do a check using the exclusion's
                         data to see if the file path should be excluded.
        """
        self._code = code
        self._menu_text = menu_text
        self._input_text = input_text
        self._accepts_limitations = accepts_limitations
        self._function = function

    @property
    def code(self):
        """
        The unique identifier of this exclusion type.
        :return: The type code as a string.
        """
        return self._code

    @property
    def menu_text(self):
        """
        Text that appears on menus, primarily when selecting an exclusion type.
        :return: The menu text as a string.
        """
        return self._menu_text

    @property
    def input_text(self):
        """
        Text that appears as input prompts when entering data for this exclusion type.
        :return: The input text as a string.
        """
        return self._input_text

    @property
    def accepts_limitations(self):
        """
        Whether or not this exclusion accepts limitations. If true, the exclusion type's function and the
        individual exclusion's limitation must both return true for a file to be excluded. Will be true if
        it is not set manually.
        :return: The boolean for whether or not it accepts limitations.
        """
        return self._accepts_limitations

    @property
    def function(self):
        """
        A function that returns true or false if a given path should be excluded when given an exclusion.
        This function's first argument should be an exclusion object, and the second should be a file path
        as a string. It should do a check using the exclusion's data to see if the file path should be excluded.
        :return: This exclusion type's function.
        """
        return self._function

    def exclude_path(self, exclusion, path_to_exclude, path_destination):
        """
        Check if this should exclude a given file path given an exclusion's data. This will use this
        exclusion type's function to check if it passes, and if it does, it will perform a limitation
        check. If the limitation check passes too, then it returns true to mark this file should be
        excluded, and if not it will return false.
        :param exclusion: An exclusion with data to use to verify if the file should be excluded.
        :param path_to_exclude: A path to a file to check.
        :param path_destination: The path of where the folder or file would be in its output.
        :return: True if the path should be excluded, false otherwise.
        """
        if self._function(exclusion, path_to_exclude):
            if exclusion.limitation_check(path_to_exclude, path_destination):
                return True
        return False


def get_exclusion_type(exclusion):
    """
    Utility function to get an exclusion's type object by finding the exclusion type that has the given
    exclusion's code.
    :param exclusion: The exclusion to find the type for.
    :return: The exclusion type if found, None otherwise.
    """
    for exclusion_type in EXCLUSION_TYPES:
        if exclusion_type.code == exclusion.code:
            return exclusion_type
    return None


"""
The global list of exclusion types. This list should be referenced whenever creating menus to select a type
of exclusion or create a new exclusion. To add a new type of exclusion, only a new element should be added
to this list.
"""
EXCLUSION_TYPES = [ExclusionType(code="startswith", menu_text="Starts with some text",
                                 input_text="Files or folders that start with this text should be excluded: ",
                                 function=lambda excl, path: os.path.splitext(
                                     os.path.split(path)[1])[0].startswith(excl.data)),
                   ExclusionType(code="endswith", menu_text="Ends with some text",
                                 input_text="Files or folders that end with this text should be excluded: ",
                                 function=lambda excl, path: os.path.splitext(
                                     os.path.split(path)[1])[0].endswith(excl.data)),
                   ExclusionType(code="ext", menu_text="Specific file extension",
                                 input_text="Files with this extension should be excluded (the . before the " +
                                            "extension is needed): ",
                                 function=lambda excl, path: os.path.splitext(path)[1] == excl.data),
                   ExclusionType(code="directory", accepts_limitations=False, menu_text="Specific directory path",
                                 input_text="Folders with this absolute path will be excluded: ",
                                 function=lambda excl, path: os.path.isdir(path) and rpath(path) == rpath(excl.data)),
                   ExclusionType(code="file", menu_text="Specific filename",
                                 input_text="Files with this name and extension will be excluded: ",
                                 function=lambda excl, path: os.path.isfile(path) and os.path.split(
                                     path)[1] == excl.data)]
