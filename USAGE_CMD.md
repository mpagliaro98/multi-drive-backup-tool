# Multi-Drive Backup Tool Command Line Argument Version

The Command Line Argument version of the Multi-Drive Backup Tool is one of three ways you can interface with it. This version requires users to run `python mdbt.py` with any number of the command line arguments below to build configurations and run a backup. This is best suited for setting up batch files to run a backup just by clicking one file. For more beginner-friendly instructions on what configurations are and what their structure looks like, see the [GUI instructions](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_GUI.md), as almost everything from the first two sections there can also apply to the CLI and CMD versions.

Upon running `python mdbt.py` with no arguments, you will be presented with the list of possible options. Below is a simpler version of that list showing the main function of each option. The rest of this document will go more in-depth on how to use each one and what they all do.

When this is run, it begins with a blank configuration. All arguments you pass to it will be applied to that blank configuration. In order to save the results of one use of the program, you should use the save configuration argument at some point. Most uses will also begin with the load argument or the load/save wrapper argument to replace that initial blank configuration with an existing one, and modify it from there.

```
-i <input_path>
	Specify a file/folder to back up
-d <destination_path> <data_arg1>
	Specify a folder to back something up to
-e <exclusion_data> <data_arg1> <data_arg2>
	Create an exclusion
-t <limitation_data> <data_arg1> <data_arg2> <data_arg3>
	Create a limitation
-m <new_data> <data_arg1> [<data_arg2> <data_arg3> <data_arg4>]
	Edit data in the configuration
-x <delete_mode> <data_arg1> [<data_arg2> <data_arg3>]
	Delete data in the configuration
-s <config_name>
	Save the configuration
-l <config_name>
	Load a configuration
-c <config_name>
	Load a configuration at the start, then save it at the end
-b
	Run a backup
-p
	Print the current configuration
-q
	Display all exclusion types and their codes
-r
	Display all limitation types and their codes
-h
	Print help text
```

## -i: Input Path

Specify an absolute path right after this option to create a new entry. The path that you specify will be set as that entry's input path, which will allow it to be backed up to a destination path you specify later.

To set a directory at "C:\folder1" to be backed up, run `python mdbt.py -i "C:\folder1"`

## -d: Destination Path

Specify an absolute path to a directory where you want an input path backed up to. At least one input path must exist before you can use this option. First, you put the absolute path of where you want to back up to right after the argument flag (-d), then you must specify a data argument to say which input path this will be added to. A data argument is written as `--data <data>` where the contents of `<data>` vary between arguments that require it. In this case, this argument requires one data argument which indicates the index of the entry you'd like to modify. These indexes start at 1, so if you've only specified one input path, you'd write `--data 1` so say it should be added to the first input path.

To say you want to back up "C:\folder1" to "D:\", run `python mdbt.py -i "C:\folder1" -d "D:\" --data 1`

## -e: Exclusion

Create an exclusion and attach it to an entry using this argument. For an in-depth explanation of what exclusions are and how they work, see the Exclusions section in the [GUI usage document](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_GUI.md). The data for the exclusion is required right after the -e flag, then two data arguments must follow it. The first data argument indicates the index of the entry to add this exclusion to, starting from 1. The second data argument specifies the code of the exclusion type that will be used. To get a list of exclusion types and their codes, use the -q option, described later. For more information on what data arguments are, see the -d section above.

To create an entry with "C:\folder1" as the input, and then make an exclusion that excludes every file starting with "data_", run `python mdbt.py -i "C:\folder1" -e "data_" --data 1 --data "startswith"`

## -t: Limitation

Create a limitation and attach it to an exclusion using this argument. For an in-depth explanation of what limitations are and how they work, see the Limitations section in the [GUI usage document](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_GUI.md). This is formatted very similar to the exclusion option, but with one additional data argument. The data for the limitation is required right after the -t flag, then three data arguments follow it. The first, like with the exclusion option, indicates the index of the entry to add this to. The second one then indicates the index of the exclusion within the chosen entry to add this to. The third specifies the code of the limitation type that will be used. To get a list of limitation types and their codes, use the -r option, described later. For more information on what data arguments are, see the -d section above.

Building off the previous example, we are excluding all files that start with "data_" in the first entry, which is backing up the "C:\folder1" directory. Now we want to add a limitation to that exclusion that makes that exclusion only work within "C:\folder1\sub1" and all its subdirectories. To do this, run `python mdbt.py -i "C:\folder1" -e "data_" --data 1 --data "startswith -t "C:\folder1\sub1" --data 1 --data 1 --data "sub"`

## -m: Modify Data

The modify command can be used in a variety of ways in order to edit data in the configuration. You can specify anywhere between 1 and 4 data arguments after the -m flag, and the number of them you put indicates to the program which type of data to modify. For more information on what data arguments are, see the -d section above. Also be careful of changing data that creates cyclic entries, or makes an output the sub-path of an input, which will raise exceptions. For more information on these issues, see the Option 4 section of the [CLI usage document](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_CLI.md).

To edit an input path, only use one data argument. Write the new input path immediately after the -m flag, then after the data argument put the index of the entry to modify, starting from 1. So to change the first entry to back up "C:\folder2", you'd write `python mdbt.py -m "C:\folder2" --data 1`

To edit a destination path, use two data arguments. The new destination path follows the -m flag, then the first data argument indicates the index of the entry, and the second indicates the index of the destination path to modify, both starting from 1. So to change the first destination path on the first entry to "E:\", run `python mdbt.py -m "E:\" --data 1 --data 1`

