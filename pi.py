import sublime
import sublime_plugin

class PiCommand(sublime_plugin.TextCommand):
    """
    A simple example command that inserts text at the beginning of the file.
    To use this, open the Command Palette and select 'Pi: Hello World'.
    """

    def run(self, edit):
        self.view.insert(edit, 0, "Hello, Pi!\n")
        sublime.status_message("Pi executed successfully!")

    def is_enabled(self):
        return True
