"""
fileview.py
Author: Michael Pagliaro
A UI element that displays a treeview of the system's directory structure. Adapted from code found online
at https://svn.python.org/projects/python/trunk/Demo/tkinter/ttk/dirbrowser.py (author unknown).
"""


import os
import tkinter as tk
from tkinter import ttk
import util


class Fileview(tk.Frame):
    """
    A Fileview is a specialized Treeview, but extends a Frame so we can add scroll bars to it. This shows the
    current system's directory structure as a tree and allows navigation through it.
    """

    def __init__(self, default_focus=None, entry=None, **kw):
        """
        Create the Fileview as a child object of tkinter's Frame. This will create a Treeview with
        scroll bars, and the Treeview will be initialized to start with a list of all available drives.
        :param default_focus: If specified, the Fileview will open the direct path to this file/folder on creation.
        :param entry: A configuration entry. Exclusions on this entry will be used to grey out items that fall
                      under the entry's exclusions and limitations.
        :param kw: Any labeled arguments to initialize the underlying Frame with.
        """
        super().__init__(**kw, width=3)
        self.config(width=5)

        # Initialize the tree and the scroll bars
        self._tree = ttk.Treeview(self, columns=("fullpath", "type", "size"), displaycolumns="size")
        self._vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=self._vsb.set, xscrollcommand=self._hsb.set)
        self._entry = entry

        # Styling, must use workaround due to tkinter bug
        self.style = ttk.Style()
        self.style.map("Treeview", foreground=self.fixed_map("foreground"), background=self.fixed_map("background"))
        self._tree.tag_configure("excluded", foreground='grey')

        # Initialize each column that will be displayed
        self._tree.heading("#0", text="Directory Structure", anchor='w')
        self._tree.heading("size", text="File Size", anchor='w')
        self._tree.column("size", stretch=False, width=100)

        # Populate the tree and set its functionality
        self.populate_roots()
        self._tree.bind('<<TreeviewOpen>>', self.update_tree)

        # Arrange the tree and scroll bars within the frame
        self._tree.grid(row=0, column=0, stick=tk.NSEW, in_=self)
        self._vsb.grid(row=0, column=1, sticky=tk.NS+tk.E, in_=self)
        self._hsb.grid(row=1, column=0, sticky=tk.EW+tk.S, in_=self)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # If a default focus is given, start by showing that path
        if default_focus is not None and os.path.exists(os.path.realpath(default_focus)):
            self.travel_to_path(os.path.realpath(default_focus))

    def populate_tree(self, node):
        """
        Populate the tree with a node (representing a valid file path) and all of that path's children
        if it is a directory.
        :param node: An existing node in the tree.
        """
        if self._tree.set(node, "type") != 'directory':
            return

        # Get the current path to expand upon
        path = self._tree.set(node, "fullpath")
        self._tree.delete(*self._tree.get_children(node))

        # Loop through every child path of the selected path
        for subpath in os.listdir(path):
            # Determine if this child is a file or folder
            path_type = None
            subpath = os.path.join(path, subpath)
            if os.path.isdir(subpath):
                path_type = "directory"
            elif os.path.isfile(subpath):
                path_type = "file"

            # Get the filename and insert a new node into the tree, grey it out if it should be excluded
            filename = os.path.split(subpath)[1]
            if self._entry is not None and (self._tree.tag_has("excluded", node) or self.parent_is_excluded(node)):
                node_id = self._tree.insert(node, "end", text=filename, values=[subpath, path_type], tags=('excluded',))
            else:
                if self._entry is not None and self._entry.should_exclude(subpath):
                    node_id = self._tree.insert(node, "end", text=filename, values=[subpath, path_type],
                                                tags=('excluded',))
                else:
                    node_id = self._tree.insert(node, "end", text=filename, values=[subpath, path_type])

            # Insert additional information depending on what type the path is
            if path_type == 'directory':
                self._tree.insert(node_id, 0, text="dummy")
                self._tree.item(node_id, text=filename)
            elif path_type == 'file':
                size = os.stat(subpath).st_size
                self._tree.set(node_id, "size", util.bytes_to_string(size, precision=2))

    def populate_roots(self):
        """
        Populate the tree with nodes for each of the available drives on the system.
        """
        for drive_letter in util.get_drive_list():
            dir_path = os.path.realpath(drive_letter + '\\')
            if self._entry is not None and self._entry.should_exclude(dir_path):
                node = self._tree.insert('', 'end', text=dir_path, values=[dir_path, "directory"], tags=('excluded',))
            else:
                node = self._tree.insert('', 'end', text=dir_path, values=[dir_path, "directory"])
            self.populate_tree(node)

    def update_tree(self, event):
        """
        Update the data displayed by the tree when an event occurs, such as expanding a directory.
        :param event: The event that occurred.
        """
        tree = event.widget
        self.populate_tree(tree.focus())

    def get_focus_path(self):
        """
        Get the file path currently focused on by the tree.
        :return: The full path to the file or directory currently highlighted in the tree.
        """
        return self._tree.set(self._tree.focus(), "fullpath")

    def reset(self):
        """
        Reset this Fileview to the state it was after initialization. This will first empty all nodes from the
        Fileview, then repopulate the roots.
        """
        self._tree.delete(*self._tree.get_children())
        self.populate_roots()

    def set_entry(self, new_entry):
        """
        Set the entry field for this Fileview.
        :param new_entry: A configuration entry.
        """
        self._entry = new_entry

    def travel_to_path(self, destination, previous="", current_node=None):
        """
        Navigate through the Fileview to a given valid file path. Directories on the tree will be opened and the
        final location will become the highlighted focus of the tree.
        :param destination: A valid file path to set the tree to.
        :param previous: The previous path the tree has traveled to and opened during recursion. This should not
                         be specified by the user. Defaults to the empty string.
        :param current_node: The current node being focused on by the tree during recursion. This should not be
                             specified by the user. Defaults to None.
        """
        # If destination is empty, we've found the desired node
        if destination == "":
            return

        # Split the destination path into its individual segments
        if current_node is not None:
            self._tree.item(current_node, open=True)
        path_segments = []
        path_split = ("dummy", "dummy")
        while path_split[1] != "":
            path_split = os.path.split(destination)
            # End of path when there isn't a drive letter out front
            if path_split[0] == "":
                path_segments.append(path_split[1])
                break
            # End of path when there is a drive letter out front
            elif path_split[1] == "":
                path_segments.append(path_split[0])
                break
            else:
                path_segments.append(path_split[1])
                destination = path_split[0]

        # Update previous to the next path in the sequence
        previous = os.path.join(previous, path_segments[-1])
        del path_segments[-1]

        # Loop through all children of the current node, find the one for the path currently in previous
        for node in self._tree.get_children(item=current_node):
            if self._tree.set(node, "fullpath") == previous:
                # Node was found, so set it as the focus and create its children
                current_node = node
                self._tree.selection_set(node)
                self._tree.focus(node)
                self.populate_tree(self._tree.focus())

                # Update remaining path to be everything after previous
                remaining_path = ""
                for segment in reversed(path_segments):
                    remaining_path = os.path.join(remaining_path, segment)
                return self.travel_to_path(remaining_path, previous, current_node)

    def fixed_map(self, option):
        """
        Returns the style map for 'option' with any styles starting with ("!disabled", "!selected", ...) filtered
        out. This is a workaround to a bug in tkinter that causes style tags to not work on modern versions.
        Workaround described here: https://core.tcl-lang.org/tk/tktview?name=509cafafae
        :param option: A style option to fix.
        :return: Fixed style map.
        """
        return [elm for elm in self.style.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]

    def parent_is_excluded(self, node):
        """
        Checks if a parent of the given node in the tree has the "excluded" tag.
        :param node: A node from the tree.
        :return: True if one of its parents has the "excluded" tag, false otherwise.
        """
        parent = self._tree.parent(node)
        if parent != '':
            if self._tree.tag_has("excluded", parent):
                return True
            else:
                self.parent_is_excluded(parent)
        else:
            return False
