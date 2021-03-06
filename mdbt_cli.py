"""
mdbt_cli.py
Author: Michael Pagliaro
The command line interface. This is one possible entry-point to the application which presents users
with menus and options on the command line.
"""

import configuration
from entry import MAX_OUTPUTS, MAX_EXCLUSIONS
from configuration import InvalidPathException, SubPathException, CyclicEntryException
from exclusions import EXCLUSION_TYPES, MAX_LIMITATIONS
from limitations import LIMITATION_TYPES
import util
import backup


def input_menu(options, input_text="Choose an option: "):
    """
    Input loop for selecting an option in a menu. Given a list of strings that represent the options on this
    menu, this will prompt for input, and loop back around if a non-integer value is entered or a value that
    doesn't correspond to a menu option. Once a valid value is entered, it is returned as an integer.
    :param options: A list of strings that will be enumerated and displayed as options.
    :param input_text: The text the appears as the prompt for user input. This defaults to "Choose an option: ".
    :return: The valid number that was entered as an integer.
    """
    while True:
        print()
        for option_idx in range(1, len(options)+1):
            print("{}: {}".format(option_idx, options[option_idx-1]))
        user_input = input(input_text)
        try:
            user_int = int(user_input)
            if user_int < 1 or user_int > len(options):
                print("Invalid input.")
            else:
                return user_int
        except ValueError:
            print("Invalid input.")


def input_entry_number(low_bound, high_bound, input_text="Enter a number to select that entry: ",
                       error_text="Invalid input, no entry exists with that number"):
    """
    Input loop for finding an entry number. Given a lower and higher bound, this will continue
    asking for user input until a valid number is entered.
    :param low_bound: The lowest number that can be accepted (inclusive).
    :param high_bound: The highest number that can be accepted (inclusive).
    :param input_text: Text that will display before the input prompt.
    :param error_text: Text that will display if an invalid value is input.
    :return: A valid value that the user inputs.
    """
    while True:
        entry_number = input(input_text)
        try:
            entry_int = int(entry_number)
            if entry_int < low_bound or entry_int > high_bound:
                print(error_text)
            else:
                return entry_int
        except ValueError:
            print("Invalid input.")


def menu_option_input(config):
    """
    The code that is run when the menu option for selecting a new folder to backup is selected.
    This will accept user input until a valid file or folder path is input.
    :param config: The current backup configuration.
    """
    if config.num_entries() >= configuration.MAX_ENTRIES:
        print("The maximum number of entries has been reached, you are unable to create more.")
        return
    result = False
    while not result:
        # Accept user input for path to directory or file
        input_name = input("Enter the absolute path of a folder or file to backup (enter \"end\" to stop): ")
        if input_name == "end":
            break
        # Check if the input is valid, and if so add it to the config, otherwise display what went wrong
        try:
            configuration.append_input_to_config(config, input_name)
            break
        except (InvalidPathException, CyclicEntryException) as error:
            print(error)


def menu_option_destination(config):
    """
    The code that is run when the menu option for entering a new destination path is selected.
    This will prompt the user to choose an entry, then allow them to enter directory paths until
    they specify when to stop.
    :param config: The current backup configuration.
    """
    # Display a list of entries in the configuration
    print(config.enumerate_entries())
    # Accept input to select one of those entries (or all at once)
    entry_number = input_entry_number(low_bound=0, high_bound=config.num_entries(),
                                      input_text="Enter a number to specify that entry's destinations " +
                                                 "(or 0 to modify all at once): ")
    # Input loop: Enter paths to send this folder to
    print("Enter the absolute paths of each destination, separated by the Enter key (enter \"end\" to stop)")
    while True:
        if entry_number == 0:
            for entry_number_loop in range(1, config.num_entries() + 1):
                if config.get_entry(entry_number_loop).num_destinations() >= MAX_OUTPUTS:
                    print("The maximum number of destinations has been reached for entry "
                          "{}, you are unable to create more.".format(entry_number_loop))
                    return
        else:
            if config.get_entry(entry_number).num_destinations() >= MAX_OUTPUTS:
                print("The maximum number of destinations has been reached for entry {}, you are unable to create more."
                      .format(entry_number))
                return
        destination_input = input()
        if destination_input == "end":
            break
        try:
            configuration.append_output_to_config(config, entry_number, destination_input)
        except (InvalidPathException, SubPathException, CyclicEntryException) as error:
            print(error)


