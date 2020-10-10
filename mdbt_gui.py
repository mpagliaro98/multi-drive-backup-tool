"""
mdbt.py
Author: Michael Pagliaro
The graphical user interface. This is one possible entry-point to the application which gives users a visual
interface for the program.
"""


import tkinter as tk
from tkinter import ttk
import fileview
import configuration


class ScrollableFrame(ttk.Frame):
    """
    Adapted from code by Jose Salvatierra (https://blog.tecladocode.com/tkinter-scrollable-frames/).
    Creates a frame that can scroll if the amount of objects grows greater than the window height.
    """

    def __init__(self, container, initial_width=0, initial_height=-1, dynamic_width=True, **kwargs):
        """
        Create the object as a subclass of Frame.
        :param container: The widget that houses this scrollable frame.
        :param initial_width: The width in pixels this frame will start as. If no value is provided, this will
                              wrap to what is specified when packed.
        :param initial_height: The height in pixels this frame will start as. If no value is provided, this will
                               wrap to what is specified when packed.
        :param dynamic_width: Indicates if this frame should change width based on its child widgets. If true,
                              when a new widget is added and its width is greater than the set width, the width
                              will grow. True by default.
        :param kwargs: Any other optional parameters to send to the super constructor.
        """
        super().__init__(container, **kwargs)
        self.widgets = []
        self.max_width = initial_width
        self.dynamic_width = dynamic_width

        # Create the overall canvas, the scrollbar, and the frame
        self.canvas = tk.Canvas(self)
        if self.max_width >= 0:
            self.canvas.configure(width=self.max_width)
        if initial_height >= 0:
            self.canvas.configure(height=initial_height)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Bind functions to the frame and canvas for resizing
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.on_resize)

        # Pack all widgets
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    @property
    def master_create(self):
        """
        A property to specify in child widgets created for this frame. This should be specified as the
        container argument for any new widget.
        :return: The frame that will hold all child widgets.
        """
        return self.scrollable_frame

    def update_width(self, new_width):
        """
        Update the width of the canvas to a new value if that new value is larger than the existing max width.
        This should only be called if dynamic_width is true.
        :param new_width: The new width to attempt to update to.
        """
        if new_width > self.max_width:
            self.max_width = new_width
            self.canvas.configure(width=self.max_width)

    def on_resize(self, event):
        """
        Function called when this frame is resized. This will update the width of all child widgets to
        fit the new size of the frame, except if they are Buttons.
        :param event: The resize event.
        """
        for widget in self.widgets:
            new_width = event.width-self.scrollbar.winfo_width()
            # Not a good solution, but button width is text-based while other widgets are pixel-based
            if not isinstance(widget, tk.Button):
                widget.configure(width=new_width)

    def register_widget(self, widget):
        """
        Register a new widget with this frame. This will allow it to be updated automatically on resize events.
        This should be called after a new widget is created in this frame.
        :param widget: The widget to be added.
        """
        self.widgets.append(widget)
        if self.dynamic_width:
            self.update_width(widget.winfo_width())


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
        self.menu_file.add_command(label="Load configuration")
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
        self.entries_frame = ScrollableFrame(self.base)
        button = tk.Button(self.entries_frame.master_create, text="New Entry")
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
        self.input_frame = ScrollableFrame(self.tab_inputs, initial_width=-1, initial_height=50, dynamic_width=False)
        self.input_frame.grid(column=0, row=1, sticky=tk.NSEW)
        self.output_frame = ScrollableFrame(self.tab_inputs, initial_width=-1, initial_height=50, dynamic_width=False)
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
