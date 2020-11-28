"""
mdbt.py
Author: Michael Pagliaro
The command line argument interface. This is one possible entry-point to the application which allows users
to interface with it by passing command line arguments in order to run different functions of the program.
"""

import sys
import getopt
import itertools
import collections
import shutil
import configuration
import backup
import exclusions
from exclusions import EXCLUSION_TYPES
import limitations
from limitations import LIMITATION_TYPES


class ArgumentException(Exception):
    """
    An exception raised when an argument type is created with illegal data. This should not come up
    during normal execution of the program.
    """
    pass


class ArgumentDoesNotExistException(Exception):
    """
    An exception raised when an argument is given to the application that does not have a type. Most
    errors like these will be caught by getopt, so this will rarely appear.
    """
    pass


class BadDataException(Exception):
    """
    An exception raised when an argument comes in with improperly formatted or invalid data.
    """
    pass


class BadArgumentsException(Exception):
    """
    An exception raised when improper arguments are given. This is usually raised when data arguments
    are required and aren't found.
    """
    pass


class WrapperArgumentException(Exception):
    """
    An exception raised when a wrapper argument is invoked more than once during a single execution.
    """
    pass


class Iterator:
    """
    A wrapper class for an iterator that allows access of the current value.
    """

    def __init__(self, to_iterate):
        """
        Create this type of iterator that can view the current value without advancing the iterator.
        :param to_iterate: The object to iterate over.
        """
        self._iterator = iter(to_iterate)
        self._current = to_iterate[0] if len(to_iterate) > 0 else None

    def __next__(self):
        """
        Increment to the next value. This stores the value to be accessed later.
        :return: The new current value.
        """
        self._current = next(self._iterator)
        return self._current

    def __iter__(self):
        """
        Allows this object to be iterable.
        :return: This object.
        """
        return self

    @property
    def current(self):
        """
        The current value being viewed by the iterator.
        :return: The iterator's current value.
        """
        return self._current


########################################################################################
# Argument Types #######################################################################
########################################################################################


class Argument:
    """
    A basic class representing a type of command line argument. Arguments of this type will have an
    identifying flag, data that goes with that argument, text to help with usage, and a function that is
    called when this argument is used.
    """

    def __init__(self, flag, data, usage, function):
        """
        Creates an argument type.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param data: What data is expected from this argument. This is mainly used in usage text.
        :param usage: Some text to describe this argument in the usage text.
        :param function: A function that will be called when this argument is invoked.
        """
        self._flag = flag
        self._data = data
        self._usage = usage
        self._function = function

    @property
    def flag(self):
        """
        The flag that denotes this argument. This should be unique across all arguments.
        :return: The argument flag as a string.
        """
        return self._flag

    @property
    def data(self):
        """
        What data is expected from this argument. This is mainly used in usage text.
        :return: The argument data description as a string.
        """
        return self._data

    @property
    def usage(self):
        """
        Some text to describe this argument in the usage text.
        :return: The usage text for this argument as a string.
        """
        return self._usage

    @property
    def function(self):
        """
        A function that will be called when this argument is invoked.
        :return: The function object for this argument's function.
        """
        return self._function


class ArgumentEmpty(Argument):
    """
    A special type of argument that takes no data.
    """

    def __init__(self, flag, usage, function):
        """
        Creates the empty argument type. This will call the constructor of Argument, but set the
        data text to None. When this argument is processed, it will not expect data after it on the
        command line.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param usage: Some text to describe this argument in the usage text.
        :param function: A function that will be called when this argument is invoked.
        """
        super().__init__(flag, None, usage, function)


class ArgumentData(Argument):
    """
    A special type of argument that only takes data, and does not invoke a function when it
    is processed.
    """

    def __init__(self, flag, data, usage):
        """
        Creates the data argument type. This will call the constructor of Argument, but set the
        function to None. When this argument is processed, it won't try to make a function call.
        For a better visual indication of data arguments, they will only be allowed to have long
        flag names (2 or more characters in the flag), so if one is created with a one character
        name, an ArgumentException will be raised.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param data: What data is expected from this argument. This is mainly used in usage text.
        :param usage: Some text to describe this argument in the usage text.
        """
        super().__init__(flag, data, usage, None)
        if len(flag) <= 1:
            raise ArgumentException


