"""
mdbt_gui.py
Author: Michael Pagliaro
The graphical user interface. This is one possible entry-point to the application which gives users a visual
interface for the program.
"""


import tkinter as tk
from tkinter import ttk
import fileview
import scrollable_frame as sf
import configuration


class Application:
    """
    The main GUI application. This class contains all functionality for the main window and any
    sub-windows it creates.
    """

    def __init__(self, master):
        """
        Initialize the master application by creating the initial configuration object, creating the base
        frame, and initializing all other items on the window.
        :param master: The master widget this application will be in. Should be a Tk object.
        """
        self.master = master
        self.config = configuration.load_config("subs test")#configuration.Configuration()
        self.current_entry_number = 1
        self.base = tk.Frame(self.master)
        self.init_menu()
        self.init_tabs()
        self.init_entry_buttons()
        self.init_fileviews()
        self.init_labels()
        self.init_input_output_frames()
        self.init_buttons()
        self.configure_grid()
        self.base.pack(fill=tk.BOTH, expand=True)

    def init_menu(self):
        """
        Initialize the menu options at the top of the window.
        """
        self.menu = tk.Menu(self.base)
        self.menu_file = tk.Menu(self.menu, tearoff=0)
        self.menu_file.add_command(label="Save configuration")
        self.menu_file.add_command(label="Save configuration as...")
        self.menu_file.add_command(label="Load configuration", command=self.load_configuration)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Exit", command=self.master.quit)
        self.menu.add_cascade(label="File", menu=self.menu_file)
        self.menu_help = tk.Menu(self.menu, tearoff=0)
        self.menu_help.add_command(label="About")
        self.menu_help.add_command(label="GitHub page")
        self.menu.add_cascade(label="Help", menu=self.menu_help)
        self.master.config(menu=self.menu)

    def init_tabs(self):
        """
        Create the inputs and exclusions tabs and their respective frames.
        """
        self.tabs = ttk.Notebook(self.base)
        self.tab_inputs = ttk.Frame(self.tabs)
        self.tab_exclusions = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_inputs, text="Inputs and Outputs")
        self.tabs.add(self.tab_exclusions, text="Exclusions")
        self.tabs.grid(row=1, column=1, sticky=tk.NSEW)

    def init_entry_buttons(self):
        """
        Create the frame for buttons on the left side of the window which will represent configuration entries.
        """
        self.entries_frame = sf.ScrollableFrame(self.base)
        button = tk.Button(self.entries_frame.master_create, text="New Entry",
                           command=lambda: self.set_fields_to_entry(self.config.num_entries()+1))
        button.pack(ipadx=10, ipady=10)
        self.entries_frame.master.update()
        self.entries_frame.register_widget(button)
        self.entries_frame.grid(row=1, column=0, rowspan=2, sticky=tk.NS+tk.W)

    def init_fileviews(self):
        """
        Create the Fileview trees that display file paths.
        """
        self.input_tree = fileview.Fileview(master=self.tab_inputs)
        self.input_tree.grid(column=0, row=2, pady=10, sticky=tk.NSEW)
        self.output_tree = fileview.Fileview(master=self.tab_inputs)
        self.output_tree.grid(column=1, row=2, pady=10, sticky=tk.NSEW)

    def init_buttons(self):
        """
        Create various buttons on the window, including the backup button and the buttons below each Fileview.
        """
        # Create the backup button
        self.backup_button = tk.Button(self.base, text="BACKUP")
        self.backup_button.grid(row=2, column=1, pady=10, ipadx=60, ipady=10)

        # Create the buttons below the Fileviews
        self.input_button = tk.Button(self.tab_inputs, text="Set highlighted path to input",
                                      command=lambda: print(self.input_tree.get_focus_path()))
        self.input_button.grid(column=0, row=3)
        self.output_button = tk.Button(self.tab_inputs, text="Add highlighted path as output",
                                       command=lambda: print(self.output_tree.get_focus_path()))
        self.output_button.grid(column=1, row=3)

    def init_labels(self):
        """
        Create various labels on the window, including the configuration name label and ones for inputs
        and outputs.
        """
        self.config_name_label = ttk.Label(self.base, text="The current configuration has not been saved yet.")
        self.config_name_label.grid(row=0, columnspan=2, sticky=tk.NW)

        # Add labels above the input and output frames
        ttk.Label(self.tab_inputs, text="BACKUP").grid(column=0, row=0, padx=10, pady=10, sticky=tk.NW)
        ttk.Label(self.tab_inputs, text="COPY TO").grid(column=1, row=0, padx=10, pady=10, sticky=tk.NW)
        ttk.Label(self.tab_exclusions, text="exclusions tab").grid(column=0, row=0, padx=30, pady=30)

    def init_input_output_frames(self):
        """
        Create the scrollable frames that will hold input and output paths.
        """
        self.input_frame = sf.ScrollableFrame(self.tab_inputs, initial_width=-1,
                                              initial_height=50, dynamic_width=False)
        self.input_frame.grid(column=0, row=1, sticky=tk.NSEW)
        self.output_frame = sf.ScrollableFrame(self.tab_inputs, initial_width=-1,
                                               initial_height=50, dynamic_width=False)
        self.output_frame.grid(column=1, row=1, sticky=tk.NSEW)

    def configure_grid(self):
        """
        Configure the window's base grid to control what scales on resize. This will allow the Fileviews to
        change size while the other objects remain the same size.
        """
        self.base.rowconfigure(1, weight=1)
        self.base.columnconfigure(1, weight=1)
        self.tab_inputs.rowconfigure(2, weight=1)
        self.tab_inputs.columnconfigure(0, weight=1)
        self.tab_inputs.columnconfigure(1, weight=1)

    def load_configuration(self):
        pass

    def reset_entry_buttons(self):
        """
        Resets the entry button scrollable frame. This will clear the widget, then re-add the "New Entry"
        button to it.
        """
        self.entries_frame.clear_widgets()
        button = tk.Button(self.entries_frame.master_create, text="New Entry",
                           command=lambda: self.set_fields_to_entry(self.config.num_entries()+1))
        button.pack(ipadx=10, ipady=10)
        self.entries_frame.master.update()
        self.entries_frame.register_widget(button)

    def update_config_name_label(self):
        """
        Changes the configuration name label to show the name of the current configuration. If the current
        configuration is empty, it will say the current configuration isn't saved.
        """
        if self.config.is_empty():
            self.config_name_label.configure(text="The current configuration has not been saved yet.")
        else:
            self.config_name_label.configure(text="Current Configuration: {}".format(self.config.name))

    def set_fields_to_entry(self, entry_number):
        """
        Updates the UI fields to display info of a given configuration entry. This will show the input path,
        every output path, and display the input path in the Fileview. If the entry number provided is out of
        range, the fields will just be cleared.
        :param entry_number: The number of the entry to display. If this number doesn't correspond to a valid
                             entry, the fields will just be cleared. Starts indexing from 1.
        """
        # Clear the entry fields and record the entry number
        self.clear_fields()
        self.current_entry_number = entry_number

        # Only display entry info if it's a valid entry number. Otherwise just clear the fields
        if 0 < entry_number <= self.config.num_entries():
            # Add the input path to the input scrollable frame
            input_label = tk.Message(self.input_frame.master_create, text=self.config.get_entry(entry_number).input,
                                     width=400)
            input_label.pack()
            self.input_frame.master.update()
            self.input_frame.register_widget(input_label)

            # Set the input tree to display the input
            self.input_tree.travel_to_path(self.config.get_entry(entry_number).input)

            # Add every output path to the output scrollable frame
            for output in self.config.get_entry(entry_number).outputs:
                output_label = tk.Message(self.output_frame.master_create, text=output, width=400)
                output_label.pack()
                self.output_frame.master.update()
                self.output_frame.register_widget(output_label)

    def clear_fields(self):
        """
        Clear the UI fields associated with individual entries. This will remove all content from the input and
        output scrollable frames, as well as reset the input Fileview to its starting position. The output
        Fileview does not get reset so that the user can quickly give several entries the same output.
        """
        self.input_frame.clear_widgets()
        self.output_frame.clear_widgets()
        self.input_tree.reset()


def main():
    """
    The main entry-point for this graphical user interface. This will display an interface for the user
    to be able to interact with the application.
    """
    root = tk.Tk()
    root.title("Multi-Drive Backup Tool")
    root.geometry("1000x650")
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
