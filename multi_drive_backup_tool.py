"""
multi_drive_backup_tool.py
Author: Michael Pagliaro
The main entry-point for the tool. Handles all user input. This file acts as the entire
user interface and most of the front-end of the application.
"""

import configuration
from exclusions import EXCLUSION_TYPES
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
    result = False
    while not result:
        # Accept user input for path to directory or file
        input_name = input("Enter the absolute path of a folder or file to backup (enter \"end\" to stop): ")
        if input_name == "end":
            break
        # Check if the input is valid, and if so add it to the config
        result = configuration.append_input_to_config(config, input_name)
        # No changes occur to the config if it's invalid, so show that it's invalid
        if not result:
            print("The given path was invalid or created a cyclic entry.")


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
        destination_input = input()
        if destination_input == "end":
            break
        result = configuration.append_output_to_config(config, entry_number, destination_input)
        if not result:
            print("The given path was invalid, is a sub-folder of the input, or created a cyclic entry.")


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

    # Once chosen, display options to add different types of exclusions
    while True:
        exclusion_number = 1
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
            exclusion_number = entry.new_exclusion(exclusion_codes[exclusion_input-1], exclusion_data)
        # Return to the menu
        elif exclusion_input == len(exclusion_codes)+1:
            break

        # If this exclusion type takes limitations, prompt if the user would like to add one
        if EXCLUSION_TYPES[exclusion_input-1].accepts_limitations:
            directory_input = input("Would you like to limit this exclusion to a directory? (y/n): ")
            if directory_input.lower() == "y":
                # Get the directory to limit this exclusion to
                limit_directory = input("Enter the absolute path of a folder to limit this exclusion to: ")

                # Allow the user to select which limitation mode to use
                limitation_input = input_menu([item.menu_text for item in LIMITATION_TYPES])
                limitation_code = LIMITATION_TYPES[limitation_input-1].code

                # Add this limitation to the entry
                entry.get_exclusion(exclusion_number).add_limitation(limitation_code, limit_directory)


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
            result = False
            while not result:
                input_name = input("Enter the new absolute path of a folder or file to backup: ")
                result = configuration.edit_input_in_config(config, entry_number, input_name)
                if not result:
                    print("The given path is invalid, created a cyclic entry, or a destination became a sub-folder.")
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
            result = False
            while not result:
                input_name = input("Enter the new absolute path of a folder to make a destination: ")
                result = configuration.edit_destination_in_config(entry, dest_number, input_name, config)
                if not result:
                    print("The given path was invalid, is a sub-folder of the input, or created a cyclic entry.")
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
                # Create the edit exclusion menu, change the add limitation option to edit if a limitation exists
                excl_edit_menu = ["Change the exclusion type",
                                  "Change the exclusion data",
                                  "Add a limitation",
                                  "Return to the previous menu"]
                if exclusion.has_limitation():
                    excl_edit_menu[excl_edit_menu.index("Add a limitation")] = "Edit the limitation"
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
                # Add or edit limitation
                elif excl_edit_input == 3:
                    sub_option_edit_limitations(exclusion)
                # Return to the previous menu
                elif excl_edit_input == 4:
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


def sub_option_edit_limitations(exclusion):
    """
    The code that is run when the sub-option for editing the limitation of an exclusion is selected.
    If the limitation exists, this will display a menu allowing the user to edit the type or data of it or
    delete it. If no limitation exists, it will allow the user to create one.
    :param exclusion: The current exclusion whose limitation is being edited.
    """
    # Don't allow adding or editing if this exclusion type doesn't allow limitations
    for exclusion_type in EXCLUSION_TYPES:
        if exclusion.code == exclusion_type.code:
            if not exclusion_type.accepts_limitations:
                print("This exclusion type does not allow limitations.")
                return
    # Adding a limitation
    if not exclusion.has_limitation():
        limit_directory = input("Enter the absolute path of a folder to limit this exclusion to: ")
        limitation_input = input_menu([item.menu_text for item in LIMITATION_TYPES])
        limitation_code = LIMITATION_TYPES[limitation_input-1].code
        exclusion.add_limitation(limitation_code, limit_directory)
    # Editing a limitation
    else:
        while True:
            limit_edit_input = input_menu(["Change the limitation type",
                                           "Change the limitation data",
                                           "Delete this limitation",
                                           "Return to the previous menu"])

            # Change limitation type
            if limit_edit_input == 1:
                limitation_codes = [item.code for item in LIMITATION_TYPES]
                limitation_menu_options = [item.menu_text for item in LIMITATION_TYPES]
                new_limitation_input = input_menu(limitation_menu_options,
                                                  input_text="Choose one of these options to change the type to: ")
                exclusion.limitation.code = limitation_codes[new_limitation_input-1]
            # Change limitation data
            elif limit_edit_input == 2:
                new_data = input("Enter new data for this limitation: ")
                exclusion.limitation.data = new_data
            # Delete the limitation
            elif limit_edit_input == 3:
                del exclusion.limitation
                break
            # Return to the previous menu
            elif limit_edit_input == 4:
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
        config.name = config_name
        configuration.save_config(config, config_name)


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