class ArgumentWrapper(Argument):
    """
    A special type of argument that executes a function before every other type of argument, then
    executes another function after every other argument.
    """

    def __init__(self, flag, data, usage, begin_function, end_function):
        """
        Creates the wrapper argument type. This will call the constructor of argument, but also creates two
        unique fields: a begin_function and an end_function. The function field will be changed as this
        argument gets used throughout the application.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param data: What data is expected from this argument. This is mainly used in usage text.
        :param usage: Some text to describe this argument in the usage text.
        :param begin_function: A function that will be called the first time this argument is invoked.
        :param end_function: A function that will be called the second time this argument is invoked.
        """
        super().__init__(flag, data, usage, begin_function)
        self._begin_function = begin_function
        self._end_function = end_function

    @property
    def function(self):
        """
        Overrides the function property of its parent class. When this wrapper argument is first created, the
        function field is set to begin_function. When this method is called, begin_function will be returned, and
        the function field will now be set to the end_function. If this field is called again, end_function will
        be returned, and the function field will be set to None. Any time it is called after that, it will raise
        a WrapperArgumentException.
        :return: The proper function object depending on how many times this argument was invoked.
        """
        if self._function == self._begin_function:
            self._function = self._end_function
            return self._begin_function
        elif self._function == self._end_function:
            self._function = None
            return self._end_function
        else:
            raise WrapperArgumentException("Argument \"" + self._flag + "\" cannot be invoked more than once.")


########################################################################################
# Argument Functions ###################################################################
# All argument functions should take **kwargs as their only defined parameter, and #####
# return a dictionary of specific values or None.                                  #####
########################################################################################
# Supported inputs: "config": A configuration, "opts": A list of options, ##############
#     "iterator": An iterator with a 'current' field                      ##############
# Supported return values: "config": A configuration, "advance": The number of values ##
#     to increment the iterator by                                                    ##
########################################################################################


def option_input(**kwargs):
    """
    The code run when the input argument is given. This will create a new input path in the configuration
    to a folder or file specified.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    input_data = opts[iterator.current][1]
    configuration.append_input_to_config(config, input_data)


def option_destination(**kwargs):
    """
    The code run when the destination argument is given. This will create a new destination path in the
    configuration for the specified entry.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    :return: An integer under the 'advance' label to indicate how many arguments to advance in the
             argument loop.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    output_data = opts[iterator.current][1]
    next_opt = opts[iterator.current+1]
    next_opt_type = get_argument(next_opt[0])

    # Make sure this is followed by a data argument and extract its data
    if not isinstance(next_opt_type, ArgumentData):
        raise BadArgumentsException("Destination argument should be followed by a data argument for input_index.")
    input_index = next_opt[1]

    # Validate the data from the data argument
    if input_index.isnumeric():
        input_index = int(input_index)
    else:
        raise BadDataException("The input index should be a valid number.")
    if input_index > config.num_entries() or input_index <= 0:
        raise BadDataException("The input index should correspond to a valid entry.")

    # Create the new destination
    configuration.append_output_to_config(config, input_index, output_data)
    return {"advance": 1}


