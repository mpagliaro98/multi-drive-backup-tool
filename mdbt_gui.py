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
import configuration
from configuration import InvalidPathException, SubPathException, CyclicEntryException


def create_label_scrollable_frame(text, frame, delete_enable=False, delete_function=lambda: None):
    """
    Create a label that will be put in a scrollable frame, using this program's settings for how labels
    should look.
    :param text: The text to display.
    :param frame: The scrollable frame to put this text in.
    :param delete_enable: True if this label should be allowed to be right-clicked, displaying a menu with a
                          delete option. False by default.
    :param delete_function: The function that will run when the right-click delete command is executed. This
                            will have no effect if delete_enable is False. This function does nothing by default.
    """
    def highlight(event):
        """
        When called by an event, this will highlight the widget called. If it's already highlighted, this
        will remove the highlight.
        :param event: The event that was triggered.
        """
        event.widget.configure(bg='SystemButtonFace' if event.widget['bg'] == 'blue' else 'blue')

    def delete_popup(event):
        """
        When called by an event, this will display a menu by the mouse cursor with a delete option.
        :param event: The event that was triggered.
        """
        event.widget.configure(bg='blue')
        m = tk.Menu(frame.master, tearoff=0)
        m.add_command(label="Delete", command=delete_function)
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()
        event.widget.configure(bg='SystemButtonFace')

    input_label = tk.Message(frame.master_create, text=text, anchor=tk.W)
    if delete_enable:
        input_label.bind("<Button-1>", highlight)
        input_label.bind("<Button-3>", delete_popup)
    input_label.pack(fill=tk.BOTH)
    frame.master.update()
    frame.register_widget(input_label)


