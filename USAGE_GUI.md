
# Multi-Drive Backup Tool GUI Version  
  
These instructions are for the GUI version of this application. It allows users to get a user-friendly window to interface with the program, offering easy navigation of files and organization of backup entries. The following will explain anything a user needs to know about building a configuration and running a backup. 

These instructions can be accessed from the Github page or by selecting "How to use" from the Help menu in the application.
  
## Build a Configuration  
  
What is a configuration? A configuration defines everything that happens when you press the backup button, like a recipe. At the most basic level, a configuration contains a list of entries. Each entry defines a folder or file you want to back up, and where it will be backed up to. Beyond that, advanced features like exclusions and limitations give you more control of what is backed up, and those will be discussed later.

The instructions below will outline how to create an entry in your configuration that will be ready to be backed up.
  
### Select what you want backed up  

When you first open the application, you will be given a blank entry to work off of. You'll see a column on the left side of the window with one button named **"New Entry"** in it, this is the list of entries in your configuration. The **"New Entry"** button is highlighted blue, meaning you are currently creating a new entry.

To create the new entry, you must choose something to back up. Use the tree of files on the left, under the large **"Backup"** text near the top. You can scroll through your computer's file structure and click on a folder or file in the list to highlight it. Once you have the folder or file highlighted that you want to back up, press the **"Set highlighted path to input"** button below the file tree.

Once that button is pressed, a few things happen. First, the path you selected will appear just below the **"Backup"** text. Then you'll see a new button appear on the left side, starting with **"Entry 1"** and followed by the file or folder name you chose. This button is now highlighted instead of the **"New Entry"** button, signifying you created a new entry and are now viewing it.

If you ever want to change what you have backed up, you can simply select another file or folder in the left tree and press the **"Set highlighted path to input"** button again, and it will change.
  
### Choose where to back it up to  

Now that you chose what to back up, you need to specify where it will be backed up to. Use the file tree on the right to find locations to back it up to. Similar to how you specified the file/folder to back up, you'll just select a folder in the right tree, then press the **"Add highlighted path as output"** button. This will cause the path you selected to appear just below the **"Copy To"** text.

Unlike with the file/folder you are backing up, you can specify multiple "outputs" for where your file/folder will be backed up to. If you select another folder in the right tree and press the **"Add highlighted path as output"** button again, you'll notice that path was added to a list after the first one, and didn't replace it. If you have several paths in this list, you will be able to scroll through it.

If you want to remove "outputs" for your backup, you can delete them from the list under the **"Copy To"** text. Simply right-click the path you don't want and choose "Delete". You can also left-click these paths to highlight them. If you have several you want deleted, left-click them all to highlight them, then in the Edit menu at the top of the window, choose "Delete highlighted outputs".

With a path to back up set and any number of destinations for it set, you are now ready to run a backup.
  
## Run a Backup  
  
Backups are simple to run, and provide helpful output so you can see how far along it is. Once you've done at minimum the instructions above, press the large **"BACKUP"** button at the bottom of the window. This will create a new smaller window, with a tab for each place your file/folder will be backed up to. In this window, select the **"Start the backup"** button to begin the process.

