"""
exclusions.py
Author: Michael Pagliaro
A file to handle all data about exclusions and exclusion types. Every type of exclusion is defined in this
file, and changes only need to be made here to add additional types of exclusions.
"""

import os
import limitations


class Exclusion:
    """
    A class representing an exclusion that is held within an entry. Every exclusion has a code and some
    data (the meaning of the data is different depending on each code), and an optional limitation.
    """
    code = ""
    data = ""
    limitation = None

    def __init__(self, code, data):
        """
        Create the exclusion object. This requires a code and some data for all exclusions. The optional
        limitation is initialized to None, but can be set later.
        :param code: The code of the exclusion type this exclusion uses.
        :param data: The exclusion data.
        """
        self.code = code
        self.data = data
        self.limitation = None

    def add_limitation(self, limitation_code, limitation_data):
        """
        Add a limitation to this exclusion. This will cause this exclusion to be limited by an additional check.
        Limitation types that can apply are specified in the LIMITATION_TYPES list in limitations.py.
        :param limitation_code: The code of the limitation type this limitation uses.
        :param limitation_data: The limitation data.
        """
        self.limitation = limitations.Limitation(limitation_code, limitation_data)

    def accepts_limitations(self):
        """
        Checks if this exclusion accepts limitations. Each exclusion type specifies whether or not limitations
        can be used with it, so this checks if the type corresponding to this exclusion's code accpets
        limitations or not.
        :return: True if this exclusion accepts limitations, false otherwise.
        """
        for exclusion_type in EXCLUSION_TYPES:
            if self.code == exclusion_type.code:
                if exclusion_type.accepts_limitations:
                    return True
        return False

    def has_limitation(self):
        """
        Checks if this exclusion has a limitation applied to it.
        :return: True if a limitation exists on this exclusion, false otherwise.
        """
        return self.limitation is not None

    def limitation_check(self, path_to_exclude):
        """
        This limitation check is done every time a file is checked to be excluded, and based on the exclusion
        alone it should be excluded. This will check if the current exclusion type accepts limitations, and if
        this exclusion has a limitation, and if both are true, it will check if the limitation is satisfied.
        :param path_to_exclude: The path to a folder or file that is being checked if it satisfies this exclusion.
        :return: True if this exclusion type accepts limitations, this exclusion has a limitation, and the given
                 path satisfies the limitation. This also returns true if the type doesn't accept limitations or
                 there is no limitation. Will return false if it checks the limitation and it's not satisfied.
        """
        if self.accepts_limitations() and self.has_limitation():
            if self.limitation.satisfied(path_to_exclude):
                return True
            else:
                return False
        else:
            return True

    def edit_code(self, new_code):
        """
        Change the code of this exclusion so it corresponds to a different type. If the code is changed to a
        type that does not accept limitations, and this exclusion had a limitation already, that limitation
        will be deleted.
        :param new_code: The code to change it to.
        """
        self.code = new_code
        for exclusion_type in EXCLUSION_TYPES:
            if self.code == exclusion_type.code:
                if not exclusion_type.accepts_limitations:
                    self.delete_limitation()

    def edit_data(self, new_data):
        """
        Change the data of this exclusion.
        :param new_data: The data to change it to.
        """
        self.data = new_data

    def delete_limitation(self):
        """
        Remove the limitation from this exclusion.
        """
        self.limitation = None

    def equals(self, other_exclusion):
        """
        Check if this exclusion is equal to another. Two exclusions are equal if their code and data are
        both the same, and if they have the same limitation or both have no limitation.
        :param other_exclusion: An exclusion to check if it's equal to this one.
        :return: True if the two exclusions are equal, false otherwise.
        """
        if not isinstance(other_exclusion, Exclusion):
            return False
        # Both codes and data must be the same
        if not self.code == other_exclusion.code or not self.data == other_exclusion.data:
            return False
        # If both do have limitations, both those limitations must be the same
        if self.has_limitation() and other_exclusion.has_limitation():
            if not self.limitation.equals(other_exclusion.limitation):
                return False
        # If one doesn't have a limitation, then both must not have a limitation
        elif self.has_limitation() != other_exclusion.has_limitation():
            return False
        return True


class ExclusionType:
    """
    A class representing an exclusion type. Each type defines everything about how a type of exclusion
    operates on data. They each must have a unique code, some menu and input text that describes them to the
    user, a boolean to say if they accept limitations or not, and a boolean function that shows if a given
    path should be excluded based on a given exclusion.
    """
    code = ""
    menu_text = ""
    input_text = ""
    accepts_limitations = False
    function = None

    def __init__(self, code, menu_text, input_text, accepts_limitations, function):
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
        self.code = code
        self.menu_text = menu_text
        self.input_text = input_text
        self.accepts_limitations = accepts_limitations
        self.function = function

    def exclude_path(self, exclusion, path_to_exclude):
        """
        Check if this should exclude a given file path given an exclusion's data. This will use this
        exclusion type's function to check if it passes, and if it does, it will perform a limitation
        check. If the limitation check passes too, then it returns true to mark this file should be
        excluded, and if not it will return false.
        :param exclusion: An exclusion with data to use to verify if the file should be excluded.
        :param path_to_exclude: A path to a file to check.
        :return: True if the path should be excluded, false otherwise.
        """
        if self.function(exclusion, path_to_exclude):
            if exclusion.limitation_check(path_to_exclude):
                return True
        return False


"""
The global list of exclusion types. This list should be referenced whenever creating menus to select a type
of exclusion or create a new exclusion. To add a new type of exclusion, only a new element should be added
to this list.
"""
EXCLUSION_TYPES = [ExclusionType(code="startswith", accepts_limitations=True, menu_text="Starts with some text",
                                 input_text="Files or folders that start with this text should be excluded: ",
                                 function=lambda excl, path: os.path.splitext(
                                     os.path.split(path)[1])[0].startswith(excl.data)),
                   ExclusionType(code="endswith", accepts_limitations=True, menu_text="Ends with some text",
                                 input_text="Files or folders that end with this text should be excluded: ",
                                 function=lambda excl, path: os.path.splitext(
                                     os.path.split(path)[1])[0].endswith(excl.data)),
                   ExclusionType(code="ext", accepts_limitations=True, menu_text="Specific file extension",
                                 input_text="Files with this extension should be excluded (the . before the " +
                                            "extension is needed): ",
                                 function=lambda excl, path: os.path.splitext(path)[1] == excl.data),
                   ExclusionType(code="directory", accepts_limitations=False, menu_text="Specific directory path",
                                 input_text="Folders with this absolute path will be excluded: ",
                                 function=lambda excl, path: os.path.realpath(path) == os.path.realpath(excl.data))]
