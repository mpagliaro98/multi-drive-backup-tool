# Multi-Drive Backup Tool

Author: Michael Pagliaro

This is a Python tool to configure and automate file backups to local drives. It allows you to create detailed configurations of which files/folders you want to back up and where to back them up to. Once all your files are configured, you can back them all up with a single button press. On subsequent backups, only the files that are new or have changed will be backed up, allowing the process to be much quicker during future backups.

## Requirements and Running

This was coded using Python 3.8, and as such requires Python 3.8 or higher to be used. [Download Python here.](https://www.python.org/downloads/)

To download this program, download the latest [release](https://github.com/mpagliaro98/multi-drive-backup-tool/releases) or simply download the current source code. Make sure all the .py files are unzipped and in their own directory, as this program will create its own files. Double-clicking multi-drive-backup-tool.py or by running `python multi-drive-backup-tool.py` from its directory in a command line or terminal will allow it to run.

## How to Use It

Upon running the program, you will be presented with a menu of options.
```
1: Select a folder or file to backup
2: Configure destination locations
3: Edit/delete configuration entries
4: Save current backup configuration
5: Load a backup configuration
6: Backup your files
7: Re-scan for available drives
8: Exit
```
To begin, you can specify a folder or file you'd like backed up by choosing **Option 1**. This will let you enter the absolute path to a folder or file.

To specify where you want that folder or file to be backed up to, use **Option 2**. You can enter several paths to folders here at once. The folder or file that you specified in **Option 1** will be copied to the folders you specify in **Option 2**.

If you made a mistake in the previous steps, you can edit your paths by using **Option 3**. Before you start the backup process, it's a good idea to use **Option 4** to save your configuration, so when you want to update your backup at a later date, you can load what you entered quickly with **Option 5**.

Once you've specified everything you'd like to backup, start the process with **Option 6**. This will copy all of the contents of the folder of file you specified in **Option 1** to every folder you specified in **Option 2**, and will create folders with the suffix "BACKUP" to store the backups. For instance, if you want to backup a folder called "My Folder", the program will create a folder called "My Folder BACKUP" at the destination and copy all the files into there. Once the backup is complete, it will also place a file called `_BACKUP-CONFIRMATION.txt` into the backed-up folder that says when the backup was last run. If you want to see exactly what files were copied/modified during the process, or if something went wrong, you can check the backup log file that was created in the `logs` directory. This directory will be in the folder where you ran this program.

## License
MIT License

See LICENSE.md for details.