def menu_option_exclude(config):
    """
    The code that is run when the menu option for adding an exclusion is selected. This will prompt the
    user to choose an entry, then allow them to enter an exclusion of one of a variety of types.
    :param config: The current backup configuration.
    """
    # Display a list of entries in the configuration
    print(config.enumerate_entries())
    # Accept input to select one of those entries
    entry_number = input_entry_number(low_bound=1, high_bound=config.num_entries(),
                                      input_text="Enter a number to add an exclusion to that entry: ")
    entry = config.get_entry(entry_number)

    # If exclusions already exist on this entry, ask if the user would like to instead create limitations
    if entry.num_exclusions() > 0:
        starting_input = input_menu(["Create a new exclusion", "Add a limitation to an existing exclusion",
                                     "Return to the previous menu"])
        if starting_input == 2:
            sub_option_limitations(entry)
            return
        elif starting_input == 3:
            return

    # Once chosen, display options to add different types of exclusions
    while True:
        # Return if the maximum number of exclusions has been reached
        if config.get_entry(entry_number).num_exclusions() >= MAX_EXCLUSIONS:
            print("The maximum number of exclusions has been reached for entry {}, you are unable to create more."
                  .format(entry_number))
            return

        print()
        print(entry.to_string(exclusion_mode=True))
        exclusion_codes = [item.code for item in EXCLUSION_TYPES]
        exclusion_menu_options = [item.menu_text for item in EXCLUSION_TYPES]
        exclusion_input_messages = [item.input_text for item in EXCLUSION_TYPES]
        exclusion_menu_options.append("Return to the menu")
        exclusion_input = input_menu(exclusion_menu_options)

        # If it's a valid exclusion, take input for it
        if 1 <= exclusion_input <= len(exclusion_codes):
            exclusion_data = input(exclusion_input_messages[exclusion_input-1])
            entry.new_exclusion(exclusion_codes[exclusion_input-1], exclusion_data)
        # Return to the menu
        elif exclusion_input == len(exclusion_codes)+1:
            break


def sub_option_limitations(entry):
    """
    The code that is run when the sub-option for adding a limitation is selected. This will prompt the
    user to choose an exclusion, then allow them to enter a limitation of one of a variety of types.
    :param entry: An entry from the configuration that's currently being added to.
    """
    # Display a list of exclusions in the entry
    print("\n" + entry.enumerate_exclusions())
    # Accept input to select one of those exclusions
    excl_number = input_entry_number(low_bound=1, high_bound=entry.num_exclusions(),
                                     input_text="Enter a number to add a limitation to that exclusion: ")
    exclusion = entry.get_exclusion(excl_number)

    # Once chosen, display options to add different types of limitations
    while True:
        # Return if the maximum number of limitations has been reached
        if exclusion.num_limitations() >= MAX_LIMITATIONS:
            print("The maximum number of limitations has been reached for exclusion {}, you are unable to create more."
                  .format(excl_number))
            return

        print()
        print(exclusion.to_string(include_limitations=True, entry_input=entry.input))
        limitation_codes = [item.code for item in LIMITATION_TYPES]
        limitation_menu_options = [item.menu_text for item in LIMITATION_TYPES]
        limitation_input_messages = [item.input_text for item in LIMITATION_TYPES]
        limitation_menu_options.append("Return to the menu")
        limitation_input = input_menu(limitation_menu_options)

        # If it's a valid limitation, take input for it
        if 1 <= limitation_input <= len(limitation_codes):
            limitation_data = input(limitation_input_messages[limitation_input-1])
            exclusion.add_limitation(limitation_codes[limitation_input-1], limitation_data)
        # Return to the menu
        elif limitation_input == len(limitation_codes)+1:
            break