To change an exclusion's type or data, use three data arguments. The first two data arguments function similar to before. The first data argument indicates the index of the entry, and the second data argument indicates the index of the exclusion in that entry to modify, both starting from one. Things change when it comes to the third data argument, however. The third argument should be a 1 if you want to edit the exclusion's type, or a 2 if you want to edit the exclusion's data. This in turn affects what you put right after the -m flag. When editing an exclusion's type, a new exclusion type code should follow the -m flag. When editing an exclusion's data, new data should follow the -m flag instead. For instance, if you want to change the data on the second exclusion in the first entry to the string "new_data", you would run `python mdbt.py -m "new_data" --data 1 --data 2 --data 2`

Changing limitation types and data requires four data arguments, and functions very similarly to how exclusions work. The first three arguments are indexes - first is the index of an entry, then an index of an exclusion in that entry, then an index of a limitation in that exclusion, all starting from one. Similar to before, the fourth argument is either a 1 to edit that limitation's type or 2 to edit that limitation's data. If it is 1, the data right after the -m flag will be the code of a limitation type, or if it is 2, it will be some new data. For instance, if you wanted to change the type of the third limitation on the first exclusion on the second entry to the "this directory and no subdirectories" type, run `python mdbt.py -m "sub" --data 2 --data 1 --data 3 --data 1`

## -x: Delete Data

Similar to the modify command, the delete command takes a variable number of data arguments. However, this time it takes a "delete mode" right after the -x flag to determine what kind of data will be deleted, and then each mode has a number of data arguments it requires. For more information on what data arguments are, see the -d section above. Valid delete modes for this are "entry", "destination", "exclusion", and "limitation".

To delete an entry, first specify "entry" after the -x flag. Then it requires one data argument, just the index of the entry to delete. So to delete the third entry in the configuration, you'd run `python mdbt.py -x "entry" --data 3`

To delete a destination, first specify "destination" after the -x flag, then put two data arguments. The first is the index of an entry, and the second is the index of a destination in that entry to delete, both starting from one. So to delete the first destination in the second entry, you'd run `python mdbt.py -x "destination" --data 2 --data 1`

To delete an exclusion, first specify "exclusion" after the -x flag, then also put two data arguments. Like before, the first is the index of an entry, but now the second is the index of an exclusion in that entry you want to delete. So to delete the fourth exclusion in the third entry, you'd run `python mdbt.py -x "exclusion" --data 3 --data 4`

To delete a limitation, first specify "limitation" after the -x flag, then put three data arguments. The first two are the same as for deleting exclusions - first specify the index of an entry, then the index of an exclusion in that entry. The third data argument is then the index of a limitation in that exclusion you'd like to delete. So to delete the first limitation in the second exclusion of the fourth entry, you'd run `python mdbt.py -x "limitation" --data 4 --data 2 --data 1`

## -s: Save the Configuration

Use this option to save your configuration to a file. Simply write the name you'd like to give this configuration after the -s flag and it will be saved. Be careful of overwriting existing configuration files, as this gives no prompt if you're going to overwrite an existing file. Also note that since arguments are processed in order by the program, the positioning of where you put the save argument is important. In order to save all the changes you are currently making, this argument should be the last you send to the program. If you put this argument in the middle, every command that comes after it will not be saved to the file.

To save the current configuration to a file called "my config", run `python mdbt.py -s "my config"`

## -l: Load a Configuration

Use this option to load in a saved configuration to edit it further or to run a backup using it. Specify the name of the saved configuration after the -l flag. This will replace the current configuration with the one just loaded in, so if this argument is called in the middle of the sequence, previous changes will be erased.

To load a configuration in named "my config", run `python mdbt.py -l "my config"`

## -c: Load/Save Wrapper

This is a unique type of argument that combines the functionality of the load and save arguments. Specify a name of a saved configuration after the -c flag. Now no matter where in the sequence this argument is, it will be called first, and load in that configuration at the start of execution. Then once every other argument is finished, it will save the configuration back to the same file it was loaded from. Only one -c argument should be specified when you run the application, otherwise unexpected changes may occur.

To make changes to a configuration named "my config", run `python mdbt.py -c "my config" [any other arguments...]`

## -b: Backup

This argument starts the backup process with the configuration that is currently in the system. It requires no data after the -b flag to run. You can either specify a series of arguments to build a configuration before running the -b flag, or load in a configuration at the start and run the -b flag after that.

To load in a configuration named "my config" and run a backup on it, run `python mdbt.py -l "my config" -b`

## -p: Print the Configuration

To display the full configuration, use this argument. This is only for utility purposes and does not do anything other than print configuration data to the screen.

To display a saved configuration named "my config", run `python mdbt.py -l "my config" -p`

## -q: Print Exclusion Types

This is another utility argument that displays a list of all available exclusion types. It is useful to run this as a standalone argument before creating exclusions in order to have a list of what types are available and their codes. The first value on each displayed line is the exclusion type code, followed by a description of what each does.

To show a list of exclusion types, run `python mdbt.py -q`

## -r: Print Limitation Types

Similar to the exclusion types argument, this does the same but for limitation types. The type code will be the first value on each line, followed by a description of each.

To show a list of limitation types, run `python mdbt.py -r`

## -h: Help

The help argument displays usage text for the program when run. Either specify this argument, or run the program with no arguments in order to get the usage text to display. It will show a formatted list of every argument the program accepts along with a description of how to use each. This document goes more in-depth than the usage text.

To display help text, run `python mdbt.py -h` or just `python mdbt.py`