The backup process works in two stages. First, it looks at all the files it needs to process and determine what needs to be copied over (the window will say it's "finding files" during this). After that, every file that needs to be copied will be moved over. It will work one backup at a time down the list of tabs on the small window.

If you've already done this backup previously, the process will only find files that are new, changed, or no longer in the backup and only modify those files. This will make subsequent backups of the same file/folder much faster than the first.

The window will show you what file it's currently working with, how many files it will be modifying, and the size of the backup. Once a backup is done, it will also show how long it took and the size difference between this backup and the most recent previous version of this backup. If you want more details, you can check the **log file**. A log file is generated on every backup you run, and shows a complete list of what files were modified and what was done with them. You can find your log file in the /logs/ directory in the same directory you installed this program to. Log file names contain the date and time when the backup was started, so they will be ordered by when the backup was done.

You may encounter an error during a backup. This can commonly happen if it tries to back up a file it does not have permission to move or modify. The window will show how many errors occurred, and for further information you can find exact details of the error in the log file. Most of the time errors will come from hidden files that you didn't mean to back up (such as desktop.ini files on Windows), so these can be fixed by simply excluding them (discussed later). For other more serious errors, feel free to contact me.

## Further Build the Configuration

### Create a second entry  

For more complex configurations, you will want multiple entries in order to back up multiple files/folders at once. After your first entry is created, select the **"New Entry"** button on the left side of the window to bring up a blank entry. From here, instructions are the same as when you created your first entry. Setting the "input" creates the entry, and you can keep going back to the **"New Entry"** button to create more.

### Save/load your configuration

Configurations can be saved and loaded to make doing a backup as simple as opening the program, loading your configuration, and hitting Backup. To save, go to the **"File"** menu on the top of the window and select **"Save configuration as..."**. This will allow you to name the configuration, and will give you a confirmation saying it was successfully saved.

Once it is saved, you will notice the next on the very top-left of the window change to display your configuration's name. As you make modifications to your configuration in the future, an asterisk (*) will appear beside the name. This indicates changes were made since the last save, so simply go to **File > Save configuration** to update the saved file.

Use the **File > Load configuration** option to load a saved configuration. This will bring up a list of saved configurations; simply click on the one you'd like to load and it will be loaded in. If you would instead like to delete a saved configuration file, you can also do that from the load window. In that window, right-click on the name of a saved configuration and select "Delete" to remove it from the list and delete it's file.

### Configuration limits

Configurations cannot have an unlimited number of entries, as that would allow configuration file sizes to grow out of control if unchecked and would bog down the system. A configuration can have at most 50 entries. Each of these entries is limited to only one "input" as usual, and 50 "outputs" as locations where the backup will be made. Each entry can also feature up to 100 exclusions. Each exclusion can then itself have up to 100 limitations. Exclusions and limitations will be discussed in the next section.
  
## Advanced Configuration Options  

### Exclusions

You can further customize your backup configuration with Exclusions and Limitations. Once you have an entry created, navigate to the **Exclusions** tab near the top of the window. This will change the window to display two columns.

Exclusions are rules for the backup that tell it which files, if any, should be excluded from the backup. On the Exclusions tab, press the **"Create a new exclusion"** button near the bottom of the window to see a list of exclusion rules. Select one of those rules, and another window will open up allowing you to input data for that rule. For instance, if you select the "Starts with some text" rule, then input "data_" into the text box on the smaller window and press Create, all files and folders in your backup whose name begins with "data_" will not be backed up. Creating an exclusion creates a button for it in the left column of the **Exclusions** tab. Each exclusion rule goes more in-depth on what they do and have different means of user input on their respective creation windows, so be sure to try multiple ones out.

Once an exclusion is created, you can see which files and folders will be excluded on the left file tree in the **Inputs and Outputs** tab. Navigate through the tree to find a file that fits the exclusion rules you wrote, and you will notice its name is greyed out. Editing and deleting exclusions is also simple. Simply right-click on the exclusion button you'd like to modify, where you can find Edit and Delete commands.

### Limitations

Limitations are extensions of exclusions. A limitation limits where the rules of its exclusion take effect. Once you create an exclusion, click on the resulting button in the left column to highlight it. Now, the **"Add a limitation to this exclusion"** button becomes accessible, and clicking on it results in a similar list of rules to the exclusions list. Clicking on a rule will bring up another small window almost identical to the one you used to make an exclusion, and after inputting data and pressing the Create button, the limitation will appear in the right column. Editing and deleting limitations works exactly the same as for exclusions.

As an example of how limitations work, imagine you give your "file name starts with data_" exclusion a limitation that says limit this exclusion to the directory "C:\folder1" and all subdirectories. Now, only files whose name starts with "data_" and who are somewhere within C:\folder1 will be excluded. If a file that starts with "data_" is instead in C:\folder2, that file will not be excluded.

### Miscellaneous

This application offers multiple ways to get a desired configuration for a backup. For instance, if you would like to back up a folder to multiple different drives, but some drives aren't large enough to fit the entire thing, you can set up multiple entries for that same folder, and simply apply different exclusions to each. Another way this is possible is with the "drive" limitation, which works differently from other limitations. This limitation is only applied during the backup process, and makes its exclusion only work when you are backing something up to the drive letter you gave it. As an example of that, imagine you are doing a backup to the D: and E: drives, with the exclusion that says file names starting with "data_" will be excluded. When you give a drive limitation to that exclusion and give it the "D:" drive, now your backups to both drives will be slightly different. Files starting with "data_" will not appear in the backup on the "D:" drive, but they will appear on the backup on the "E:" drive.