def menu_option_edit(config):
    """
    The code that is run when the menu option for editing the configuration is selected. This will allow
    the user to choose an entry, then display a menu that will allow the user to edit that entry's input
    path, edit its destinations, edit its exclusions, delete all its destinations, delete all its exclusions,
    delete the entire entry, or return to the previous menu.
    :param config: The current backup configuration.
    """
    # Display a list of entries in the configuration
    print(config.enumerate_entries())
    # Accept input to select one of those entries
    entry_number = input_entry_number(low_bound=1, high_bound=config.num_entries(),
                                      input_text="Enter a number to edit or delete that entry: ")
    entry = config.get_entry(entry_number)

    # Once chosen, display options to edit or delete this entry
    while True:
        print()
        print(entry.to_string())
        edit_input = input_menu(["Edit the input path",
                                 "Edit the destinations",
                                 "Edit the exclusions",
                                 "Delete all destinations",
                                 "Delete all exclusions",
                                 "Delete this entire entry",
                                 "Return to the menu"])

        # Edit the input path
        if edit_input == 1:
            while True:
                input_name = input("Enter the new absolute path of a folder or file to backup: ")
                try:
                    configuration.edit_input_in_config(config, entry_number, input_name)
                    break
                except (InvalidPathException, SubPathException, CyclicEntryException) as error:
                    print(error)
        # Edit the destinations
        elif edit_input == 2:
            if entry.num_destinations() > 0:
                sub_option_edit_destinations(config, entry)
            else:
                print("There are no destinations to edit or delete.")
                continue
        # Edit the exclusions
        elif edit_input == 3:
            if entry.num_exclusions() > 0:
                sub_option_edit_exclusions(entry)
            else:
                print("There are no exclusions to edit or delete.")
                continue
        # Delete all destinations
        elif edit_input == 4:
            del entry.outputs
        # Delete all exclusions
        elif edit_input == 5:
            del entry.exclusions
        # Delete this entry
        elif edit_input == 6:
            config.delete_entry(entry_number)
            break
        # Return to the previous menu
        elif edit_input == 7:
            break


def sub_option_edit_destinations(config, entry):
    """
    The code that is run when the sub-option for editing the destinations of an entry is selected.
    This will display a menu, allowing the user to choose to edit a destination, delete a destination,
    or return to the previous menu.
    :param config: The current configuration.
    :param entry: An entry from the configuration that's currently being edited.
    """
    while True:
        destination_input = input_menu(["Edit a destination",
                                        "Delete a destination",
                                        "Return to the previous menu"])

        # Edit destination
        if destination_input == 1:
            print("\n" + entry.enumerate_destinations())
            dest_number = input_entry_number(low_bound=1, high_bound=entry.num_destinations(),
                                             input_text="Enter a number to specify which destination to edit: ")
            while True:
                input_name = input("Enter the new absolute path of a folder to make a destination: ")
                try:
                    configuration.edit_destination_in_config(entry, dest_number, input_name, config)
                    break
                except (InvalidPathException, SubPathException, CyclicEntryException) as error:
                    print(error)
        # Delete destination
        elif destination_input == 2:
            print("\n" + entry.enumerate_destinations())
            dest_number = input_entry_number(low_bound=1, high_bound=entry.num_destinations(),
                                             input_text="Enter a number to specify which destination to delete: ")
            entry.delete_destination(dest_number)
            # Go to the previous menu if the last destination is deleted
            if entry.num_destinations() == 0:
                break
        # Return to the previous menu
        elif destination_input == 3:
            break


def sub_option_edit_exclusions(entry):
    """
    The code that is run when the sub-option for editing the exclusions of an entry is selected.
    This will display a menu, allowing the user to choose to edit an exclusion, delete an exclusion,
    or return to the previous menu.
    :param entry: An entry from the configuration that's currently being edited.
    """
    while True:
        print("\n" + entry.to_string(exclusion_mode=True))
        exclusion_input = input_menu(["Edit an exclusion",
                                      "Delete an exclusion",
                                      "Return to the previous menu"])

        # Edit exclusion
        if exclusion_input == 1:
            print("\n" + entry.enumerate_exclusions())
            excl_number = input_entry_number(low_bound=1, high_bound=entry.num_exclusions(),
                                             input_text="Enter a number to specify which exclusion to edit: ")
            exclusion = entry.get_exclusion(excl_number)

            while True:
                # Create the exclusion editing menu
                excl_edit_menu = ["Change the exclusion type",
                                  "Change the exclusion data",
                                  "Edit the limitations",
                                  "Delete all limitations",
                                  "Return to the previous menu"]
                excl_edit_input = input_menu(excl_edit_menu)

                # Change exclusion type
                if excl_edit_input == 1:
                    exclusion_codes = [item.code for item in EXCLUSION_TYPES]
                    exclusion_menu_options = [item.menu_text for item in EXCLUSION_TYPES]
                    new_exclusion_input = input_menu(exclusion_menu_options,
                                                     input_text="Choose one of these options to change the type to: ")
                    exclusion.code = exclusion_codes[new_exclusion_input-1]
                # Change exclusion data
                elif excl_edit_input == 2:
                    exclusion_codes = [item.code for item in EXCLUSION_TYPES]
                    exclusion_input_messages = [item.input_text for item in EXCLUSION_TYPES]
                    input_message = "Enter the new data for this exclusion: "
                    for exclusion_type_idx in range(len(exclusion_codes)):
                        if exclusion_codes[exclusion_type_idx] == exclusion.code:
                            input_message = exclusion_input_messages[exclusion_type_idx]
                    new_data = input(input_message)
                    exclusion.data = new_data
                # Edit limitations
                elif excl_edit_input == 3:
                    if exclusion.has_limitations():
                        sub_option_edit_limitations(exclusion, entry.input)
                    else:
                        print("There are no limitations on this exclusion to edit.")
                # Delete all limitations
                elif excl_edit_input == 4:
                    del exclusion.limitations
                # Return to the previous menu
                elif excl_edit_input == 5:
                    break
        # Delete exclusion
        elif exclusion_input == 2:
            print("\n" + entry.enumerate_exclusions())
            excl_number = input_entry_number(low_bound=1, high_bound=entry.num_exclusions(),
                                             input_text="Enter a number to specify which exclusion to delete: ")
            entry.delete_exclusion(excl_number)
            # Go to the previous menu if the last exclusion is deleted
            if entry.num_exclusions() == 0:
                break
        # Return to the previous menu
        elif exclusion_input == 3:
            break