def option_exclusion(**kwargs):
    """
    The code run when the exclusion argument is given. This will create a new exclusion in the
    configuration for the specified entry.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    :return: An integer under the 'advance' label to indicate how many arguments to advance in the
             argument loop.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    exclusion_data = opts[iterator.current][1]
    first_data_opt = opts[iterator.current+1]
    first_opt_type = get_argument(first_data_opt[0])
    second_data_opt = opts[iterator.current+2]
    second_opt_type = get_argument(second_data_opt[0])

    # Make sure this is followed by two data arguments and extract its data
    if not isinstance(first_opt_type, ArgumentData) or not isinstance(second_opt_type, ArgumentData):
        raise BadArgumentsException("Exclusion argument should be followed by two data arguments, first for " +
                                    "input_index and second for exclusion_type.")
    input_index = first_data_opt[1]
    exclusion_code = second_data_opt[1]

    # Validate the data from the data arguments
    if input_index.isnumeric():
        input_index = int(input_index)
    else:
        raise BadDataException("The input index should be a valid number.")
    invalid_exclusion_type = True
    for exclusion_type in EXCLUSION_TYPES:
        if exclusion_code == exclusion_type.code:
            invalid_exclusion_type = False
    if invalid_exclusion_type:
        raise BadDataException("The exclusion type must be a valid exclusion type.")
    if input_index > config.num_entries() or input_index <= 0:
        raise BadDataException("The input index should correspond to a valid entry.")

    # Create the new destination
    config.get_entry(input_index).new_exclusion(exclusion_code, exclusion_data)
    return {"advance": 2}


def option_limitation(**kwargs):
    """
    The code run when the limitation argument is given. This will create a new limitation in the
    configuration for the specified entry and exclusion.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    :return: An integer under the 'advance' label to indicate how many arguments to advance in the
             argument loop.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    limitation_data = opts[iterator.current][1]
    first_data_opt = opts[iterator.current+1]
    first_opt_type = get_argument(first_data_opt[0])
    second_data_opt = opts[iterator.current+2]
    second_opt_type = get_argument(second_data_opt[0])
    third_data_opt = opts[iterator.current+3]
    third_opt_type = get_argument(third_data_opt[0])

    # Make sure this is followed by two data arguments and extract its data
    if not isinstance(first_opt_type, ArgumentData) or not isinstance(second_opt_type, ArgumentData) \
            or not isinstance(third_opt_type, ArgumentData):
        raise BadArgumentsException("Limitation argument should be followed by three data arguments, first for " +
                                    "input_index, second for exclusion_index, last for limitation_type.")
    input_index = first_data_opt[1]
    exclusion_index = second_data_opt[1]
    limitation_code = third_data_opt[1]

    # Validate the data from the data arguments
    if input_index.isnumeric() and exclusion_index.isnumeric():
        input_index = int(input_index)
        exclusion_index = int(exclusion_index)
    else:
        raise BadDataException("The input index and exclusion index should be valid numbers.")
    invalid_limitation_type = True
    for limitation_type in LIMITATION_TYPES:
        if limitation_code == limitation_type.code:
            invalid_limitation_type = False
    if invalid_limitation_type:
        raise BadDataException("The limitation type must be a valid limitation type.")
    if input_index > config.num_entries() or input_index <= 0:
        raise BadDataException("The input index should correspond to a valid entry.")
    if exclusion_index > config.get_entry(input_index).num_exclusions() or exclusion_index <= 0:
        raise BadDataException("The exclusion index should correspond to a valid exclusion.")

    # Create the new destination
    config.get_entry(input_index).get_exclusion(exclusion_index).add_limitation(limitation_code, limitation_data)
    return {"advance": 3}


