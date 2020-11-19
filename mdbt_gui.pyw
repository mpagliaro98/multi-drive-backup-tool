"""
mdbt_gui.py
Author: Michael Pagliaro
The graphical user interface. This is one possible entry-point to the application which gives users a visual
interface for the program.
"""


import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import webbrowser
import fileview
import scrollable_frame as sf
import tooltip as tt
import configuration
import util
import backup_asyncio
import exclusions
import limitations
from configuration import InvalidPathException, SubPathException, CyclicEntryException
from exclusions import EXCLUSION_TYPES
from limitations import LIMITATION_TYPES


def highlight(event):
    """
    When called by an event, this will highlight the widget called. If it's already highlighted, this
    will remove the highlight.
    :param event: The event that was triggered.
    """
    event.widget.configure(bg='SystemButtonFace' if event.widget['bg'] == 'blue' else 'blue')


class MdbtMessage(tk.Message):
    """
    A class that creates a tkinter message with settings usable by this application.
    """

    def __init__(self, text, frame, popup_members=None):
        """
        Create a label that will be put in a scrollable frame, using this program's settings for how labels
        should look.
        :param text: The text to display.
        :param frame: The scrollable frame to put this text in.
        :param popup_members: A list of tuples containing a string and a function each. Each item in the list will be
                              made into a menu item that will appear when the button is right-clicked.
        """
        super().__init__(frame.master_create, text=text, anchor=tk.W)
        if popup_members is None:
            popup_members = []
        self.frame = frame
        self.popup_members = popup_members
        if len(self.popup_members) > 0:
            self.bind("<Button-1>", highlight)
            self.bind("<Button-3>", self.right_click_popup)
        self.pack(fill=tk.BOTH)
        frame.master.update()
        frame.register_widget(self)

    def change_popup_function(self, member_name, new_function):
        """
        Change what function runs when an item on this message's right click menu is called. The function to change
        is specified by member_name.
        :param member_name: The name of the member whose function to change.
        :param new_function: The new function run when the right-click command is executed.
        """
        for member_idx in range(len(self.popup_members)):
            if self.popup_members[member_idx][0] == member_name:
                self.popup_members[member_idx] = (member_name, new_function)

    def right_click_popup(self, event):
        """
        When called by an event, this will display a menu by the mouse cursor with a delete option.
        :param event: The event that was triggered.
        """
        highlight(event)
        m = tk.Menu(self.frame.master, tearoff=0)
        for member in self.popup_members:
            m.add_command(label=member[0], command=member[1])
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()
        highlight(event)


