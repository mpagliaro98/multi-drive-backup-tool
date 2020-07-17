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

        # Edit/delete configuration entries
        elif user_input == "3":
            # Return to the menu if there's no entries
            if config.num_entries() == 0:
                print("There are no entries to edit or delete.")
                continue
            # Display a list of entries in the configuration
            config.enumerate_entries()
            # Accept input to select one of those entries
            entry_number = input("Enter a number to edit or delete that entry: ")
            if int(entry_number) < 1 or int(entry_number) > config.num_entries():
                print("Invalid input, no entry exists with that number")
                continue
            # Once chosen, have options to edit input, edit outputs, delete all outputs, or delete entire entry
            while True:
                print()
                print(config.entry_to_string(int(entry_number)))
                print("1: Edit the input path\n2: Edit the destinations\n3: Delete all destinations")
                print("4: Delete this entire entry\n5: Return to the menu")
                edit_input = input("Choose an option: ")
                if edit_input == "1":
                    result = False
                    while not result:
                        input_name = input("Enter the new absolute path of a folder or file to backup: ")
                        config, result = configuration.edit_input_in_config(config, int(entry_number), input_name)
                        if not result:
                            print("The given path was invalid, or is already specified.")
                elif edit_input == "2":
                    if config.num_destinations(int(entry_number)) == 0:
                        print("There are no destinations to edit or delete.")
                        continue
                    while True:
                        print("\n1: Edit a destination\n2: Delete a destination\n3: Return to the previous menu")
                        destination_input = input("Choose an option: ")
                        if destination_input == "1":
                            print()
                            config.enumerate_destinations(int(entry_number))
                            dest_number = input("Enter a number to specify which destination to edit: ")
                            if int(dest_number) < 1 or int(dest_number) > config.num_destinations(int(entry_number)):
                                print("Invalid input, no entry exists with that number")
                                continue
                            result = False
                            while not result:
                                input_name = input("Enter the new absolute path of a folder to make a destination: ")
                                config, result = configuration.edit_destination_in_config(config, int(entry_number),
                                                                                          int(dest_number), input_name)
                                if not result:
                                    print("The given path was invalid, is already specified, or is a sub-folder " +
                                          "of the input.")
                        elif destination_input == "2":
                            print()
                            config.enumerate_destinations(int(entry_number))
                            dest_number = input("Enter a number to specify which destination to delete: ")
                            if int(dest_number) < 1 or int(dest_number) > config.num_destinations(int(entry_number)):
                                print("Invalid input, no entry exists with that number")
                                continue
                            config.delete_destination(int(entry_number), int(dest_number))
                        elif destination_input == "3":
                            break
                        else:
                            print("Invalid input.")
                elif edit_input == "3":
                    config.delete_destinations(int(entry_number))
                elif edit_input == "4":
                    config.delete_entry(int(entry_number))
                    break
                elif edit_input == "5":
                    break
                else:
                    print("Invalid input.")
            # If editing outputs, enumerate outputs and have options to edit an output or delete an output

        # Save current configuration
        elif user_input == "4":
            # Input: Give a name to this configuration
            config_name = input("Enter a name for this configuration: ")
            # Pass the config and the name to the save function (ask to overwrite if the name exists)
            overwrite = "y"
            if configuration.config_exists(config_name):
                overwrite = input("Would you like to overwrite this existing configuration? (y/n): ")
            if overwrite.lower() == "y":
                configuration.save_config(config, config_name)

        # Load a configuration
        elif user_input == "5":
            # Input loop: Enter name of saved configuration, input "end" to stop, stop once a valid name is entered
            config_list = configuration.saved_config_display_string()
            if config_list == "":
                print("There are no currently saved configurations.")
                continue
            print("List of available saved configurations:")
            print(configuration.saved_config_display_string())
            while True:
                config_name = input("Enter a name of a configuration to load (enter \"end\" to return to the menu): ")
                if configuration.config_exists(config_name):
                    config = configuration.load_config(config_name)
                    break
                elif config_name == "end":
                    break
                print("{} is an invalid configuration name.".format(config_name))

        # Run the backup
        elif user_input == "6":
            # Print the configuration, showing each folder to backup and its destinations
            configuration.config_display_string(config)
            # Ask to confirm if this is ok to backup
            backup_confirmation = input("Would you like to start the backup with this configuration? (y/n): ")
            # If yes, run the backup
            if backup_confirmation.lower() == "y":
                backup.run_backup(config)

        # Refresh
        elif user_input == "7":
            print("Scanning again for available drives...")
            continue

        # Exit
        elif user_input == "8":
            break

        # Handle any other inputs
        else:
            print("Invalid input")


if __name__ == "__main__":
    main()