def sub_option_edit_limitations(exclusion, entry_input):
    """
    The code that is run when the sub-option for editing the limitations of an exclusion is selected.
    This will display a menu allowing the user to edit the type or data of any of the limitations, or delete
    any of them.
    :param exclusion: The current exclusion whose limitation is being edited.
    :param entry_input: The input field from the corresponding entry, used for shortening limitation data paths.
    """
    while True:
        print("\n" + exclusion.to_string(include_limitations=True, entry_input=entry_input))
        limitation_input = input_menu(["Edit a limitation",
                                       "Delete a limitation",
                                       "Return to the previous menu"])

        # Edit limitation
        if limitation_input == 1:
            print("\n" + exclusion.enumerate_limitations(entry_input=entry_input))
            limit_number = input_entry_number(low_bound=1, high_bound=exclusion.num_limitations(),
                                              input_text="Enter a number to specify which limitation to edit: ")
            limitation = exclusion.get_limitation(limit_number)

            while True:
                limit_edit_input = input_menu(["Change the limitation type",
                                               "Change the limitation data",
                                               "Return to the previous menu"])

                # Change limitation type
                if limit_edit_input == 1:
                    limitation_codes = [item.code for item in LIMITATION_TYPES]
                    limitation_menu_options = [item.menu_text for item in LIMITATION_TYPES]
                    while True:
                        new_limitation_input = input_menu(limitation_menu_options,
                                                          input_text="Choose an option to change the type to: ")
                        if not exclusion.accepts_limitations() and not \
                                LIMITATION_TYPES[new_limitation_input-1].always_applicable:
                            print("This limitation is not allowed with this type of exclusion.")
                        else:
                            break
                    limitation.code = limitation_codes[new_limitation_input-1]
                # Change limitation data
                elif limit_edit_input == 2:
                    limitation_codes = [item.code for item in LIMITATION_TYPES]
                    limitation_input_messages = [item.input_text for item in LIMITATION_TYPES]
                    input_message = "Enter the new data for this limitation: "
                    for limitation_type_idx in range(len(limitation_codes)):
                        if limitation_codes[limitation_type_idx] == exclusion.get_limitation(1).code:
                            input_message = limitation_input_messages[limitation_type_idx]
                    new_data = input(input_message)
                    limitation.data = new_data
                # Return to the previous menu
                elif limit_edit_input == 3:
                    break
        # Delete limitation
        elif limitation_input == 2:
            print("\n" + exclusion.enumerate_limitations())
            limit_number = input_entry_number(low_bound=1, high_bound=exclusion.num_limitations(),
                                              input_text="Enter a number to specify which limitation to delete: ")
            exclusion.delete_limitation(limit_number)
            # Go to the previous menu if the last limitation is deleted
            if exclusion.num_limitations() == 0:
                break
        # Return to the previous menu
        elif limitation_input == 3:
            break


def menu_option_save(config):
    """
    The code that is run when the menu option for saving the current configuration is selected.
    This will prompt the user for a name, then save the configuration to a file.
    :param config: The current backup configuration.
    """
    # Input: Give a name to this configuration
    config_name = input("Enter a name for this configuration: ")
    # Pass the config and the name to the save function (ask to overwrite if the name exists)
    overwrite = "y"
    if configuration.config_exists(config_name):
        overwrite = input("Would you like to overwrite this existing configuration? (y/n): ")
    if overwrite.lower() == "y":
        old_config_name = config.name
        config.name = config_name
        try:
            configuration.save_config(config, config_name)
        except FileNotFoundError:
            print("\nERROR: The name \"" + config_name + "\" is not a valid configuration name.")
            config.name = old_config_name


