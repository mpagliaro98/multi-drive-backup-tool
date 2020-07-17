"""
multi_drive_backup_tool.py
Author: Michael Pagliaro
The main entry-point for the tool. Handles all user input.
"""

import configuration
import util
import backup


def display_main_menu():
    """
    Print out the options that make up the main menu.
    """
    print("\n1: Select a folder or file to backup")
    print("2: Configure destination locations")
    print("3: Edit/delete configuration entries")
    print("4: Save current backup configuration")
    print("5: Load a backup configuration")
    print("6: Backup your files")
    print("7: Re-scan for available drives")
    print("8: Exit")


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
        if int(entry_number) < low_bound or int(entry_number) > high_bound:
            print(error_text)
        else:
            return entry_number


def menu_option_input(config):
    """
    The code that is run when the menu option for selecting a new folder to backup is selected.
    This will accept user input until a valid file or folder path is input.
    :param config: The current backup configuration.
    :return: The updated configuration with the new user-input path.
    """
    result = False
    while not result:
        # Accept user input for path to directory or file
        input_name = input("Enter the absolute path of a folder or file to backup: ")
        # Check if the input is valid, and if so add it to the config
        config, result = configuration.append_input_to_config(config, input_name)
        # No changes occur to the config if it's invalid, so show that it's invalid
        if not result:
            print("The given path was invalid, or is already specified.")
    return config


def menu_option_destination(config):
    """
    The code that is run when the menu option for entering a new destination path is selected.
    This will prompt the user to choose an entry, then allow them to enter directory paths until
    they specify when to stop.
    :param config: The current backup configuration.
    :return: The updated configuration with the new destination paths.
    """
    # Display a list of entries in the configuration
    config.enumerate_entries()
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
        config, result = configuration.append_output_to_config(config, int(entry_number), destination_input)
        if not result:
            print("The given path was invalid, is already specified, or is a sub-folder of the input.")
    return config


def sub_option_edit_destinations(config, entry_number):
    """
    The code that is run when the sub-option for editing the destinations of an entry is selected.
    This will display a menu, allowing the user to choose to edit a destination, delete a destination,
    or return to the previous menu.
    :param config: The current backup configuration.
    :param entry_number: The number of the index of the entry, starting at 1.
    :return: The updated configuration with edited destinations.
    """
    while True:
        print("\n1: Edit a destination\n2: Delete a destination\n3: Return to the previous menu")
        destination_input = input("Choose an option: ")

        # Edit destination
        if destination_input == "1":
            print()
            config.enumerate_destinations(int(entry_number))
            dest_number = input_entry_number(low_bound=1, high_bound=config.num_destinations(int(entry_number)),
                                             input_text="Enter a number to specify which destination to edit: ")
            result = False
            while not result:
                input_name = input("Enter the new absolute path of a folder to make a destination: ")
                config, result = configuration.edit_destination_in_config(config, int(entry_number),
                                                                          int(dest_number), input_name)
                if not result:
                    print("The given path was invalid, is already specified, or is a sub-folder " +
                          "of the input.")
        # Delete destination
        elif destination_input == "2":
            print()
            config.enumerate_destinations(int(entry_number))
            dest_number = input_entry_number(low_bound=1, high_bound=config.num_destinations(int(entry_number)),
                                             input_text="Enter a number to specify which destination to delete: ")
            config.delete_destination(int(entry_number), int(dest_number))
            # Go to the previous menu if the last destination is deleted
            if config.num_destinations(int(entry_number)) == 0:
                break
        # Return to the previous menu
        elif destination_input == "3":
            break
        # Invalid input
        else:
            print("Invalid input.")
    return config


def menu_option_edit(config):
    """
    The code that is run when the menu option for editing the configuration is selected. This will allow
    the user to choose an entry, then display a menu that will allow the user to edit that entry's input
    path, edit its destinations, delete all its destinations, delete the entire entry, or return to the
    previous menu.
    :param config: The current backup configuration.
    :return: The updated configuration with edited values.
    """
    # Display a list of entries in the configuration
    config.enumerate_entries()
    # Accept input to select one of those entries
    entry_number = input_entry_number(low_bound=1, high_bound=config.num_entries(),
                                      input_text="Enter a number to edit or delete that entry: ")
    # Once chosen, display options to edit or delete this entry
    while True:
        print()
        print(config.entry_to_string(int(entry_number)))
        print("1: Edit the input path\n2: Edit the destinations\n3: Delete all destinations")
        print("4: Delete this entire entry\n5: Return to the menu")
        edit_input = input("Choose an option: ")

        # Edit the input path
        if edit_input == "1":
            result = False
            while not result:
                input_name = input("Enter the new absolute path of a folder or file to backup: ")
                config, result = configuration.edit_input_in_config(config, int(entry_number), input_name)
                if not result:
                    print("The given path is invalid, already specified, or a destination became a sub-folder.")
        # Edit the destinations
        elif edit_input == "2":
            if config.num_destinations(int(entry_number)) > 0:
                config = sub_option_edit_destinations(config, entry_number)
            else:
                print("There are no destinations to edit or delete.")
                continue
        # Delete all destinations
        elif edit_input == "3":
            config.delete_destinations(int(entry_number))
        # Delete this entry
        elif edit_input == "4":
            config.delete_entry(int(entry_number))
            break
        # Return to the previous menu
        elif edit_input == "5":
            break
        # Invalid input
        else:
            print("Invalid input.")
    return config


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
        if configuration.config_exists(config_name):
            config = configuration.load_config(config_name)
            break
        elif config_name == "end":
            break
        print("{} is an invalid configuration name.".format(config_name))
    return config


def menu_option_backup(config):
    """
    The code that is run when the menu option for backing up the selected files is selected.
    This will ask for confirmation before beginning, and then run the backup process.
    :param config: The current backup configuration.
    """
    # Print the configuration, showing each folder to backup and its destinations
    print(configuration.config_display_string(config))
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
        print("\n======================================================================================")
        # Scan for drives, display available space
        drive_list = util.get_drive_list()
        print()
        for drive in drive_list:
            print(util.drive_space_display_string(drive, precision=2), end="")
        # Display current configuration information
        print("\n" + configuration.config_display_string(config))

        # Display the main menu and prompt for user input
        display_main_menu()
        user_input = input("Enter the number of an option: ")
        print()

        # Select a folder or file to backup
        if user_input == "1":
            config = menu_option_input(config)
        # Configure destination locations
        elif user_input == "2":
            # Return to the menu if there's no entries
            if config.num_entries() > 0:
                config = menu_option_destination(config)
            else:
                print("There are no entries to add a destination to.")
                continue
        # Edit/delete configuration entries
        elif user_input == "3":
            # Return to the menu if there's no entries
            if config.num_entries() > 0:
                config = menu_option_edit(config)
            else:
                print("There are no entries to edit or delete.")
                continue
        # Save current configuration
        elif user_input == "4":
            menu_option_save(config)
        # Load a configuration
        elif user_input == "5":
            config_list = configuration.saved_config_display_string()
            if config_list == "":
                print("There are no currently saved configurations.")
                continue
            else:
                config = menu_option_load(config, config_list)
        # Run the backup
        elif user_input == "6":
            # Return to the menu if there's no entries
            if config.num_entries() > 0:
                menu_option_backup(config)
            else:
                print("There is nothing currently selected to backup.")
                continue
        # Refresh
        elif user_input == "7":
            print("Scanning again for available drives...")
            continue
        # Exit
        elif user_input == "8":
            break
        # Handle any other inputs
        else:
            print("Invalid input.")


if __name__ == "__main__":
    main()
