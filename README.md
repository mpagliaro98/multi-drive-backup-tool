# Multi-Drive Backup Tool

Author: Michael Pagliaro

This is a Python tool to configure and automate file backups to local drives. It allows you to create detailed configurations of which files/folders you want to back up, where to back them up to, and which files if any you would like excluded from the backup. Once all your files are configured, you can back them all up with a single button press. On subsequent backups, only the files that are new or have changed will be backed up, allowing the process to be much quicker during future backups.

There are three versions of this application which allow it to be interfaced with in different ways.
1. The GUI (graphical user interface) displays the application in a window, and is the simplest and most user-friendly option.
2. The CLI (command line interface) offers a menu on the command line to interface with the application.
3. The Command Line Argument Interface has no front-end, instead allowing users to pass arguments in through the command line to use features of the program.

## Download and Install

**NOTE:** This was only developed and tested on Windows, so usage on Linux or OSX is not supported.

To download and use this program, download the latest [release](https://github.com/mpagliaro98/multi-drive-backup-tool/releases). An option will be available for each version of the program. The GUI version's download ends in `-gui`, `-cli` for the CLI, and `-cmd` for the command line argument interface.

The GUI and CLI versions come as .msi installers which will install the program as a .exe file.

The command line argument interface comes instead in a .zip archive, so once you extract it somewhere you can access it by running `python mdbt.py` in a command line.

## How to Use

For detailed usage instructions for each version, see their corresponding usage documents.
* GUI version - [USAGE_GUI.md](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_GUI.md)
* CLI version - [USAGE_CLI.md](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_CLI.md)
* Command Line Argument version - [USAGE_CMD.md](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/USAGE_CMD.md)

## Building the Executable Yourself

This program is packaged as a standalone .exe file and distributed in an installer in the Releases section. To create this yourself, you must have pyinstaller (download from pip) and Inno Setup on your system. Then download this entire repository anywhere on your system. You will also need [zipjs.bat](https://github.com/npocmaka/batch.scripts/blob/master/hybrids/jscript/zipjs.bat), hosted by npocmaka on Github, and place that file inside the deploy/ directory. All you have to do from there is run build.bat from the command line and supply it one command line argument, being the version number you want to give the application. The script will create the three distributions found on each release in the Releases section and put them in a Releases folder in the base of the downloaded repository. If you run into problems with Inno Setup, edit the path to ISCC.exe in build.bat to where it is located on your system.

## License

MIT License

See [the license document](https://github.com/mpagliaro98/multi-drive-backup-tool/blob/master/LICENSE) for details.
