"""
limitations.py
Author: Michael Pagliaro
A file containing all information about limitations and limitation types. Every type of limitation is defined
in this file, and changes to those only need to be made in this file to affect the entire program.
"""

import os
import util
import abc
import tkinter as tk
from fileview import Fileview


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
        limitation_type = get_limitation_type(self)
        if limitation_type.check_function(self, path_to_exclude, path_destination):
            return True
        else:
            return False

    def to_string(self, entry_input=None):
        """
        Creates a string representation of this limitation. If given another path as an argument and this limitation's
        type specifies the data should be a path, it will try to shorten the data of this limitation.
        :param entry_input: A path that could be used to shorten this limitation's data. For instance, if the
                            limitation data is the path a/b/c/d, and you pass in a/b/c for entry_input, when
                            the limitation data is displayed it will appear as .../c/d
        :return: This limitation's information in a string.
        """
        limitation_type = get_limitation_type(self)
        if entry_input is not None and limitation_type.data_is_path and os.path.exists(os.path.realpath(self._data)):
            display_limitation = util.shorten_path(os.path.realpath(self._data), entry_input)
        else:
            display_limitation = self._data
        return "{} \"{}\" {}".format(limitation_type.prefix_string, display_limitation, limitation_type.suffix_string)

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
    for when each is selectable in menus, input text for when the user is prompted to enter data for this limitation,
    and a function that takes a limitation and a path and returns true or false if that path satisfies that limitation.
    """

    def __init__(self, code, prefix_string, suffix_string, menu_text, input_text, function, ui_input, ui_edit,
                 ui_submit, always_applicable=False, data_is_path=False):
        """
        Create the new limitation type object. All fields are initialized from the start.
        :param code: A unique string identifier for this type.
        :param prefix_string: A string that can be printed before limitation data to explain how this limitation
                              modifies an exclusion.
        :param suffix_string: A string that can be printed after limitation data to explain how this limitation
                              modifies an exclusion.
        :param menu_text: Text that should display in menus when selecting which type to choose.
        :param input_text: Text that should display when inputting data for this limitation type.
        :param function: A function that takes a limitation object and a string file path. This will return true
                         if the file path satisfies the limitation based on the given limitation's data, and
                         false otherwise.
        :param ui_input: A function that defines a GUI widget that can accept input for this limitation type. It
                         will be given one argument, a window that it will be the child of. This should return the
                         widget that will be put in that window.
        :param ui_edit: A function that defines a GUI widget and how it will react when the limitation is being
                        edited. It will be given two arguments, first a window that it will be the child of, and
                        second the limitation being edited. This should return the widget that will be put in that
                        window, preferably with its input field set to the existing limitation's data.
        :param ui_submit: A function that defines how to handle when a limitation of this type is submitted through
                          the GUI. It will be given one argument, the GUI element that holds data for a new or
                          edited limitation of this type. It should access that element and return its data.
        :param always_applicable: A boolean that indicates if this limitation is always applicable to exclusions.
                                  A limitation type that is always applicable is allowed to be attached to an
                                  exclusion even if that exclusion type's accepts_limitations is false. This is
                                  false by default.
        :param data_is_path: A boolean that indicates the data held by this limitation should be a path. If true,
                             it will attempt to display the data as a path where possible and attempt to shorten
                             the path. False by default.
        """
        self._code = code
        self._prefix_string = prefix_string
        self._suffix_string = suffix_string
        self._menu_text = menu_text
        self._input_text = input_text
        self._function = function
        self._always_applicable = always_applicable
        self._data_is_path = data_is_path
        self._ui_input = ui_input
        self._ui_edit = ui_edit
        self._ui_submit = ui_submit

    @property
    def code(self):
        """
        The unique string identifier for this limitation type.
        :return: The type code as a string.
        """
        return self._code

    @property
    def prefix_string(self):
        """
        A string that can be printed before limitation data to explain how this limitation modifies an exclusion.
        :return: The suffix string as a string.
        """
        return self._prefix_string

    @property
    def suffix_string(self):
        """
        A string that can be printed after limitation data to explain how this limitation modifies an exclusion.
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
    def input_text(self):
        """
        Text that should display when inputting data for this limitation type.
        :return: The input text as a string.
        """
        return self._input_text

    @property
    def function(self):
        """
        A function that takes a limitation object and a string file path. This will return true if the
        file path satisfies the limitation based on the given limitation's data, and false otherwise.
        :return: The limitation function.
        """
        return self._function

    @property
    def always_applicable(self):
        """
        A boolean that indicates if this limitation is always applicable to exclusions. A limitation type that
        is always applicable is allowed to be attached to an exclusion even if that exclusion type's
        accepts_limitations is false.
        :return: True if this limitation type is always applicable, false otherwise.
        """
        return self._always_applicable

    @property
    def data_is_path(self):
        """
        A boolean that indicates the data held by this limitation should be a path. If true, it will attempt to
        display the data as a path where possible and attempt to shorten the path. False by default.
        :return: True if this limitation type's data should be a file path, false otherwise.
        """
        return self._data_is_path

    @property
    def ui_input(self):
        """
        A function that defines a GUI widget that can accept input for this limitation type. It will be given
        one argument, a window that it will be the child of. This should return the widget that will be put in
        that window.
        :return: This limitation type's UI input function.
        """
        return self._ui_input

    @property
    def ui_edit(self):
        """
        A function that defines a GUI widget and how it will react when the limitation is being edited. It will
        be given two arguments, first a window that it will be the child of, and second the limitation being edited.
        This should return the widget that will be put in that window, preferably with its input field set to the
        existing limitation's data.
        :return: This limitation type's UI edit function.
        """
        return self._ui_edit

    @property
    def ui_submit(self):
        """
        A function that defines how to handle when a limitation of this type is submitted through the GUI. It will
        be given one argument, the GUI element that holds data for a new or edited limitation of this type. It should
        access that element and return its data.
        :return: This limitation type's UI submit function.
        """
        return self._ui_submit

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


