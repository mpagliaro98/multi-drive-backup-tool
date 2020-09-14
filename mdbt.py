"""
mdbt.py
Author: Michael Pagliaro
The command line argument interface. This is one possible entry-point to the application which allows users
to interface with it by passing command line arguments in order to run different functions of the program.
"""


import sys


def main():
    """
    The main entry-point for this command line argument interface. This will check which arguments were entered
    and run the appropriate functions for each.
    """
    num_args = len(sys.argv)
    args = sys.argv
    print("Unimplemented.")


if __name__ == "__main__":
    main()
