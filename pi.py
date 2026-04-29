import sublime
import sublime_plugin

class PiAskCommand(sublime_plugin.TextCommand):
    """
    Copies the current file path and line number to the clipboard
    so it can be easily pasted into the Pi REPL.
    """
    def run(self, edit):
        file_name = self.view.file_name()
        
        if not file_name:
            sublime.status_message("Pi: Unsaved file, no path available.")
            return

        selections = self.view.sel()
        if not selections:
            return

        # Take the first cursor/selection
        region = selections[0]
        start_row, _ = self.view.rowcol(region.begin())
        end_row, _ = self.view.rowcol(region.end())
        
        start_line = start_row + 1
        end_line = end_row + 1

        if start_line == end_line:
            reference = f"{file_name}:{start_line}"
        else:
            reference = f"{file_name}:{start_line}-{end_line}"

        # Copy to clipboard
        sublime.set_clipboard(reference)
        sublime.status_message(f"Pi: Copied '{reference}'")

    def is_visible(self):
        # Only show in the context menu if there is a real file behind the view
        return self.view.file_name() is not None