def menu_option_load(config, config_list):
    """
    The code that is run when the menu option for loading a configuration from a file is selected.
    This will show the user the configurations they can load, then prompt for input on which to load.
    :param config: The current backup configuration.
    :param config_list: A string listing all the possible configurations that can be loaded.
    :return: The newly loaded configuration.
    """
    print("List of available saved configurations:")
    print(config_list)
    while True:
        # Once a valid name is entered, load that configuration
        config_name = input("Enter a name of a configuration to load (enter \"end\" to return to the menu): ")
        if config_name == "end":
            break
        elif configuration.config_exists(config_name):
            config = configuration.load_config(config_name)
            break
        else:
            print("{} is an invalid configuration name.".format(config_name))
    return config


def menu_option_backup(config):
    """
    The code that is run when the menu option for backing up the selected files is selected.
    This will ask for confirmation before beginning, and then run the backup process.
    :param config: The current backup configuration.
    """
    # Do not continue if one of the paths in the configuration no longer exists
    if not config.all_paths_are_valid():
        print("At least one of the input or output paths in this configuration is no longer valid.")
        print("Please ensure all relevant drives are plugged in, or edit any invalid paths.")
    else:
        # If this configuration is new or was modified, ask to save it
        if config.name is None:
            save_input = input("Your configuration has not been saved yet. Would you like to save it? (y/n): ")
            if save_input.lower() == "y":
                menu_option_save(config)
        elif configuration.config_was_modified(config):
            save_input = input("This configuration has changed since it was last saved. " +
                               "Would you like to update it? (y/n): ")
            if save_input.lower() == "y":
                configuration.save_config(config, config.name)

        # Ask to confirm if this is ok to backup
        backup_confirmation = input("Would you like to start the backup with this configuration? (y/n): ")
        # If yes, run the backup
        if backup_confirmation.lower() == "y":
            backup.run_backup(config)


def main():
    """
    The main entry-point for this command line interface. This runs a loop that accepts user
    commands and handles input in a variety of ways.
    """
    config = configuration.Configuration()
    while True:
        print("\n" + '='*80)
        # Scan for drives, display available space
        drive_list = util.get_drive_list()
        print()
        for drive in drive_list:
            print(util.drive_space_display_string(drive, precision=2), end="")
        # Display current configuration information
        print("\nCalculating file sizes...", end="\r", flush=True)
        print(configuration.config_display_string(config))

        # Display the main menu and prompt for user input
        user_input = input_menu(["Select a folder or file to backup",
                                 "Configure destination locations",
                                 "Exclude specific files/folders from your backup",
                                 "Edit/delete configuration entries",
                                 "Save current backup configuration",
                                 "Load a backup configuration",
                                 "Backup your files",
                                 "Re-scan for available drives",
                                 "Exit"])
        print()

        # Select a folder or file to backup
        if user_input == 1:
            menu_option_input(config)
        # Configure destination locations
        elif user_input == 2:
            # Return to the menu if there's no entries
            if config.num_entries() > 0:
                menu_option_destination(config)
            else:
                print("There are no entries to add a destination to.")
                continue
        # Exclude files/folders
        elif user_input == 3:
            if config.num_entries() > 0:
                menu_option_exclude(config)
            else:
                print("There are no entries to add exclusions to.")
                continue
        # Edit/delete configuration entries
        elif user_input == 4:
            # Return to the menu if there's no entries
            if config.num_entries() > 0:
                menu_option_edit(config)
            else:
                print("There are no entries to edit or delete.")
                continue
        # Save current configuration
        elif user_input == 5:
            menu_option_save(config)
        # Load a configuration
        elif user_input == 6:
            config_list = configuration.saved_config_display_string()
            if config_list == "":
                print("There are no currently saved configurations.")
                continue
            else:
                config = menu_option_load(config, config_list)
        # Run the backup
        elif user_input == 7:
            # Return to the menu if there's no entries
            if config.num_entries() > 0:
                if config.all_entries_have_outputs():
                    menu_option_backup(config)
                else:
                    print("Not all inputs have a destination specified to back them up to.")
                    continue
            else:
                print("There is nothing currently selected to backup.")
                continue
        # Refresh
        elif user_input == 8:
            print("Scanning again for available drives...")
            continue
        # Exit
        elif user_input == 9:
            break


if __name__ == "__main__":
    main()
