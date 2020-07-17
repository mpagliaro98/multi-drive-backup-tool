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
    print("3: Save current backup configuration")
    print("4: Load a backup configuration")
    print("5: Backup your files")
    print("6: Re-scan for available drives")
    print("7: Exit")


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
            result = False
            while not result:
                # Accept user input for path to directory or file
                input_name = input("Enter the absolute path of a folder or file to backup: ")
                # Check if the input is valid, and if so add it to the config
                config, result = configuration.append_input_to_config(config, input_name)
                # No changes occur to the config if it's invalid, so show that it's invalid
                if not result:
                    print("The given path was invalid, or is already specified.")

        # Configure destination locations
        elif user_input == "2":
            # Return to the menu if there's no entries
            if config.num_entries() == 0:
                print("There are no entries to add a destination to.")
                continue
            # Display a list of entries in the configuration
            config.enumerate_entries()
            # Accept input to select one of those entries (or all at once)
            entry_number = input("Enter a number to specify that entry's destinations (or 0 to modify all at once): ")
            if int(entry_number) < 0 or int(entry_number) > config.num_entries():
                print("Invalid input, no entry exists with that number")
                continue
            # Input loop: Enter paths to send this folder to
            print("Enter the absolute paths of each destination, separated by the Enter key (enter \"end\" to stop)")
            while True:
                destination_input = input()
                if destination_input == "end":
                    break
                config, result = configuration.append_output_to_config(config, int(entry_number), destination_input)
                if not result:
                    print("The given path was invalid, is already specified, or is a sub-folder of the input.")

        # Save current configuration
        elif user_input == "3":
            # Input: Give a name to this configuration
            config_name = input("Enter a name for this configuration: ")
            # Pass the config and the name to the save function (ask to overwrite if the name exists)
            overwrite = "y"
            if configuration.config_exists(config_name):
                overwrite = input("Would you like to overwrite this existing configuration? (y/n): ")
            if overwrite.lower() == "y":
                configuration.save_config(config, config_name)

        # Load a configuration
        elif user_input == "4":
            # Input loop: Enter name of saved configuration, input "end" to stop, stop once a valid name is entered
            config_list = configuration.saved_config_display_string()
            if config_list == "":
                print("There are no currently saved configurations.")
                continue
            print(configuration.saved_config_display_string())
            while True:
                config_name = input("Enter a name of a configuration to load (enter \"end\" to stop): ")
                if configuration.config_exists(config_name):
                    config = configuration.load_config(config_name)
                    break
                elif config_name == "end":
                    break
                print("{} is an invalid configuration name.".format(config_name))

        # Run the backup
        elif user_input == "5":
            # Print the configuration, showing each folder to backup and its destinations
            configuration.config_display_string(config)
            # Ask to confirm if this is ok to backup
            backup_confirmation = input("Would you like to start the backup with this configuration? (y/n): ")
            # If yes, run the backup
            if backup_confirmation.lower() == "y":
                backup.run_backup(config)

        # Refresh
        elif user_input == "6":
            print("Scanning again for available drives...")
            continue

        # Exit
        elif user_input == "7":
            break

        # Handle any other inputs
        else:
            print("Invalid input")


if __name__ == "__main__":
    main()