def option_edit(**kwargs):
    """
    The code to run when the edit argument is given. This determines what data is being edited by how many
    data arguments follow this argument. First, this argument takes some data that the target will change to.
    After that, if 1 data argument is given with an integer index, the corresponding input path is changed.
    If 2 data arguments are given, both with integer indexes, the corresponding destination path is changed.
    If 3 data arguments are given, the first two with integer indexes and the third with a 1, the corresponding
    exclusion's type is changed. If the third is a 2, the corresponding exclusion's data is changed.
    If 4 data arguments are given, the first three with integer indexes and the fourth with a 1, the corresponding
    limitation's type is changed. If the fourth is a 2, the corresponding limitation's data is changed.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    :return: An integer under the 'advance' label to indicate how many arguments to advance in the
             argument loop.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    original_index = iterator.current
    new_data = opts[original_index][1]

    # Calculate the number of data arguments that follow this
    num_data_args = 0
    current_idx = original_index + 1
    while current_idx < len(opts):
        if isinstance(get_argument(opts[current_idx][0]), ArgumentData):
            num_data_args += 1
            current_idx += 1
        else:
            break
    if num_data_args <= 0 or num_data_args > 4:
        raise BadArgumentsException("The edit argument requires between 1 and 4 arguments.")

    # Edit an input path
    if num_data_args == 1:
        configuration.edit_input_in_config(config, int(opts[original_index+1][1]), new_data)
    # Edit a destination path
    elif num_data_args == 2:
        configuration.edit_destination_in_config(config.get_entry(int(opts[original_index+1][1])),
                                                 int(opts[original_index+2][1]), new_data, config)
    # Edit an exclusion
    elif num_data_args == 3:
        # Edit an exclusion's type
        if int(opts[original_index+3][1]) == 1:
            if exclusions.is_valid_exclusion_type(new_data):
                config.get_entry(int(opts[original_index+1][1])).get_exclusion(int(opts[original_index+2][1])).code \
                    = new_data
            else:
                raise BadDataException("When editing an exclusion's type, you must provide a valid exclusion type.")
        # Edit an exclusion's data
        elif int(opts[original_index+3][1]) == 2:
            config.get_entry(int(opts[original_index+1][1])).get_exclusion(int(opts[original_index+2][1])).data \
                = new_data
        else:
            raise BadDataException("When editing an exclusion, the last argument must be 1 or 2.")
    # Edit a limitation
    elif num_data_args == 4:
        # Edit a limitation's type
        if int(opts[original_index+4][1]) == 1:
            if limitations.is_valid_limitation_type(new_data):
                config.get_entry(int(opts[original_index+1][1])).get_exclusion(int(opts[original_index+2][1])) \
                    .get_limitation(int(opts[original_index+3][1])).code = new_data
            else:
                raise BadDataException("When editing a limitation's type, you must provide a valid limitation type.")
        # Edit a limitation's data
        elif int(opts[original_index+4][1]) == 2:
            config.get_entry(int(opts[original_index+1][1])).get_exclusion(int(opts[original_index+2][1])) \
                .get_limitation(int(opts[original_index+3][1])).data = new_data
        else:
            raise BadDataException("When editing a limitation, the last argument must be 1 or 2.")
    return {"advance": num_data_args}


def option_delete(**kwargs):
    """
    The code that runs when the delete argument is given. Using the given delete mode, either "entry",
    "destination", "exclusion", or "limitation", it parses the following data arguments to get the index
    of the object to delete. For entry mode, just the entry index is required. For destination mode, the
    entry index and the destination index are required. For exclusion mode, the entry index and the
    exclusion index are required. For limitation mode, the entry index, exclusion index, and limitation
    index are required.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    :return: An integer under the 'advance' label to indicate how many arguments to advance in the
             argument loop.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    original_index = iterator.current
    delete_mode = opts[original_index][1]

    # Calculate the number of data arguments that follow this
    num_data_args = 0
    current_idx = original_index + 1
    while current_idx < len(opts):
        if isinstance(get_argument(opts[current_idx][0]), ArgumentData):
            num_data_args += 1
            current_idx += 1
        else:
            break

    # Validate the delete mode and the needed number of data arguments
    if delete_mode == "entry" and not num_data_args == 1:
        raise BadArgumentsException("The delete argument using entry mode requires 1 data argument.")
    elif delete_mode == "destination" and not num_data_args == 2:
        raise BadArgumentsException("The delete argument using destination mode requires 2 data arguments.")
    elif delete_mode == "exclusion" and not num_data_args == 2:
        raise BadArgumentsException("The delete argument using exclusion mode requires 2 data arguments.")
    elif delete_mode == "limitation" and not num_data_args == 3:
        raise BadArgumentsException("The delete argument using limitation mode requires 3 data arguments.")
    elif not delete_mode == "entry" and not delete_mode == "destination" and not delete_mode == "exclusion" and \
            not delete_mode == "limitation":
        raise BadDataException(delete_mode + " is an invalid delete mode.")

    # Delete an entry
    if delete_mode == "entry":
        if 0 < int(opts[original_index+1][1]) <= config.num_entries():
            config.delete_entry(int(opts[original_index+1][1]))
        else:
            raise BadDataException("You must provide valid indexes for the entry to delete.")
    # Delete a destination
    elif delete_mode == "destination":
        if 0 < int(opts[original_index+1][1]) <= config.num_entries() and 0 < int(opts[original_index+2][1]) \
                <= config.get_entry(int(opts[original_index+1][1])).num_destinations():
            config.get_entry(int(opts[original_index+1][1])).delete_destination(int(opts[original_index+2][1]))
        else:
            raise BadDataException("You must provide valid indexes for the destination to delete.")
    # Delete an exclusion
    elif delete_mode == "exclusion":
        if 0 < int(opts[original_index+1][1]) <= config.num_entries() and 0 < int(opts[original_index+2][1]) \
                <= config.get_entry(int(opts[original_index+1][1])).num_exclusions():
            config.get_entry(int(opts[original_index+1][1])).delete_exclusion(int(opts[original_index+2][1]))
        else:
            raise BadDataException("You must provide valid indexes for the exclusion to delete.")
    # Delete a limitation
    elif delete_mode == "limitation":
        if 0 < int(opts[original_index+1][1]) <= config.num_entries() and 0 < int(opts[original_index+2][1]) \
                <= config.get_entry(int(opts[original_index+1][1])).num_exclusions() and 0 < \
                int(opts[original_index+3][1]) <= config.get_entry(int(opts[original_index+1][1])).get_exclusion(
                int(opts[original_index+2][1])).num_limitations():
            config.get_entry(int(opts[original_index+1][1])).get_exclusion(int(opts[original_index+2][1])) \
                .delete_limitation(int(opts[original_index+3][1]))
        else:
            raise BadDataException("You must provide valid indexes for the limitation to delete.")
    return {"advance": num_data_args}


