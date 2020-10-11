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
        self._widgets = []
        self.initial_width = initial_width
        self.dynamic_width = dynamic_width

        # Create the overall canvas, the scrollbar, and the frame
        self.canvas = tk.Canvas(self)
        if self.initial_width >= 0:
            self.canvas.configure(width=self.initial_width)
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

    @property
    def widgets(self):
        """
        The list of widgets held by this frame.
        :return: A list of widgets.
        """
        return self._widgets

    def update_width(self):
        """
        Update the width of the canvas to be as wide as its largest widget. If there are no widgets, set it
        to its initial width. This should only be called if dynamic_width is true.
        """
        canvas_width = 0
        if len(self._widgets) == 0:
            canvas_width = self.initial_width
        else:
            for widget in self._widgets:
                if widget.winfo_reqwidth() + self.scrollbar.winfo_reqwidth() + 3 > canvas_width:
                    canvas_width = widget.winfo_reqwidth() + self.scrollbar.winfo_reqwidth() + 3
        self.canvas.configure(width=canvas_width)

    def on_resize(self, event):
        """
        Function called when this frame is resized. This will update the width of all child widgets to
        fit the new size of the frame, except if they are Buttons.
        :param event: The resize event.
        """
        for widget in self._widgets:
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
        self._widgets.append(widget)
        # If we aren't adding a button, increase its width to match the frame
        if not isinstance(widget, tk.Button):
            new_width = self.canvas.winfo_width() - self.scrollbar.winfo_width()
            widget.configure(width=new_width)
        # Update the frame width if dynamic width is on
        if self.dynamic_width:
            self.update_width()

    def clear_widgets(self):
        """
        Removes all widgets from this frame and resets its size to how it was when it was created.
        """
        for widget in self._widgets:
            widget.destroy()
        self._widgets = []
        self.canvas.configure(width=self.initial_width)

    def remove_widget(self, widget_idx):
        """
        Remove a widget at a given index in the widgets list.
        :param widget_idx: The index of the widget to delete.
        """
        self._widgets[widget_idx].destroy()
        del self._widgets[widget_idx]

    def edit_text_on_widget(self, widget_idx, new_text):
        """
        Change the text on a given widget. If dynamic width is on, this will also update the frame's width.
        :param widget_idx: The index of the widget to modify, starting from 0.
        :param new_text: The new text to put on the widget.
        """
        self._widgets[widget_idx].configure(text=new_text)
        if self.dynamic_width:
            self.update_width()
