"""
backup_asyncio.py
Author: Michael Pagliaro
The graphical user interface. This is one possible entry-point to the application which gives users a visual
interface for the program.
"""


import threading
import asyncio
import queue
import backup
from observer import observer


class BackupThread(threading.Thread):
    """
    A special-purpose asyncio thread for running the backup process concurrently with something else. While the
    thread is running, a queue is kept and constantly updated with information from the backup process about
    number of files processed, the current status, etc. Processes using this thread can check the queue at set
    intervals to keep things like a UI updated alongside the backup.
    """

    def __init__(self, config):
        """
        Create the thread before running it. This accepts specific arguments needed while it runs.
        :param config: A configuration of files and folders to backup.
        """
        self.loop = asyncio.get_event_loop()
        self.progress_queue = queue.Queue()
        self.config = config
        threading.Thread.__init__(self)

    def run(self):
        """
        Launch the thread by starting the backup process. Various observer functions are also kept here to
        update the queue.
        """
        @observer(backup.increment_backup_number, self)
        def update_backup_number(backup_thread):
            backup_thread.progress_queue.put(("backup_number", backup.BACKUP_NUMBER))

        @observer(backup.increment_processed, self)
        @observer(backup.reset_globals, self)
        def update_processed(backup_thread):
            backup_thread.progress_queue.put(("processed", backup.NUM_FILES_PROCESSED))

        @observer(backup.increment_modified, self)
        @observer(backup.reset_globals, self)
        def update_modified(backup_thread):
            backup_thread.progress_queue.put(("modified", backup.NUM_FILES_MODIFIED))

        @observer(backup.increment_new, self)
        @observer(backup.reset_globals, self)
        def update_new(backup_thread):
            backup_thread.progress_queue.put(("new", backup.NUM_FILES_NEW))

        @observer(backup.increment_deleted, self)
        @observer(backup.reset_globals, self)
        def update_deleted(backup_thread):
            backup_thread.progress_queue.put(("deleted", backup.NUM_FILES_DELETED))

        @observer(backup.increment_error, self)
        @observer(backup.reset_globals, self)
        def update_error(backup_thread):
            backup_thread.progress_queue.put(("error", backup.NUM_FILES_ERROR))

        @observer(backup.increment_size, self)
        @observer(backup.reset_globals, self)
        def update_size(backup_thread):
            backup_thread.progress_queue.put(("size", backup.TOTAL_SIZE_PROCESSED))

        @observer(backup.increment_backup_progress, self)
        @observer(backup.reset_globals, self)
        def update_progress(backup_thread):
            backup_thread.progress_queue.put(
                ("progress",
                 0 if backup.NUM_FILES_MARKED == 0 else backup.BACKUP_PROGRESS / backup.NUM_FILES_MARKED * 100))

        @observer(backup.set_status, self)
        def update_status(backup_thread):
            backup_thread.progress_queue.put(("status", backup.CURRENT_STATUS))

        self.loop.run_until_complete(self.run_backup())

    async def run_backup(self):
        """
        Start the run_backup() asyncio task.
        """
        await asyncio.wait([backup.run_backup(self.config)])