def option_save(**kwargs):
    """
    The code run when the save argument is given. This will save the given configuration to a file with the
    name given with this argument.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    config_name = opts[iterator.current][1]
    old_config_name = config.name
    config.name = config_name
    try:
        configuration.save_config(config, config_name)
    except FileNotFoundError:
        print("\nERROR: The name \"" + config_name + "\" is not a valid configuration name.")
        config.name = old_config_name


def option_load(**kwargs):
    """
    The code run when the load argument is given. This will load the configuration of a given name and return it.
    :param kwargs: A dictionary of arguments. This expects 'opts' as a list of options created by getopt and
                   'iterator' as the current iterator being used.
    :return: The new configuration object returned in a dictionary with the key 'config'.
    """
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    config_name = opts[iterator.current][1]
    print("Loading {}.dat...".format(config_name))
    return {"config": configuration.load_config(config_name)}


def option_backup(**kwargs):
    """
    The code run when the backup argument is given. This will pass the configuration to the backup module
    to run the backup process.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration.
    """
    backup.run_backup(kwargs["config"])


def option_print(**kwargs):
    """
    The code run when the print argument is given. This will display the given configuration.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration.
    """
    print("\nCalculating file sizes...", end="\r", flush=True)
    print(configuration.config_display_string(kwargs["config"], show_exclusions=True))


def option_print_ext_types(**kwargs):
    """
    The code run when the print exclusion types argument is given. This will display a list of any valid
    exclusion type along with a description of each.
    :param kwargs: A dictionary of arguments. None are needed for this function.
    """
    for exclusion_type in EXCLUSION_TYPES:
        input_text = exclusion_type.input_text
        if len(input_text) > 2 and input_text[-1] == ' ' and input_text[-2] == ':':
            input_text = input_text[:len(input_text)-2]
        print("{} - {}".format(exclusion_type.code, input_text))


def option_print_lim_types(**kwargs):
    """
    The code run when the print limitation types argument is given. This will display a list of any valid
    limitation type along with a description of each.
    :param kwargs: A dictionary of arguments. None are needed for this function.
    """
    for limitation_type in LIMITATION_TYPES:
        input_text = limitation_type.input_text
        if len(input_text) > 2 and input_text[-1] == ' ' and input_text[-2] == ':':
            input_text = input_text[:len(input_text) - 2]
        print("{} - {}".format(limitation_type.code, input_text))


def option_help(**kwargs):
    """
    The code run when the help argument is given. This simply displays the usage text.
    :param kwargs: A dictionary of arguments. None are needed for this function.
    """
    display_usage()


########################################################################################
# Arguments ############################################################################
# All arguments used by this application are defined here. #############################
########################################################################################


ARGUMENT_FLAGS = [Argument("i", "input_path", "A path that will be a source for a backup.", option_input),
                  Argument("d", "destination_path", "A path that will be a destination for an input. Should be " +
                           "followed by --data <input_index>.", option_destination),
                  Argument("e", "exclusion_data", "Data that will be used in an exclusion. Should be followed by " +
                           "two data arguments, first for <input_index> then for <exclusion_type>.", option_exclusion),
                  Argument("t", "limitation_data", "Data that will be used in an limitation. Should be followed by " +
                           "three data arguments, first for <input_index>, then for <exclusion_index>, last for " +
                           "<limitation_type>.", option_limitation),
                  Argument("m", "new_data", "Modify data in the configuration. You first give it the data you want " +
                           "to change something to, then the number of following data arguments determines what is " +
                           "being changed. One data argument with an index changes an input path. Two data arguments " +
                           "both with indexes changes a destination path. Three data arguments, the first two with " +
                           "indexes and the third with a 1 changes an exclusion's type, making the third a 2 changes " +
                           "an exclusion's data. Four data arguments, the first three with indexes and the fourth " +
                           "with a 1 changes a limitation's type, making the fourth a 2 changes a limitation's data.",
                           option_edit),
                  Argument("x", "delete_mode", "Delete something in the configuration. You must first specify a " +
                           "mode, basically what you want to delete, right after this argument. Options are \"" +
                           "entry\", \"destination\", \"exclusion\", and \"limitation\". After each, you must " +
                           "provide data arguments to give all the information of what to delete. After \"entry" +
                           "\", use one data argument to give the index of the entry to delete. After \"destination" +
                           "\", use two data arguments to give the entry index and destination index. After " +
                           "\"exclusion\", use two data arguments to give the entry index and exclusion index. After " +
                           "\"limitation\", use three data arguments to give the entry index, exclusion index, and " +
                           "limitation index.", option_delete),
                  Argument("s", "config_name", "A name to save this configuration as.", option_save),
                  Argument("l", "config_name", "The name of a saved configuration to load.", option_load),
                  ArgumentWrapper("c", "config_name", "Load this config at the start and save it at the end.",
                                  option_load, option_save),
                  ArgumentEmpty("b", "Run a backup on the current configuration.", option_backup),
                  ArgumentEmpty("p", "Print the current configuration.", option_print),
                  ArgumentEmpty("q", "Print all valid exclusion types.", option_print_ext_types),
                  ArgumentEmpty("r", "Print all valid limitation types.", option_print_lim_types),
                  ArgumentEmpty("h", "Display this help text.", option_help),
                  ArgumentData("data", "value", "A data argument. Some arguments above must be followed by one or " +
                               "more of these, with specific data requirements.")]


########################################################################################
# Utility Functions and Main ###########################################################
# Below are any utility functions for the main program and the main function itself. ###
########################################################################################


def display_usage():
    """
    Displays the usage text of this application.
    """
    print("Usage: mdbt.py [combination of flags below]")
    console_width, _ = shutil.get_terminal_size((80, 20))
    for arg in ARGUMENT_FLAGS:
        prefix = "--" if len(arg.flag) > 1 else "-"
        print(' ' * 4 + ("{}{}:".format(prefix, arg.flag) if arg.data is None
              else "{}{} <{}>:".format(prefix, arg.flag, arg.data)))
        usage_words = arg.usage.split(' ')
        chars_used = int(console_width / 6)
        print(' ' * chars_used, end='')
        for word in usage_words:
            if chars_used + len(word) + 2 > console_width:
                chars_used = int(console_width / 6)
                print('\n' + ' ' * chars_used, end='')
            chars_used += len(word) + 1
            print(word + ' ', end='')
        print()
    print("\nExample of a command requiring multiple data arguments (exclusion command):")
    print("  python mdbt.py -e \"abc\" --data 1 --data \"startswith\"")


def get_argument(flag):
    """
    Given an argument flag from the command line, this finds the argument object that contains all data
    about that argument. The flag passed in is expected to be prefaced with a hyphen, for example '-b'
    or '--di'. If no argument exists with the given flag, it will raise an ArgumentDoesNotExistException.
    :param flag: A flag to find its corresponding argument as a string.
    :return: The argument object with a matching flag property.
    """
    flag_value = flag[1:] if len(flag) <= 2 else flag[2:]
    for arg in ARGUMENT_FLAGS:
        if flag_value == arg.flag:
            return arg
    raise ArgumentDoesNotExistException


def extract_opt_type(opts, arg_type):
    """
    Loop through a list of options and take any options of a given argument type and put them into a
    separate list. These options in the new list will be removed from the original list.
    :param opts: A list of options created by getopt.
    :param arg_type: An argument class to extract from the list.
    :return: A list of arg_type options that used to be in the original list. The opts list will be
             modified by reference.
    """
    opts_type = []
    wrapper_opt_idxs = []
    for opt_idx in range(len(opts)):
        argument = get_argument(opts[opt_idx][0])
        if isinstance(argument, arg_type):
            opts_type.append(opts[opt_idx])
            wrapper_opt_idxs.append(opt_idx)
    for opt_idx in reversed(wrapper_opt_idxs):
        del opts[opt_idx]
    return opts_type


def argument_loop(config, opts):
    """
    Loops through a list of command line arguments parsed by getopt and processes the function and data
    associated with each one.
    :param config: The current configuration.
    :param opts: A list of options created by getopt.
    :return: The configuration, which can be modified.
    """
    iterator = Iterator(range(len(opts)))
    for opt_idx in iterator:
        opt = opts[opt_idx][0]
        argument = get_argument(opt)

        # Raise exception if trying to process data argument, otherwise run the argument's function
        if isinstance(argument, ArgumentData):
            raise BadArgumentsException("Data argument \"" + argument.flag + "\" found when not required.")
        else:
            return_vals = argument.function(config=config, opts=opts, iterator=iterator)

            # Process return values, to add new supported return values add new if statements here
            if return_vals is not None:
                for key, value in return_vals.items():
                    if key == "config":
                        config = value
                    elif key == "advance":
                        collections.deque(itertools.islice(iterator, value))
    return config


def main(argv):
    """
    The main entry-point for this command line argument interface. This will check which arguments were entered
    and run the appropriate functions for each.
    """
    # Display usage text if no arguments are given
    if len(argv) == 0:
        display_usage()
        sys.exit(2)

    # Prepare the configuration and things for getopt
    config = configuration.Configuration()
    getopt_options = ""
    getopt_long_options = []

    # Build the option string and list for getopt
    for arg in ARGUMENT_FLAGS:
        if len(arg.flag) > 1:
            getopt_long_options.append(arg.flag + "=")
        else:
            getopt_options += arg.flag + ("" if isinstance(arg, ArgumentEmpty) else ":")

    # Read in the arguments with getopt
    try:
        opts, args = getopt.getopt(argv, getopt_options, getopt_long_options)
    except getopt.GetoptError as ge:
        print("There was an error in the arguments you entered.")
        print(ge.msg)
        display_usage()
        sys.exit(2)

    # Extract wrapper arguments from the main list and ensure none are called more than once
    wrapper_opts = extract_opt_type(opts, ArgumentWrapper)
    for outer_idx in range(len(wrapper_opts)):
        for inner_idx in range(len(wrapper_opts)):
            if outer_idx != inner_idx:
                if wrapper_opts[outer_idx][0] == wrapper_opts[inner_idx][0]:
                    raise BadArgumentsException("Cannot use the same type of wrapper argument twice.")

    # Run the begin function of every wrapper argument
    config = argument_loop(config, wrapper_opts)

    # Loop through the main argument list
    config = argument_loop(config, opts)

    # Run the end function of every wrapper argument
    argument_loop(config, wrapper_opts)


if __name__ == "__main__":
    main(sys.argv[1:])
