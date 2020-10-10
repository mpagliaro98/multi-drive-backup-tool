"""
scrollable_frame.py
Author: Michael Pagliaro
A UI element that creates a frame with a scrollbar. Adapted from code found online at
https://blog.tecladocode.com/tkinter-scrollable-frames/ by Jose Salvatierra.
"""


import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """
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
        self.initial_width = initial_width
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

    def clear_widgets(self):
        """
        Removes all widgets from this frame and resets its size to how it was when it was created.
        """
        for widget in self.widgets:
            widget.destroy()
        self.widgets = []
        self.canvas.configure(width=self.initial_width)
        self.max_width = self.initial_width