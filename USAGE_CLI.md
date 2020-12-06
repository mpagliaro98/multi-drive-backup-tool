
# Multi-Drive Backup Tool CLI Version  
  
For more beginner-friendly instructions on what configurations are and what their structure looks like, see the [GUI instructions](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_GUI.md), as almost everything from the first two sections there can also apply to the CLI and CMD versions.  
  
The Command Line Interface version of this application was the first front-end created and used to test the rest of the application. The GUI version is more recommended for a better user experience. Upon running the program, you will be presented with a menu of options.

```  
1: Select a folder or file to backup  
2: Configure destination locations  
3: Exclude specific files/folders from your backup  
4: Edit/delete configuration entries  
5: Save current backup configuration  
6: Load a backup configuration  
7: Backup your files  
8: Re-scan for available drives  
9: Exit  
```  

The following sections of this usage guide will cover each menu option in detail.
  
## Option 1: Choose What to Back Up  

To begin, use this option to specify what to back up. Absolute paths are entered one at a time in order to create entries.
  
## Option 2: Where to Back It Up To  

Once an entry has been created using option 1, you can add locations where the backups will be made. This will present you with a list of all the entries so far, and you can choose to enter a location for just one or for all of them at once. Once you choose, you can enter as many locations for backups as you'd like until you enter "end".
  
## Option 3: Optional Exclusions and Limitations  

Option 3 allows you to add exclusions and limitations. These are optional features to further customize your configuration, and are described in detail under the Advanced Configuration Options heading in the [GUI usage document](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_GUI.md).

Upon selecting the option, you will be given the option to choose an entry. If that entry has no exclusions currently on it, you will be given a list of exclusion rules to choose from. Choosing one will prompt you to enter data for it, and each has different requirements for how the data should be formatted, which will be explained in the prompt.

If the entry you select has at least one exclusion on it already, you will instead get a menu asking if you'd like to create an exclusion or add a limitation to an existing exclusion. The first option takes you through the previous paragraph, but the second option will give you a list of exclusions on your chosen entry. Then you may choose a limitation rule and input data for it in the same way you did for the exclusion.
  
## Option 4: Editing Your Configuration  

All controls for editing and deleting existing data in your configuration are under option 4. First you are given the option to choose an entry, after which you may edit any details of the entry, delete parts of an entry, or delete the whole entry entirely. When it comes to editing the input path or any destinations, it is worth noting that they can't be changed to become a sub-path of one another or create cyclic entries. Any of an entry's outputs cannot be a sub-path of its input, which would cause the first issue. Second, a cyclic entry is created when one entry makes a backup within the input path of a later entry. Both of these issues create size calculation issues during the backup process, and the first may end up a recursive backup loop.
  
## Option 5: Saving Your Configuration  

Configurations can be saved using option 5. This allows you to specify the name your configuration should have, and if that name matches any previously saved configurations, it will ask you if you'd like to overwrite it. To update the saved file of your existing configuration, you will have to re-enter its name at this point. Configurations get saved to the `/configs/` directory in the directory where this program was installed, and are each saved to their own `.dat` files.
  
## Option 6: Loading a Saved Configuration  

Load a configuration you've previously saved using this option. Deleting configurations from within the CLI is not possible, instead you can simply go to the `/configs/` directory and delete the configuration files you would no longer like.
  
## Option 7: Run a Backup  

Once your configuration is ready, you can use this option to run the backup process. The folders/files you specified as inputs will be copied to each output location you specified for each of them. When a file or folder is copied over, it will be given the suffix "BACKUP", so copying for instance "C:\folder1" to "D:\" will make a new folder called "D:\folder1 BACKUP" and copy all files into there. Once the backup is complete, a `_BACKUP-CONFIRMATION.txt` file is placed in the root of each backup, containing the date and time the backup was completed. This information is also present in the log file created for this backup, which can be found in the `/logs/` directory within the directory this program was installed in. Each log file contains a complete list of every modification the backup process made, as well as more detailed information about any errors that may have occurred. In the event you are backing up something that you had already backed up during a previous use of this program, only files that are new or changed since the last backup will be copied over. Files in the backup destination that are no longer in the source directory will be removed as well.
  
## Other

The final two options are self-explanatory - option 8 refreshes the main menu to check for any drives that have changed, and option 9 exits. It is also worth noting that configurations are interchangeable between versions of this application - for instance a configuration created in the CLI version can be used in the GUI version and vice versa.