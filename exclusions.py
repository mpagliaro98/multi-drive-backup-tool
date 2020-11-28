"""
exclusions.py
Author: Michael Pagliaro
A file to handle all data about exclusions and exclusion types. Every type of exclusion is defined in this
file, and changes only need to be made here to add additional types of exclusions.
"""

import os
from datetime import datetime
from os.path import realpath as rpath
import limitations
from fileview import Fileview
import tkinter as tk
from tkcalendar import DateEntry
import dateutil.parser as parser


# Limit to the number of limitations allowed in an exclusion
MAX_LIMITATIONS = 100


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
        exclusion_type = get_exclusion_type(self)
        limit_idx_list = []
        for limitation_idx in range(len(self._limitations)):
            limitation = self._limitations[limitation_idx]
            limitation_type = limitations.get_limitation_type(limitation)
            if not exclusion_type.accepts_limitations and not limitation_type.always_applicable:
                limit_idx_list.append(limitation_idx+1)
        for delete_idx in reversed(limit_idx_list):
            self.delete_limitation(delete_idx)

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

    @limitations.deleter
    def limitations(self):
        """
        Delete all limitations from this exclusion.
        """
        self._limitations = []

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

    def add_limitation(self, limitation_code, limitation_data):
        """
        Add a limitation to this exclusion. This will cause this exclusion to be limited by an additional check.
        Limitation types that can apply are specified in the LIMITATION_TYPES list in limitations.py.
        :param limitation_code: The code of the limitation type this limitation uses.
        :param limitation_data: The limitation data.
        """
        if self.num_limitations() < MAX_LIMITATIONS:
            self._limitations.append(limitations.Limitation(limitation_code, limitation_data))

    def has_limitations(self):
        """
        Checks if this exclusion has at least one limitation applied to it.
        :return: True if a limitation exists on this exclusion, false otherwise.
        """
        return len(self._limitations) > 0

    def num_limitations(self):
        """
        Gets the number of limitations that this exclusion has.
        :return: The number of limitations.
        """
        return len(self._limitations)

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
        exclusion_type = get_exclusion_type(self)
        if self.has_limitations():
            for limitation in self._limitations:
                limitation_type = limitations.get_limitation_type(limitation)
                if exclusion_type.accepts_limitations or limitation_type.always_applicable:
                    if limitation.satisfied(path_to_exclude, path_destination):
                        return True
                else:
                    # Should be an impossible state
                    return True
            return False
        else:
            return True

    def enumerate_limitations(self, entry_input=None):
        """
        Iterate through all the limitations of this exclusion and display them alongside a number.
        :return: A string containing every enumerated limitation.
        """
        return_str = ""
        for limit_idx in range(len(self._limitations)):
            limitation = self._limitations[limit_idx]
            return_str += "{}: {}\n".format(limit_idx+1, limitation.to_string(entry_input=entry_input))
        return return_str.strip()

    def to_string(self, include_limitations=False, entry_input=None):
        """
        Creates a string representation of this exclusion. Using an optional parameter, limitations can
        also be included in the string.
        :param include_limitations: Writes limitations as well if true, false otherwise.
        :param entry_input:
        :return: This exclusion's code and data as a string.
        """
        return_str = "{} \"{}\"".format(self._code, self._data)
        if include_limitations:
            for limitation in self._limitations:
                return_str += "\n\tLimited to {}".format(limitation.to_string(entry_input))
        return return_str

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

    def __init__(self, code, menu_text, input_text, function, ui_input, ui_edit, ui_submit, accepts_limitations=True):
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
        :param ui_input: A function that defines a GUI widget that can accept input for this limitation type. It
                         will be given one argument, a window that it will be the child of. This should return
                         the widget that will be put in that window.
        :param ui_edit: A function that defines a GUI widget and how it will react when the exclusion is being
                        edited. It will be given two arguments, first a window that it will be the child of, and
                        second the exclusion being edited. This should return the widget that will be put in that
                        window, preferably with its input field set to the existing exclusion's data.
        :param ui_submit: A function that defines how to handle when an exclusion of this type is submitted through
                          the GUI. It will be given one argument, the GUI element that holds data for a new or
                          edited exclusion of this type. It should access that element and return its data.
        """
        self._code = code
        self._menu_text = menu_text
        self._input_text = input_text
        self._accepts_limitations = accepts_limitations
        self._ui_input = ui_input
        self._ui_edit = ui_edit
        self._ui_submit = ui_submit
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

    @property
    def ui_input(self):
        """
        A function that defines a GUI widget that can accept input for this exclusion type. It will be given
        one argument, a window that it will be the child of. This should return the widget that will be put in
        that window.
        :return: This exclusion type's UI input function.
        """
        return self._ui_input

    @property
    def ui_edit(self):
        """
        A function that defines a GUI widget and how it will react when the exclusion is being edited. It will
        be given two arguments, first a window that it will be the child of, and second the exclusion being edited.
        This should return the widget that will be put in that window, preferably with its input field set to the
        existing exclusion's data.
        :return: This exclusion type's UI edit function.
        """
        return self._ui_edit

    @property
    def ui_submit(self):
        """
        A function that defines how to handle when an exclusion of this type is submitted through the GUI. It will
        be given one argument, the GUI element that holds data for a new or edited exclusion of this type. It should
        access that element and return its data.
        :return: This exclusion type's UI submit function.
        """
        return self._ui_submit

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


def is_valid_exclusion_type(excl_type):
    """
    Checks if a given string corresponds to a valid exclusion type.
    :param excl_type: A string to check.
    :return: True if the given string equals an exclusion type's code, false otherwise.
    """
    for exclusion_type in EXCLUSION_TYPES:
        if excl_type == exclusion_type.code:
            return True
    return False


"""
The global list of exclusion types. This list should be referenced whenever creating menus to select a type
of exclusion or create a new exclusion. To add a new type of exclusion, only a new element should be added
to this list.
"""
EXCLUSION_TYPES = [ExclusionType(code="startswith", menu_text="Starts with some text",
                                 input_text="Files or folders that start with this text should be excluded: ",
                                 function=lambda excl, path: os.path.splitext(
                                     os.path.split(path)[1])[0].startswith(excl.data),
                                 ui_input=lambda m: tk.Entry(m),
                                 ui_edit=lambda m, excl: tk.Entry(m, textvariable=tk.StringVar(m, value=excl.data)),
                                 ui_submit=lambda e: e.get()),
                   ExclusionType(code="endswith", menu_text="Ends with some text",
                                 input_text="Files or folders that end with this text should be excluded: ",
                                 function=lambda excl, path: os.path.splitext(
                                     os.path.split(path)[1])[0].endswith(excl.data),
                                 ui_input=lambda m: tk.Entry(m),
                                 ui_edit=lambda m, excl: tk.Entry(m, textvariable=tk.StringVar(m, value=excl.data)),
                                 ui_submit=lambda e: e.get()),
                   ExclusionType(code="ext", menu_text="Specific file extension",
                                 input_text="Files with this extension should be excluded (the . before the " +
                                            "extension is needed): ",
                                 function=lambda excl, path: os.path.splitext(path)[1] == excl.data,
                                 ui_input=lambda m: tk.Entry(m),
                                 ui_edit=lambda m, excl: tk.Entry(m, textvariable=tk.StringVar(m, value=excl.data)),
                                 ui_submit=lambda e: e.get()),
                   ExclusionType(code="directory", accepts_limitations=False, menu_text="Specific directory path",
                                 input_text="Folders with this absolute path will be excluded: ",
                                 function=lambda excl, path: os.path.isdir(path) and rpath(path) == rpath(excl.data),
                                 ui_input=lambda m: Fileview(master=m),
                                 ui_edit=lambda m, excl: Fileview(master=m, default_focus=excl.data),
                                 ui_submit=lambda e: e.get_focus_path()),
                   ExclusionType(code="file", menu_text="Specific filename",
                                 input_text="Files with this name and extension will be excluded: ",
                                 function=lambda excl, path: os.path.isfile(path) and os.path.split(
                                     path)[1] == excl.data,
                                 ui_input=lambda m: tk.Entry(m),
                                 ui_edit=lambda m, excl: tk.Entry(m, textvariable=tk.StringVar(m, value=excl.data)),
                                 ui_submit=lambda e: e.get()),
                   ExclusionType(code="dir_name", menu_text="Specific directory name",
                                 input_text="Directories with this name will be excluded: ",
                                 function=lambda excl, path: os.path.isdir(path) and os.path.split(
                                     path)[1] == excl.data,
                                 ui_input=lambda m: tk.Entry(m),
                                 ui_edit=lambda m, excl: tk.Entry(m, textvariable=tk.StringVar(m, value=excl.data)),
                                 ui_submit=lambda e: e.get()),
                   ExclusionType(code="before", menu_text="Files modified before a given date",
                                 input_text="Files modified before this date will be excluded (MM/DD/YYYY): ",
                                 function=lambda excl, path: os.path.isfile(path) and datetime.strptime(
                                     excl.data, "%m/%d/%Y") > datetime.fromtimestamp(os.path.getmtime(path)),
                                 ui_input=lambda m: DateEntry(m, date_pattern="mm/dd/y"),
                                 ui_edit=lambda m, excl: DateEntry(
                                     m, date_pattern="mm/dd/y", year=parser.parse(excl.data).year,
                                     month=parser.parse(excl.data).month, day=parser.parse(excl.data).day),
                                 ui_submit=lambda e: e.get_date().strftime("%m/%d/%Y")),
                   ExclusionType(code="after", menu_text="Files modified after a given date",
                                 input_text="Files modified after this date will be excluded (MM/DD/YYYY): ",
                                 function=lambda excl, path: os.path.isfile(path) and datetime.strptime(
                                     excl.data, "%m/%d/%Y") < datetime.fromtimestamp(os.path.getmtime(path)),
                                 ui_input=lambda m: DateEntry(m, date_pattern="mm/dd/y"),
                                 ui_edit=lambda m, excl: DateEntry(
                                     m, date_pattern="mm/dd/y", year=parser.parse(excl.data).year,
                                     month=parser.parse(excl.data).month, day=parser.parse(excl.data).day),
                                 ui_submit=lambda e: e.get_date().strftime("%m/%d/%Y"))]