def get_limitation_type(limitation):
    """
    Utility function to get a limitation's type object by finding the limitation type that has the given
    limitation's code.
    :param limitation: The limitation to find the type for.
    :return: The limitation type if found, None otherwise.
    """
    for limitation_type in LIMITATION_TYPES:
        if limitation_type.code == limitation.code:
            return limitation_type
    return None


def is_valid_limitation_type(limit_type):
    """
    Checks if a given string corresponds to a valid limitation type.
    :param limit_type: A string to check.
    :return: True if the given string equals an limitation type's code, false otherwise.
    """
    for limitation_type in LIMITATION_TYPES:
        if limit_type == limitation_type.code:
            return True
    return False


"""
A global list of limitation types. This list should be referenced whenever creating menus to select a type
of limitation or create a new limitation. To add a new type of limitation, only a new element should be added
to this list.
"""
LIMITATION_TYPES = \
    [LimitationTypeInput(code="dir", prefix_string="directory", suffix_string="only",
                         menu_text="This exclusion should only affect a given directory and no sub-directories",
                         input_text="Enter the absolute path of a directory to limit this exclusion to: ",
                         data_is_path=True,
                         function=lambda limit, path: util.path_is_in_directory(path, os.path.realpath(limit.data)),
                         ui_input=lambda m: Fileview(master=m),
                         ui_edit=lambda m, limit: Fileview(master=m, default_focus=limit.data),
                         ui_submit=lambda e: e.get_focus_path()),
     LimitationTypeInput(code="sub", prefix_string="directory", suffix_string="and all sub-directories",
                         menu_text="This exclusion should affect a given directory and all of its sub-directories",
                         input_text="Enter the absolute path of a directory to limit this exclusion to: ",
                         data_is_path=True,
                         function=lambda limit, path: path.startswith(os.path.realpath(limit.data) + os.sep),
                         ui_input=lambda m: Fileview(master=m),
                         ui_edit=lambda m, limit: Fileview(master=m, default_focus=limit.data),
                         ui_submit=lambda e: e.get_focus_path()),
     LimitationTypeOutput(code="drive", prefix_string="the", suffix_string="drive during backups",
                          menu_text="This exclusion should only apply to a specific drive during a backup",
                          input_text="Enter the drive letter and a colon of the drive to limit this to: ",
                          always_applicable=True,
                          function=lambda limit, path: os.path.splitdrive(path)[0] == limit.data,
                          ui_input=lambda m: tk.Entry(m),
                          ui_edit=lambda m, limit: tk.Entry(m, textvariable=tk.StringVar(m, value=limit.data)),
                          ui_submit=lambda e: e.get())]