class MdbtButton(tk.Button):
    """
    A class that creates a tkinter button with settings usable by this application.
    """

    def __init__(self, text, frame, command=lambda: None, ipadx=0, ipady=0, popup_members=None):
        """
        Create a button that will be put in a scrollable frame, using this program's settings for how buttons
        should look.
        :param text: The text that goes in the button.
        :param frame: The scrollable frame to add this button to.
        :param command: Optional parameter, a function run when this button is pressed. Does nothing if not specified.
        :param ipadx: Optional parameter, horizontal padding between the text and the button sides. Defaults to 0.
        :param ipady: Optional parameter, vertical padding between the text and the button edges. Defaults to 0.
        :param popup_members: A list of tuples containing a string and a function each. Each item in the list will be
                              made into a menu item that will appear when the button is right-clicked.
        """
        self.hack_image = tk.PhotoImage(width=1, height=1)
        super().__init__(frame.master_create, text=text, image=self.hack_image, compound=tk.CENTER, command=command)
        if popup_members is None:
            popup_members = []
        self.frame = frame
        self.popup_members = popup_members
        if len(self.popup_members) > 0:
            self.bind("<Button-3>", self.right_click_popup)
        self.pack(ipadx=ipadx, ipady=ipady)
        frame.master.update()
        frame.register_widget(self)

    def change_popup_function(self, member_name, new_function):
        """
        Change what function runs when an item on this button's right click menu is called. The function to change
        is specified by member_name.
        :param member_name: The name of the member whose function to change.
        :param new_function: The new function run when the right-click command is executed.
        """
        for member_idx in range(len(self.popup_members)):
            if self.popup_members[member_idx][0] == member_name:
                self.popup_members[member_idx] = (member_name, new_function)

    def right_click_popup(self, event):
        """
        When called by an event, this will display a menu by the mouse cursor with a delete option.
        :param event: The event that was triggered.
        """
        m = tk.Menu(self.frame.master, tearoff=0)
        for member in self.popup_members:
            m.add_command(label=member[0], command=member[1])
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()


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
        self.config = configuration.Configuration()
        self.current_entry_number = 1
        self.current_exclusion_number = 0
        self.base = tk.Frame(self.master)
        self.init_menu()
        self.init_tabs()
        self.init_entry_buttons()
        self.init_fileviews()
        self.init_labels()
        self.init_input_output_frames()
        self.init_exclusion_frames()
        self.init_buttons()
        self.configure_grid()
        self.base.pack(fill=tk.BOTH, expand=True)
        self.set_fields_to_entry(self.current_entry_number)

    def init_menu(self):
        """
        Initialize the menu options at the top of the window.
        """
        self.menu = tk.Menu(self.base)
        self.menu_file = tk.Menu(self.menu, tearoff=0)
        self.menu_file.add_command(label="Save configuration", command=self.save_configuration)
        self.menu_file.add_command(label="Save configuration as...", command=self.save_configuration_as)
        self.menu_file.add_command(label="Load configuration", command=self.load_configuration)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Exit", command=self.master.quit)
        self.menu.add_cascade(label="File", menu=self.menu_file)
        self.menu_edit = tk.Menu(self.menu, tearoff=0)
        self.menu_edit.add_command(label="Delete current entry", command=self.delete_entry)
        self.menu_edit.add_command(label="Delete highlighted outputs", command=self.delete_highlighted_destinations)
        self.menu_edit.add_command(label="Delete all exclusions on the current entry",
                                   command=self.delete_entry_exclusions)
        self.menu_edit.add_command(label="Delete all limitations on the current exclusion",
                                   command=self.delete_exclusion_limitations)
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label="Clear configuration", command=self.clear_configuration)
        self.menu.add_cascade(label="Edit", menu=self.menu_edit)
        self.menu_help = tk.Menu(self.menu, tearoff=0)
        self.menu_help.add_command(label="About")
        self.menu_help.add_command(label="How to use")
        self.menu_help.add_command(label="GitHub page", command=lambda: webbrowser.open(
            "https://github.com/mpagliaro98/multi-drive-backup-tool"))
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
        self.add_new_entry_button()
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
        self.backup_button = tk.Button(self.base, text="BACKUP", command=self.backup)
        self.backup_button.grid(row=2, column=1, pady=10, ipadx=60, ipady=10)

        # Create the buttons below the Fileviews
        self.input_button = tk.Button(self.tab_inputs, text="Set highlighted path to input", command=self.set_input)
        self.input_button.grid(column=0, row=3)
        self.output_button = tk.Button(self.tab_inputs, text="Add highlighted path as output", command=self.add_output)
        self.output_button.grid(column=1, row=3)

        # Create the buttons below the scrollable frames in the exclusions tab
        self.exclusion_button = tk.Button(self.tab_exclusions, text="Create a new exclusion",
                                          command=self.create_exclusion_menu)
        self.exclusion_button.grid(column=0, row=2)
        self.limitation_button = tk.Button(self.tab_exclusions, text="Add a limitation to this exclusion",
                                           command=self.create_limitation_menu)
        self.limitation_button.grid(column=1, row=2)

    def init_labels(self):
        """
        Create various labels on the window, including the configuration name label and ones for inputs
        and outputs.
        """
        self.config_name_label = ttk.Label(self.base, text="The current configuration has not been saved yet.")
        self.config_name_label.grid(row=0, columnspan=2, sticky=tk.NW)

        # Add labels above the input and output frames
        self.input_label = ttk.Label(self.tab_inputs, text="BACKUP", font="Helvetica 12 bold")
        self.input_label.grid(column=0, row=0, padx=5, pady=10, sticky=tk.NW)
        tt.Tooltip(self.input_label, text="The file or folder you want to backup will be displayed in this section. " +
                   "Navigate through the file tree below to find what you want to backup, then once it's highlighted" +
                   ", press the \"Set highlighted path to input\" button. This will create a new entry for the thing " +
                   "you are backing up. To edit this later, use the same process to select a new file or folder.")
        self.output_label = ttk.Label(self.tab_inputs, text="COPY TO", font="Helvetica 12 bold")
        self.output_label.grid(column=1, row=0, padx=5, pady=10, sticky=tk.NW)
        tt.Tooltip(self.output_label, text="The folders your backup will be made in will be displayed in this " +
                   "section. Similar to the section to the left, select a folder in the file tree below, then press " +
                   "the \"Add highlighted path as output\" button to make it a location a backup will be made. You " +
                   "can add multiple unique locations for a single input. To remove a location, right click on it " +
                   "in the scroll-box below and press \"Delete\", or highlight multiple by left-clicking them and " +
                   "select \"Delete highlighted outputs\" in the Edit menu.")

        # Add labels above the exclusion and limitation frames
        self.exclusion_label = ttk.Label(self.tab_exclusions, text="EXCLUSIONS", font="Helvetica 12 bold")
        self.exclusion_label.grid(column=0, row=0, padx=5, pady=10, sticky=tk.NW)
        tt.Tooltip(self.exclusion_label, text="Exclude particular files and folders from your backup using various " +
                   "rules defined below. Click the exclusion button below, choose one of the options for what kinds " +
                   "of files to exclude, then fill in data on the resulting window. Exclusions are limited to their " +
                   "respective entries they were created under. Files that have been excluded will appear greyed-out " +
                   "in the file tree under the \"BACKUP\" text on the inputs tab.")
        self.limitation_label = ttk.Label(self.tab_exclusions, text="LIMITATIONS", font="Helvetica 12 bold")
        self.limitation_label.grid(column=1, row=0, padx=5, pady=10, sticky=tk.NW)
        tt.Tooltip(self.limitation_label, text="Limitations can be applied to exclusions to limit their effects to a " +
                   "smaller subset of files. Once an exclusion is created, click on it to highlight it, then use the " +
                   "limitation button below to create one in the same way exclusions are created.")

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

    def init_exclusion_frames(self):
        """
        Create the scrollable frames that will hold exclusions and limitations.
        """
        self.exclusion_frame = sf.ScrollableFrame(self.tab_exclusions, initial_width=-1, dynamic_width=False)
        self.exclusion_frame.grid(column=0, row=1, sticky=tk.NSEW)
        self.limitation_frame = sf.ScrollableFrame(self.tab_exclusions, initial_width=-1, dynamic_width=False)
        self.limitation_frame.grid(column=1, row=1, sticky=tk.NSEW)

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
        self.tab_exclusions.rowconfigure(1, weight=1)
        self.tab_exclusions.columnconfigure(0, weight=1)
        self.tab_exclusions.columnconfigure(1, weight=1)

    def save_configuration(self):
        """
        Functionality for saving an existing configuration. If this configuration has yet to be saved, this
        will run the Save As function. Otherwise, it will save and update the current configuration's file.
        """
        if not configuration.config_exists(self.config.name):
            self.save_configuration_as()
        else:
            configuration.save_config(self.config, self.config.name)
        self.update_config_name_label()

    def save_configuration_as(self):
        """
        Functionality for saving a new configuration file. This will prompt the user to enter a name for
        the configuration, then ask to overwrite if it already exists, and then save it.
        """
        def save_window_response(app):
            """
            Inner function for the save window. This will receive the text entered in the save window,
            then destroy the save window.
            :param app: The Application object that this window was spawned from.
            """
            if not app.save_entry.get() == "":
                app.save_name = app.save_entry.get()
            app.save_window.destroy()

        # Create the save window and prompt for a name, don't resume main window until this is done
        self.save_name = None
        self.save_window = tk.Toplevel(self.master)
        self.save_window.wm_title("Save Configuration")
        tk.Label(self.save_window, text="Enter a name for this configuration:").pack()
        self.save_entry = tk.Entry(self.save_window)
        self.save_entry.pack()
        tk.Button(self.save_window, text="Save", command=lambda: save_window_response(self)).pack()
        self.save_window.grab_set()
        self.master.wait_window(self.save_window)
        self.save_window.grab_release()

        # If a name was entered, attempt to save it
        if self.save_name is not None:
            # Ask to overwrite if it shares a name with an existing configuration
            if configuration.config_exists(self.save_name):
                mbox = messagebox.askyesno("Overwrite", "A configuration named " + self.save_name +
                                           " already exists. Would you like to overwrite it?")
                if mbox == tk.NO:
                    return
            self.config.name = self.save_name
            configuration.save_config(self.config, self.save_name)
            self.update_config_name_label()
            messagebox.showinfo("Configuration Saved", self.save_name + ".dat was successfully saved to the " +
                                configuration.CONFIG_DIRECTORY + " directory.")

    def load_configuration(self):
        """
        Functionality for loading a configuration. This will display a sub-window with buttons for each
        valid configuration, and if one is selected, the window will update to load that configuration.
        """
        def load_window_response(app, config_list_idx):
            """
            Inner function for the load window. This will receive a response from a button pressed on the
            load window, save the result of what was selected, and then destroy the load window.
            :param app: The Application object this window was spawned from.
            :param config_list_idx: The index into the config name list that this button had.
            """
            app.config_name = app.config_name_list[config_list_idx]
            app.load_window.destroy()

        def load_window_delete(app, config_list_idx):
            """
            Inner function for the load window. This will be called when the delete option on one of the
            buttons is pressed, and will delete that configuration file from the system.
            :param app: The Application object this window was spawned from.
            :param config_list_idx: The index into the config name list that this button had.
            """
            configuration.delete_config(app.config_name_list[config_list_idx])
            if app.config.name == app.config_name_list[config_list_idx]:
                app.config.name = None
            app.config_load_frame.remove_widget(config_list_idx)
            app.config_name_list = configuration.saved_config_display_string().strip().split("\n")
            for widget_idx in range(config_list_idx, len(app.config_load_frame.widgets)):
                app.config_load_frame.edit_command_on_widget(widget_idx,
                                                             lambda i=widget_idx: load_window_response(app, i))
                app.config_load_frame.widgets[widget_idx].change_popup_function(
                    "Delete", lambda i=widget_idx: load_window_delete(app, i))
            app.update_config_name_label()

        # Create the load window
        self.config_name = None
        self.load_window = tk.Toplevel(self.master)
        self.load_window.wm_title("Load Configuration")
        self.load_window.geometry("300x300")
        self.config_name_list = configuration.saved_config_display_string().strip().split("\n")
        self.config_load_frame = sf.ScrollableFrame(self.load_window, dynamic_width=False)

        # Create a button for every saved configuration
        for name_idx in range(len(self.config_name_list)):
            MdbtButton(self.config_name_list[name_idx], self.config_load_frame,
                       command=lambda i=name_idx: load_window_response(self, i), ipadx=5, ipady=5,
                       popup_members=[("Delete", lambda i=name_idx: load_window_delete(self, i))])
        self.config_load_frame.pack(fill=tk.BOTH, expand=True)
        self.load_window.grab_set()
        self.master.wait_window(self.load_window)
        self.load_window.grab_release()

        # If an option was chosen, load it in
        if self.config_name is not None:
            self.config = configuration.load_config(self.config_name)
            self.update_config_name_label()
            self.update_output_label()
            self.reset_entry_buttons()
            for entry_number in range(1, self.config.num_entries()+1):
                self.create_entry_button(entry_number)
            self.set_fields_to_entry(1)

    def clear_configuration(self):
        """
        Functionality for clearing a configuration. This will set the application's current configuration to
        a new empty one, as well as reset all fields in the UI.
        """
        self.config = configuration.Configuration()
        self.update_config_name_label()
        self.update_output_label()
        self.reset_entry_buttons()
        self.set_fields_to_entry(1)

    def reset_entry_buttons(self):
        """
        Resets the entry button scrollable frame. This will clear the widget, then re-add the "New Entry"
        button to it.
        """
        self.entries_frame.clear_widgets()
        self.add_new_entry_button()

    def update_config_name_label(self):
        """
        Changes the configuration name label to show the name of the current configuration. If the current
        configuration is empty, it will say the current configuration isn't saved. If the current configuration
        is different from its saved version, it will display an asterisk next to its name.
        """
        if not configuration.config_exists(self.config.name):
            self.config_name_label.configure(text="The current configuration has not been saved yet.")
        else:
            if configuration.config_was_modified(self.config):
                self.config_name_label.configure(text="Current Configuration: {}*".format(self.config.name))
            else:
                self.config_name_label.configure(text="Current Configuration: {}".format(self.config.name))

    def update_output_label(self):
        """
        Update the "copy to" label to display how many destinations the current entry has.
        """
        if self.current_entry_number > self.config.num_entries():
            self.output_label.configure(text="COPY TO")
        elif self.config.get_entry(self.current_entry_number).num_destinations() == 0:
            self.output_label.configure(text="COPY TO")
        elif self.config.get_entry(self.current_entry_number).num_destinations() == 1:
            self.output_label.configure(text="COPY TO (1 location)")
        else:
            self.output_label.configure(text="COPY TO ({} locations)".format(self.config.get_entry(
                self.current_entry_number).num_destinations()))

    def set_fields_to_entry(self, entry_number):
        """
        Updates the UI fields to display info of a given configuration entry. This will show the input path,
        every output path, and display the input path in the Fileview. If the entry number provided is out of
        range, the fields will just be cleared.
        :param entry_number: The number of the entry to display. If this number doesn't correspond to a valid
                             entry, the fields will just be cleared. Starts indexing from 1.
        """
        # Clear the entry fields, highlight the selected button, and record the entry number
        self.clear_fields()
        self.highlight_entry_button(self.current_entry_number, entry_number)
        self.current_entry_number = entry_number
        self.input_tree.set_entry(None)
        self.update_output_label()

        # Default to disabling the exclusion and limitation buttons and clearing their frame contents
        self.exclusion_button['state'] = tk.DISABLED
        self.limitation_button['state'] = tk.DISABLED
        self.exclusion_frame.clear_widgets()
        self.limitation_frame.clear_widgets()

        # Only display entry info if it's a valid entry number. Otherwise just clear the fields
        if 0 < entry_number <= self.config.num_entries():
            # Add the input path to the input scrollable frame
            MdbtMessage(self.config.get_entry(entry_number).input, self.input_frame)

            # Set the input tree to display the input
            self.input_tree.set_entry(self.config.get_entry(self.current_entry_number))
            self.input_tree.reset()
            self.input_tree.travel_to_path(self.config.get_entry(entry_number).input)

            # Add every output path to the output scrollable frame
            for output_idx in range(1, len(self.config.get_entry(entry_number).outputs)+1):
                MdbtMessage(self.config.get_entry(entry_number).get_destination(output_idx), self.output_frame,
                            popup_members=[("Delete", lambda i=output_idx: self.delete_destination(i))])

            # Add every exclusion in the exclusions tab
            for exclusion_idx in range(1, len(self.config.get_entry(entry_number).exclusions)+1):
                MdbtButton(self.config.get_entry(entry_number).get_exclusion(exclusion_idx).to_string(),
                           self.exclusion_frame, command=lambda i=exclusion_idx: self.set_exclusion_fields(i),
                           ipadx=10, ipady=10,
                           popup_members=[("Edit", lambda i=exclusion_idx: self.edit_exclusion(i)),
                                          ("Delete", lambda i=exclusion_idx: self.delete_exclusion(i))])

            # Ensure the exclusion button is enabled and set the exclusion number
            self.exclusion_button['state'] = tk.NORMAL
            self.current_exclusion_number = 0

    def set_exclusion_fields(self, excl_number):
        """
        Updates the UI fields on the exclusions tab to display information relevant to the selected exclusion.
        :param excl_number: The index of the exclusion newly selected, starting from 1.
        """
        # Highlight the proper exclusion button
        if 0 < self.current_exclusion_number <= self.config.get_entry(self.current_entry_number).num_exclusions():
            self.exclusion_frame.widgets[self.current_exclusion_number-1].configure(bg="SystemButtonFace", fg="black")
        self.exclusion_frame.widgets[excl_number-1].configure(bg="blue", fg="white")

        # Refresh old values
        self.limitation_button['state'] = tk.NORMAL
        self.current_exclusion_number = excl_number
        self.limitation_frame.clear_widgets()

        # Populate the limitation frame
        for limitation_idx in range(1, len(self.config.get_entry(self.current_entry_number).get_exclusion(
                self.current_exclusion_number).limitations)+1):
            limitation = self.config.get_entry(self.current_entry_number).get_exclusion(
                self.current_exclusion_number).get_limitation(limitation_idx)
            MdbtButton(limitation.to_string(), self.limitation_frame, ipadx=10, ipady=10,
                       popup_members=[("Edit", lambda i=limitation_idx: self.edit_limitation(i)),
                                      ("Delete", lambda i=limitation_idx: self.delete_limitation(i))])

    def delete_destination(self, dest_number):
        """
        Delete a destination from an entry in the configuration. This should be called from the right-click
        delete menu on destination labels. This will first delete the destination, then update the delete
        functions on every label that follows.
        :param dest_number: The index of the destination in that entry, starting from 1.
        """
        self.config.get_entry(self.current_entry_number).delete_destination(dest_number)
        self.output_frame.remove_widget(dest_number-1)
        for widget_idx in range(dest_number-1, len(self.output_frame.widgets)):
            self.output_frame.widgets[widget_idx].change_popup_function(
                "Delete", lambda i=widget_idx+1: self.delete_destination(i))
        self.update_config_name_label()
        self.update_output_label()

    def delete_highlighted_destinations(self):
        """
        Delete any highlighted destinations from this entry. This is called from the "Delete highlighted
        outputs" menu item under the Edit menu. If the current selected entry isn't created yet, the
        current entry has no destinations, or no destinations are highlighted, this will do nothing.
        """
        # If this entry isn't created yet or it has no destinations, do nothing
        if self.current_entry_number > self.config.num_entries():
            return
        elif self.config.get_entry(self.current_entry_number).num_destinations() == 0:
            return

        # Find which destinations are highlighted and delete them
        num_deleted = 0
        for output_idx in reversed(range(1, len(self.config.get_entry(self.current_entry_number).outputs)+1)):
            if self.output_frame.widgets[output_idx-1]['bg'] == "blue":
                self.config.get_entry(self.current_entry_number).delete_destination(output_idx)
                num_deleted += 1
        if num_deleted == 0:
            return

        # Rebuild the output frame with the remaining destinations
        self.output_frame.clear_widgets()
        for output_idx in range(1, len(self.config.get_entry(self.current_entry_number).outputs) + 1):
            MdbtMessage(self.config.get_entry(self.current_entry_number).get_destination(output_idx), self.output_frame,
                        popup_members=[("Delete", lambda i=output_idx: self.delete_destination(i))])
        self.update_config_name_label()
        self.update_output_label()

    def delete_entry(self, entry_number=0):
        """
        Delete an entry from the configuration, remove its button from the UI, and edit all the buttons after it
        so it accurately reflects the new state of the configuration.
        :param entry_number: The number of the entry to delete. By default it will delete the entry currently being
                             viewed.
        """
        # If this is used on the new entry button, don't do anything, otherwise delete the entry
        if entry_number == 0:
            entry_number = self.current_entry_number
        if entry_number > self.config.num_entries() or entry_number <= 0:
            return
        self.config.delete_entry(entry_number)

        # Delete its entry button, then update every following entry button
        self.entries_frame.remove_widget(entry_number-1)
        for widget_idx in range(entry_number-1, len(self.entries_frame.widgets)-1):
            path_split = os.path.split(self.config.get_entry(widget_idx+1).input)
            button_text = path_split[0] if path_split[1] == "" else path_split[1]
            self.entries_frame.edit_text_on_widget(widget_idx, "Entry {}\n{}".format(widget_idx+1, button_text))
            self.entries_frame.edit_command_on_widget(widget_idx, lambda i=widget_idx+1: self.set_fields_to_entry(i))
            self.entries_frame.widgets[widget_idx].change_popup_function("Delete",
                                                                         lambda i=widget_idx+1: self.delete_entry(i))
        self.entries_frame.edit_command_on_widget(self.config.num_entries(),
                                                  lambda: self.set_fields_to_entry(self.config.num_entries()+1))

        # Display the proper entry and update the UI
        if self.current_entry_number >= entry_number:
            if self.current_entry_number > entry_number:
                self.current_entry_number -= 1
            self.set_fields_to_entry(self.current_entry_number)
            self.highlight_entry_button(self.current_entry_number, self.current_entry_number)
        self.update_config_name_label()

    def delete_exclusion(self, excl_number):
        """
        Delete an exclusion from the configuration, remove its button from the UI, and update all buttons after
        it so they accurately reflect the new state of the configuration.
        :param excl_number: The index of the exclusion to delete, starting from 1.
        """
        # Delete the exclusion and its button, and update the configuration label
        self.config.get_entry(self.current_entry_number).delete_exclusion(excl_number)
        self.exclusion_frame.remove_widget(excl_number-1)
        self.update_config_name_label()
        self.input_tree.reset()
        self.input_tree.travel_to_path(self.config.get_entry(self.current_entry_number).input)

        # Update UI elements if they'll be affected by the delete
        if self.current_exclusion_number == excl_number:
            self.limitation_frame.clear_widgets()
            self.limitation_button['state'] = tk.DISABLED
        elif self.current_exclusion_number > excl_number:
            self.set_exclusion_fields(self.current_exclusion_number-1)

        # Update the command and delete functions for all buttons after the deleted one
        for widget_idx in range(excl_number-1, len(self.exclusion_frame.widgets)):
            self.exclusion_frame.edit_command_on_widget(widget_idx, lambda i=widget_idx+1: self.set_exclusion_fields(i))
            self.exclusion_frame.widgets[widget_idx].change_popup_function(
                "Delete", lambda i=widget_idx+1: self.delete_exclusion(i))
            self.exclusion_frame.widgets[widget_idx].change_popup_function(
                "Edit", lambda i=widget_idx+1: self.edit_exclusion(i))

    def delete_limitation(self, limit_number):
        """
        Delete a limitation from the configuration, remove its button from the UI, and update all buttons after
        it so they accurately reflect the new state of the configuration.
        :param limit_number: The index of the limitation to delete, starting from 1.
        """
        # Delete the limitation and its button, and update the configuration label
        self.config.get_entry(self.current_entry_number).get_exclusion(
            self.current_exclusion_number).delete_limitation(limit_number)
        self.limitation_frame.remove_widget(limit_number-1)
        self.update_config_name_label()
        self.input_tree.reset()
        self.input_tree.travel_to_path(self.config.get_entry(self.current_entry_number).input)

        # Update the delete functions for all buttons after the deleted one
        for widget_idx in range(limit_number-1, len(self.limitation_frame.widgets)):
            self.limitation_frame.widgets[widget_idx].change_popup_function(
                "Delete", lambda i=widget_idx+1: self.delete_limitation(i))
            self.limitation_frame.widgets[widget_idx].change_popup_function(
                "Edit", lambda i=widget_idx+1: self.edit_limitation(i))

    def delete_entry_exclusions(self):
        """
        If a valid entry is selected, delete all exclusions and limitations from it.
        """
        if 0 < self.current_entry_number <= self.config.num_entries():
            del self.config.get_entry(self.current_entry_number).exclusions
            self.exclusion_frame.clear_widgets()
            self.limitation_frame.clear_widgets()
            self.update_config_name_label()
            self.limitation_button['state'] = tk.DISABLED

    def delete_exclusion_limitations(self):
        """
        If a valid exclusion is selected, delete all limitations from it.
        """
        if 0 < self.current_entry_number <= self.config.num_entries():
            if 0 < self.current_exclusion_number <= self.config.get_entry(self.current_entry_number).num_exclusions():
                del self.config.get_entry(self.current_entry_number).get_exclusion(
                    self.current_exclusion_number).limitations
                self.limitation_frame.clear_widgets()
                self.update_config_name_label()

    def clear_fields(self):
        """
        Clear the UI fields associated with individual entries. This will remove all content from the input and
        output scrollable frames, as well as reset the input Fileview to its starting position. The output
        Fileview does not get reset so that the user can quickly give several entries the same output.
        """
        self.input_frame.clear_widgets()
        self.output_frame.clear_widgets()
        self.input_tree.reset()

    def create_entry_button(self, entry_number):
        """
        Create a new button in the entry button list, which will be added to the bottom of the list but
        just above the "New Entry" button.
        :param entry_number: The number of the configuration entry this button points to.
        """
        # Remove the "New Entry" button
        self.entries_frame.remove_widget(len(self.entries_frame.widgets)-1)

        # Create a button for the given entry number
        path_split = os.path.split(self.config.get_entry(entry_number).input)
        button_text = path_split[0] if path_split[1] == "" else path_split[1]
        MdbtButton("Entry {}\n{}".format(entry_number, button_text), self.entries_frame,
                   command=lambda: self.set_fields_to_entry(entry_number), ipadx=10, ipady=10,
                   popup_members=[("Delete", lambda i=entry_number: self.delete_entry(i))])

        # Re-add the "New Entry" button
        self.add_new_entry_button()

    def add_new_entry_button(self):
        """
        Create the "New Entry" button at the bottom of the entry button list.
        """
        new_entry_button = MdbtButton("New Entry", self.entries_frame, command=lambda: self.set_fields_to_entry(
            self.config.num_entries()+1), ipadx=10, ipady=10)
        tt.Tooltip(new_entry_button, text="Use this button to add a new entry to your backup configuration. Pressing " +
                   "this button will display blank fields to the right, and once you specify which file/folder is " +
                   "being backed up, the entry will be created. The entry will not be solidified until you see a " +
                   "button on the left side of the window with the file/folder name of what you want to backup in it.")

    def highlight_entry_button(self, old_entry_number, new_entry_number):
        """
        Highlight a button in the entries scrollable frame. This takes an old and a new number, so the button
        corresponding to the old number will be made its normal color while the new number will be highlighted.
        :param old_entry_number: The index of the button to remove highlighting from, starting from 1.
        :param new_entry_number: The index of the button to highlight, starting from 1.
        """
        if 0 < old_entry_number <= self.config.num_entries()+1:
            self.entries_frame.widgets[old_entry_number-1].configure(bg="SystemButtonFace", fg="black")
        self.entries_frame.widgets[new_entry_number-1].configure(bg="blue", fg="white")

    def set_input(self):
        """
        Functionality for the "set highlighted path as input" button. This will take the focused path from the
        input Fileview and create a new configuration entry with it, or if an entry is already selected, this
        will update this entry's input to the new path.
        """
        focus_path = self.input_tree.get_focus_path()
        if focus_path == "":
            return
        # Create a new entry
        if self.current_entry_number > self.config.num_entries():
            try:
                configuration.append_input_to_config(self.config, focus_path)
                self.create_entry_button(self.current_entry_number)
                self.highlight_entry_button(self.current_entry_number, self.current_entry_number)
                MdbtMessage(self.config.get_entry(self.current_entry_number).input, self.input_frame)
                self.exclusion_button['state'] = tk.NORMAL
            except (InvalidPathException, CyclicEntryException) as e:
                messagebox.showerror("Error", str(e))
        # Edit an existing entry
        else:
            try:
                configuration.edit_input_in_config(self.config, self.current_entry_number, focus_path)
                path_split = os.path.split(self.config.get_entry(self.current_entry_number).input)
                button_text = path_split[0] if path_split[1] == "" else path_split[1]
                self.entries_frame.edit_text_on_widget(self.current_entry_number-1,
                                                       "Entry {}\n{}".format(self.current_entry_number, button_text))

                # Change the input path label
                MdbtMessage(self.config.get_entry(self.current_entry_number).input, self.input_frame)
                self.input_frame.remove_widget(0)
            except (InvalidPathException, SubPathException, CyclicEntryException) as e:
                messagebox.showerror("Error", str(e))
        self.update_config_name_label()

    def add_output(self):
        """
        Functionality for the "add highlighted path as output" button. This will add the path selected in the
        output Fileview as a new output path in the configuration's currently displayed entry.
        """
        focus_path = self.output_tree.get_focus_path()
        if focus_path == "":
            return
        # If we are on an existing entry, attempt to add a destination to it
        if 0 < self.current_entry_number <= self.config.num_entries():
            try:
                configuration.append_output_to_config(self.config, self.current_entry_number, focus_path)
                dest_number = self.config.get_entry(self.current_entry_number).num_destinations()
                MdbtMessage(self.config.get_entry(self.current_entry_number).get_destination(dest_number),
                            self.output_frame,
                            popup_members=[("Delete", lambda i=dest_number: self.delete_destination(i))])
                self.update_config_name_label()
                self.update_output_label()
            except (InvalidPathException, SubPathException, CyclicEntryException) as e:
                messagebox.showerror("Error", str(e))
        # Otherwise, say we can only add destinations if an input was set
        else:
            messagebox.showerror("Error", "You must set an input path before you can add destinations.")

    def edit_exclusion(self, excl_number):
        """
        Code run when the edit exclusion command is run. This will get the exclusion to be edited, its corresponding
        type, then launch the edit window.
        :param excl_number: The index of the exclusion to edit.
        """
        exclusion = self.config.get_entry(self.current_entry_number).get_exclusion(excl_number)
        exclusion_type = exclusions.get_exclusion_type(exclusion)
        self.excl_limit_window(True, exclusion_type, exclusion, excl_number)

    def edit_limitation(self, limit_number):
        """
        Code run when the edit limitation command is run. This will get the limitation to be edited, its corresponding
        type, then launch the edit window.
        :param limit_number: The index of the limitation to edit.
        """
        limitation = self.config.get_entry(self.current_entry_number).get_exclusion(
            self.current_exclusion_number).get_limitation(limit_number)
        limitation_type = limitations.get_limitation_type(limitation)
        self.excl_limit_window(False, limitation_type, limitation, limit_number)

    def backup(self):
        """
        Run when the backup button is pressed. This will do several checks to ensure the current configuration
        is valid and can be backed up. For a backup to be able to run, the current configuration must have at
        least one entry, all entries must have at least one output, and every path in every entry must be valid.
        """
        if self.config.num_entries() > 0:
            if self.config.all_entries_have_outputs():
                if self.config.all_paths_are_valid():
                    self.create_backup_window()
                else:
                    messagebox.showwarning("Cannot Run Backup", "At least one of the input or output paths in this " +
                                           "configuration is no longer valid. Please ensure all relevant drives are " +
                                           "plugged in, or edit any invalid paths.")
            else:
                messagebox.showwarning("Cannot Run Backup", "Not all inputs have a destination specified to back " +
                                       "them up to.")
        else:
            messagebox.showwarning("Cannot Run Backup", "There is nothing currently selected to backup.")

    def create_backup_window(self):
        """
        Creates and runs the backup sub-window for displaying information on the progress of the current backup.
        """
        # Initialize the backup window
        self.backup_window = tk.Toplevel(self.master)
        self.backup_window.wm_title("Run Backup")
        self.backup_window.geometry("500x210")

        # Create lists to hold all UI elements that require updating
        self.backup_status_labels = []
        self.backup_progress_bars = []
        self.backup_labels_modified = []
        self.backup_labels_new = []
        self.backup_labels_deleted = []
        self.backup_labels_error = []
        self.backup_labels_size = []

        # Create every item shown on the window
        self.backup_tabs = ttk.Notebook(self.backup_window)
        backup_number = 0
        tab_list = []
        for entry in self.config.entries:
            for output in entry.outputs:
                tab_list.append(ttk.Frame(self.backup_tabs))
                self.backup_tabs.add(tab_list[backup_number], text="Backup " + str(backup_number+1))
                tk.Message(tab_list[backup_number], text="Copying {} to {}".format(entry.input, output),
                           width=490).grid(row=0, column=0, columnspan=5, sticky=tk.NW)
                self.backup_status_labels.append(tk.Label(tab_list[backup_number], text="Inactive"))
                self.backup_status_labels[backup_number].grid(row=1, column=0, columnspan=5, padx=5, sticky=tk.NW)
                self.backup_progress_bars.append(ttk.Progressbar(tab_list[backup_number], orient=tk.HORIZONTAL,
                                                                 length=100, mode='determinate'))
                self.backup_progress_bars[backup_number].grid(row=2, column=0, columnspan=5, pady=10, sticky=tk.NSEW)
                self.backup_labels_modified.append(tk.Label(tab_list[backup_number], text="Modified: 0"))
                self.backup_labels_modified[backup_number].grid(row=3, column=0, padx=5, sticky=tk.NW)
                self.backup_labels_new.append(tk.Label(tab_list[backup_number], text="New: 0"))
                self.backup_labels_new[backup_number].grid(row=3, column=1, padx=5, sticky=tk.NW)
                self.backup_labels_deleted.append(tk.Label(tab_list[backup_number], text="Deleted: 0"))
                self.backup_labels_deleted[backup_number].grid(row=3, column=2, padx=5, sticky=tk.NW)
                self.backup_labels_error.append(tk.Label(tab_list[backup_number], text="Error: 0"))
                self.backup_labels_error[backup_number].grid(row=3, column=3, padx=5, sticky=tk.NW)
                self.backup_labels_size.append(tk.Label(tab_list[backup_number],
                                                        text="{}".format(util.bytes_to_string(0, 2))))
                self.backup_labels_size[backup_number].grid(row=3, column=4, padx=5, sticky=tk.NW)
                tab_list[backup_number].columnconfigure(0, weight=1)
                tab_list[backup_number].columnconfigure(1, weight=1)
                tab_list[backup_number].columnconfigure(2, weight=1)
                tab_list[backup_number].columnconfigure(3, weight=1)
                tab_list[backup_number].columnconfigure(4, weight=1)
                backup_number += 1
        self.num_backups = backup_number
        self.backup_tabs.pack(expand=True, fill=tk.BOTH)
        self.backup_start_button = tk.Button(self.backup_window, text="Start the backup", command=self.start_backup)
        self.backup_start_button.pack(pady=10)

        # Launch the window
        self.backup_window.current_backup = 0
        self.backup_window.grab_set()
        self.master.wait_window(self.backup_window)
        self.backup_window.grab_release()

    def start_backup(self):
        """
        Start the backup process. This will spawn a new thread that will run the backup function and call the
        UI on a set interval to update various labels and the progress bar.
        """
        self.backup_start_button['state'] = 'disabled'
        self.backup_refresh_time = 50
        self.backup_thread = backup_asyncio.BackupThread(self.config)
        self.backup_window.after(self.backup_refresh_time, self.refresh_backup_window)
        self.backup_thread.start()

    def refresh_backup_window(self):
        """
        Refresh the fields on the backup window. This takes data from the backup thread's queue and updates
        data on the UI in the order new data was received. This will be called on a set interval.
        """
        # Display a message and return if the thread is dead and the queue is empty
        if not self.backup_thread.is_alive() and self.backup_thread.progress_queue.empty():
            if not self.backup_thread.error_flag:
                messagebox.showinfo("Complete", "All backups are complete.")
            return

        # For every item in the queue, process it based on its key
        while not self.backup_thread.progress_queue.empty():
            key, data = self.backup_thread.progress_queue.get()
            if key == "backup_number":
                self.backup_window.current_backup = data
                if 0 <= self.backup_window.current_backup < self.num_backups:
                    self.backup_tabs.select(self.backup_window.current_backup)
            elif key == "processed":
                if data == 0:
                    label_text = "Inactive"
                else:
                    label_text = "{} files found".format(data)
                self.backup_status_labels[self.backup_window.current_backup].configure(text=label_text)
            elif key == "modified":
                self.backup_labels_modified[self.backup_window.current_backup].configure(
                    text="Modified: {}".format(data))
            elif key == "new":
                self.backup_labels_new[self.backup_window.current_backup].configure(text="New: {}".format(data))
            elif key == "deleted":
                self.backup_labels_deleted[self.backup_window.current_backup].configure(
                    text="Deleted: {}".format(data))
            elif key == "error":
                self.backup_labels_error[self.backup_window.current_backup].configure(
                    text="Error: {}".format(data))
            elif key == "size":
                self.backup_labels_size[self.backup_window.current_backup].configure(
                    text="{}".format(util.bytes_to_string(data, 2)))
            elif key == "progress":
                self.backup_progress_bars[self.backup_window.current_backup]['value'] = data
            elif key == "status":
                self.backup_status_labels[self.backup_window.current_backup].configure(text=data)
            elif key == "marked":
                if data == 0:
                    self.backup_progress_bars[self.backup_window.current_backup]['value'] = 100
            elif key == "display_error":
                if not data == "":
                    messagebox.showerror("Error", data)
            else:
                print("INVALID KEY")

        # Reset the timer so this method runs again after the set interval
        self.backup_window.after(self.backup_refresh_time, self.refresh_backup_window)

    def create_exclusion_menu(self):
        """
        Make a pop-up menu at the mouse's position that displays a list of exclusion types.
        """
        m = tk.Menu(self.master, tearoff=0)
        for exclusion_type in EXCLUSION_TYPES:
            m.add_command(label=exclusion_type.menu_text,
                          command=lambda e=exclusion_type: self.excl_limit_window(True, e))
        try:
            m.tk_popup(self.master.winfo_pointerx(), self.master.winfo_pointery())
        finally:
            m.grab_release()

    def create_limitation_menu(self):
        """
        Make a pop-up menu at the mouse's position that displays a list of limitation types.
        """
        m = tk.Menu(self.master, tearoff=0)
        for limitation_type in LIMITATION_TYPES:
            m.add_command(label=limitation_type.menu_text,
                          command=lambda l=limitation_type: self.excl_limit_window(False, l))
        try:
            m.tk_popup(self.master.winfo_pointerx(), self.master.winfo_pointery())
        finally:
            m.grab_release()

    def excl_limit_window(self, exclusion_mode, type_var, existing=None, old_index=0):
        """
        Launch the window for creating and editing exclusions/limitations and handle the results. Depending on the
        exclusion or limitation type passed in, the widget that accepts user input will be different.
        :param exclusion_mode: Whether this runs in exclusion mode or limitation mode. True signifies it'll run in
                               exclusion mode and false is for limitation mode.
        :param type_var: The exclusion/limitation type to create an exclusion of, or the exclusion/limitation type
                         corresponding to the exclusion/limitation being edited. This parameter is required.
        :param existing: If an exclusion/limitation is being edited, the object being edited. If this parameter
                         is given, the old_index parameter must also be given.
        :param old_index: If an exclusion/limitation is being edited, the index of that object, starting from 1.
                          If this parameter is given, the existing parameter must also be given.
        """
        def excl_limit_window_response(app):
            """
            Handle the response from the Create/Update button. This will set the excl_limit_code and excl_limit_data
            fields in the application if user data is given, then destroy the window.
            :param app: The current application.
            """
            new_data = type_var.ui_submit(app.excl_limit_element)
            if not new_data == "":
                app.excl_limit_code = type_var.code
                app.excl_limit_data = new_data
            app.exclusion_limitation_window.destroy()

        # Set initial data and data exclusive to whether an exclusion/limitation is being created or edited
        self.exclusion_limitation_window = tk.Toplevel(self.master)
        self.excl_limit_code = None
        self.excl_limit_data = None
        if existing is None:
            if exclusion_mode:
                self.exclusion_limitation_window.wm_title("Create Exclusion")
            else:
                self.exclusion_limitation_window.wm_title("Create Limitation")
            button_text = "Create"
            self.excl_limit_element = type_var.ui_input(self.exclusion_limitation_window)
        else:
            if exclusion_mode:
                self.exclusion_limitation_window.wm_title("Edit Exclusion")
            else:
                self.exclusion_limitation_window.wm_title("Edit Limitation")
            button_text = "Update"
            self.excl_limit_element = type_var.ui_edit(self.exclusion_limitation_window, existing)

        # Build the window and launch it
        tk.Label(self.exclusion_limitation_window, text=type_var.input_text).pack()
        self.excl_limit_element.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        tk.Button(self.exclusion_limitation_window, text=button_text,
                  command=lambda: excl_limit_window_response(self)).pack()
        self.exclusion_limitation_window.grab_set()
        self.master.wait_window(self.exclusion_limitation_window)
        self.exclusion_limitation_window.grab_release()

        # Handle the result
        if self.excl_limit_code is not None and self.excl_limit_data is not None:
            if existing is None:
                # Create a new exclusion
                if exclusion_mode:
                    new_index = self.config.get_entry(self.current_entry_number).new_exclusion(
                        self.excl_limit_code, self.excl_limit_data)
                    MdbtButton(self.config.get_entry(self.current_entry_number).get_exclusion(new_index).to_string(),
                               self.exclusion_frame, command=lambda i=new_index: self.set_exclusion_fields(i), ipadx=10,
                               ipady=10, popup_members=[("Edit", lambda i=new_index: self.edit_exclusion(i)),
                                                        ("Delete", lambda i=new_index: self.delete_exclusion(i))])
                # Create a new limitation
                else:
                    self.config.get_entry(self.current_entry_number).get_exclusion(
                        self.current_exclusion_number).add_limitation(self.excl_limit_code, self.excl_limit_data)
                    new_index = self.config.get_entry(self.current_entry_number).get_exclusion(
                        self.current_exclusion_number).num_limitations()
                    limitation = self.config.get_entry(self.current_entry_number).get_exclusion(
                        self.current_exclusion_number).get_limitation(new_index)
                    MdbtButton(limitation.to_string(), self.limitation_frame, ipadx=10, ipady=10,
                               popup_members=[("Edit", lambda i=new_index: self.edit_limitation(i)),
                                              ("Delete", lambda i=new_index: self.delete_limitation(i))])
            else:
                # Edit an existing exclusion
                if exclusion_mode:
                    self.config.get_entry(self.current_entry_number).get_exclusion(
                        old_index).data = self.excl_limit_data
                    self.exclusion_frame.edit_text_on_widget(old_index-1, self.config.get_entry(
                        self.current_entry_number).get_exclusion(old_index).to_string())
                # Edit an existing limitation
                else:
                    self.config.get_entry(self.current_entry_number).get_exclusion(
                        self.current_exclusion_number).get_limitation(old_index).data = self.excl_limit_data
                    self.limitation_frame.edit_text_on_widget(old_index-1, self.config.get_entry(
                        self.current_entry_number).get_exclusion(self.current_exclusion_number).get_limitation(
                        old_index).to_string())
            self.update_config_name_label()
            self.input_tree.reset()
            self.input_tree.travel_to_path(self.config.get_entry(self.current_entry_number).input)


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
