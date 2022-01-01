# Script that helps build.bat automate the process of releasing a new version

import sys


def main():
    if len(sys.argv) != 3:
        print("USAGE: iss_update_version.py iss_file version_number")
        exit()
    args = sys.argv
    iss_filename = args[1]
    version_number = args[2]
    file = open(iss_filename, 'r')
    lines = file.readlines()
    output = []
    for line in lines:
        line = line.strip()
        if line.startswith("#define MyAppVersion "):
            line = "#define MyAppVersion \"" + str(version_number) + "\""
        output.append(line + "\n")
    file.close()

    file = open(iss_filename, 'w')
    file.writelines(output)
    file.close()


if __name__ == "__main__":
    main()