def create_button_scrollable_frame(text, frame, command=lambda: None, ipadx=0, ipady=0):
    """
    Create a button that will be put in a scrollable frame, using this program's settings for how buttons
    should look.
    :param text: The text that goes in the button.
    :param frame: The scrollable frame to add this button to.
    :param command: Optional parameter, a function run when this button is pressed. Does nothing if not specified.
    :param ipadx: Optional parameter, horizontal padding between the text and the button sides. Defaults to 0.
    :param ipady: Optional parameter, vertical padding between the text and the button edges. Defaults to 0.
    """
    button = tk.Button(frame.master_create, text=text, command=command)
    button.pack(ipadx=ipadx, ipady=ipady)
    frame.master.update()
    frame.register_widget(button)


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
        self.menu_file.add_command(label="Clear configuration", command=self.clear_configuration)
        self.menu_file.add_command(label="Exit", command=self.master.quit)
        self.menu.add_cascade(label="File", menu=self.menu_file)
        self.menu_edit = tk.Menu(self.menu, tearoff=0)
        self.menu_edit.add_command(label="Delete highlighted outputs", command=self.delete_highlighted_destinations)
        self.menu.add_cascade(label="Edit", menu=self.menu_edit)
        self.menu_help = tk.Menu(self.menu, tearoff=0)
        self.menu_help.add_command(label="About")
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
        self.backup_button = tk.Button(self.base, text="BACKUP")
        self.backup_button.grid(row=2, column=1, pady=10, ipadx=60, ipady=10)

        # Create the buttons below the Fileviews
        self.input_button = tk.Button(self.tab_inputs, text="Set highlighted path to input", command=self.set_input)
        self.input_button.grid(column=0, row=3)
        self.output_button = tk.Button(self.tab_inputs, text="Add highlighted path as output", command=self.add_output)
        self.output_button.grid(column=1, row=3)

    def init_labels(self):
        """
        Create various labels on the window, including the configuration name label and ones for inputs
        and outputs.
        """
        self.config_name_label = ttk.Label(self.base, text="The current configuration has not been saved yet.")
        self.config_name_label.grid(row=0, columnspan=2, sticky=tk.NW)

        # Add labels above the input and output frames
        ttk.Label(self.tab_inputs, text="BACKUP", font="Helvetica 12 bold").grid(
            column=0, row=0, padx=10, pady=10, sticky=tk.NW)
        ttk.Label(self.tab_inputs, text="COPY TO", font="Helvetica 12 bold").grid(
            column=1, row=0, padx=10, pady=10, sticky=tk.NW)
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
        pass

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

        # Create the load window
        self.config_name = None
        self.load_window = tk.Toplevel(self.master)
        self.load_window.wm_title("Load Configuration")
        self.load_window.geometry("300x300")
        self.config_name_list = configuration.saved_config_display_string().strip().split("\n")
        config_load_frame = sf.ScrollableFrame(self.load_window, dynamic_width=False)

        # Create a button for every saved configuration
        for name_idx in range(len(self.config_name_list)):
            create_button_scrollable_frame(self.config_name_list[name_idx], config_load_frame,
                                           command=lambda i=name_idx: load_window_response(self, i), ipadx=5, ipady=5)
        config_load_frame.pack(fill=tk.BOTH, expand=True)
        self.master.wait_window(self.load_window)

        # If an option was chosen, load it in
        if self.config_name is not None:
            self.config = configuration.load_config(self.config_name)
            self.update_config_name_label()
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

        # Only display entry info if it's a valid entry number. Otherwise just clear the fields
        if 0 < entry_number <= self.config.num_entries():
            # Add the input path to the input scrollable frame
            create_label_scrollable_frame(self.config.get_entry(entry_number).input, self.input_frame)

            # Set the input tree to display the input
            self.input_tree.travel_to_path(self.config.get_entry(entry_number).input)

            # Add every output path to the output scrollable frame
            for output_idx in range(1, len(self.config.get_entry(entry_number).outputs)+1):
                create_label_scrollable_frame(self.config.get_entry(entry_number).get_destination(output_idx),
                                              self.output_frame, delete_enable=True,
                                              delete_function=lambda i=output_idx: self.delete_destination(i))

    def delete_destination(self, dest_number):
        """
        Delete a destination from an entry in the configuration. This should be called from the right-click
        delete menu on destination labels. This will first delete the destination, then remake all the labels
        in the output frame in order to update their delete functions.
        :param dest_number: The index of the destination in that entry, starting from 1.
        """
        self.config.get_entry(self.current_entry_number).delete_destination(dest_number)
        self.output_frame.clear_widgets()
        for output_idx in range(1, len(self.config.get_entry(self.current_entry_number).outputs) + 1):
            create_label_scrollable_frame(self.config.get_entry(self.current_entry_number).get_destination(output_idx),
                                          self.output_frame, delete_enable=True,
                                          delete_function=lambda i=output_idx: self.delete_destination(i))
        self.update_config_name_label()

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
            create_label_scrollable_frame(self.config.get_entry(self.current_entry_number).get_destination(output_idx),
                                          self.output_frame, delete_enable=True,
                                          delete_function=lambda i=output_idx: self.delete_destination(i))
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
        create_button_scrollable_frame("Entry {}\n{}".format(entry_number, button_text), self.entries_frame,
                                       command=lambda: self.set_fields_to_entry(entry_number), ipadx=10, ipady=10)

        # Re-add the "New Entry" button
        self.add_new_entry_button()

    def add_new_entry_button(self):
        """
        Create the "New Entry" button at the bottom of the entry button list.
        """
        create_button_scrollable_frame("New Entry", self.entries_frame, command=lambda: self.set_fields_to_entry(
            self.config.num_entries()+1), ipadx=10, ipady=10)

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
                create_label_scrollable_frame(self.config.get_entry(self.current_entry_number).input, self.input_frame)
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
                create_label_scrollable_frame(self.config.get_entry(self.current_entry_number).input, self.input_frame)
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
                create_label_scrollable_frame(self.config.get_entry(self.current_entry_number).get_destination(
                    dest_number), self.output_frame, delete_enable=True,
                    delete_function=lambda i=dest_number: self.delete_destination(i))
                self.update_config_name_label()
            except (InvalidPathException, SubPathException, CyclicEntryException) as e:
                messagebox.showerror("Error", str(e))
        # Otherwise, say we can only add destinations if an input was set
        else:
            messagebox.showerror("Error", "You must set an input path before you can add destinations.")


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
