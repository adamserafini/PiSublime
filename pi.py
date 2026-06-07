import os
import sublime
import sublime_plugin

class PiAskCommand(sublime_plugin.TextCommand):
    """
    Opens a multi-line input panel at the bottom of the screen to submit a prompt to Pi.
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
        selected_text = self.view.substr(region)

        start_row, _ = self.view.rowcol(region.begin())
        end_row, _ = self.view.rowcol(region.end())
        
        start_line = start_row + 1
        end_line = end_row + 1

        if start_line == end_line:
            reference = f"{file_name}:{start_line}"
        else:
            reference = f"{file_name}:{start_line}-{end_line}"

        window = self.view.window()
        if not window:
            sublime.status_message("Pi: No active window available.")
            return

        # Create or retrieve the multi-line output panel
        panel = window.create_output_panel('pi_ask_panel')
        
        # Configure panel settings
        panel.set_scratch(True)
        panel.set_read_only(False)
        
        settings = panel.settings()
        settings.set("word_wrap", True)
        settings.set("line_numbers", False)
        settings.set("gutter", False)
        settings.set("draw_centered", False)
        settings.set("auto_indent", True)
        settings.set("pi_ask_panel", True)
        settings.set("pi_ask_reference", reference)
        settings.set("pi_ask_selected_text", selected_text)
        settings.set("pi_ask_file_name", file_name)

        # Clear existing content and set selection to start
        panel.run_command("pi_clear_and_focus")

        # Show the panel
        window.run_command("show_panel", {"panel": "output.pi_ask_panel"})
        window.focus_view(panel)
        sublime.status_message("Pi: Type your prompt. Press Enter to submit, Shift+Enter for new line, Esc to cancel.")

    def is_visible(self):
        # Only show in the context menu if there is a real file behind the view
        return self.view.file_name() is not None


class PiClearAndFocusCommand(sublime_plugin.TextCommand):
    """
    Clears the contents of the view and resets the selection to the beginning.
    """
    def run(self, edit):
        self.view.replace(edit, sublime.Region(0, self.view.size()), "")
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(0, 0))


class PiSubmitAskCommand(sublime_plugin.TextCommand):
    """
    Command bound to Enter / Ctrl+Enter in the Pi Ask panel.
    Prepend the reference, writes to the trigger file, and hides the panel.
    """
    def run(self, edit):
        question = self.view.substr(sublime.Region(0, self.view.size())).strip()
        reference = self.view.settings().get("pi_ask_reference", "")
        selected_text = self.view.settings().get("pi_ask_selected_text", "")
        file_name = self.view.settings().get("pi_ask_file_name", "")

        # Format the final prompt
        if selected_text and selected_text.strip():
            # Get file extension for markdown syntax highlighting
            _, ext = os.path.splitext(file_name)
            syntax = ext.lstrip('.').lower() if ext else ""
            
            # Format with embedded code block
            parts = [
                f"Regarding {reference}:",
                f"```{syntax}",
                selected_text,
                "```"
            ]
            if question:
                parts.append("")
                parts.append(question)
                
            result = "\n".join(parts)
        else:
            # Fallback to pure reference format
            if question:
                result = f"{reference} {question}"
            else:
                result = reference

        # Write to Pi Sublime integration trigger file
        try:
            home = os.path.expanduser("~")
            pi_dir = os.path.join(home, ".pi")
            os.makedirs(pi_dir, exist_ok=True)
            trigger_file = os.path.join(pi_dir, "sublime-ask.txt")
            with open(trigger_file, "w", encoding="utf-8") as f:
                f.write(result)
            sublime.status_message("Pi: Sent prompt to running session.")
        except Exception as e:
            sublime.status_message("Pi: Error sending prompt to session.")

        window = self.view.window()
        if window:
            window.run_command("hide_panel", {"panel": "output.pi_ask_panel"})


class PiCancelAskCommand(sublime_plugin.TextCommand):
    """
    Command bound to Escape in the Pi Ask panel.
    Hides the panel.
    """
    def run(self, edit):
        sublime.status_message("Pi: Cancelled.")

        window = self.view.window()
        if window:
            window.run_command("hide_panel", {"panel": "output.pi_ask_panel"})
