import glob
import os
import socket
import sublime
import sublime_plugin

def get_active_sessions():
    """
    Returns a list of active Pi session Unix socket paths (sorted by most recently active first)
    by scanning for sublime-session-*.sock files and verifying their connectivity.
    Stale socket files (from crashes or reboots) are automatically cleaned up.
    """
    home = os.path.expanduser("~")
    pi_dir = os.path.join(home, ".pi")
    pattern = os.path.join(pi_dir, "sublime-session-*.sock")
    socket_files = glob.glob(pattern)
    
    active_sessions_with_mtime = []
    
    for sock_path in socket_files:
        is_active = False
        
        # Verify the Unix socket is actually listening
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.1)  # Extremely fast connection check
        try:
            s.connect(sock_path)
            s.close()
            is_active = True
        except Exception:
            # Socket is dead or stale, clean it up
            try:
                os.remove(sock_path)
            except Exception:
                pass
                
        if is_active:
            try:
                mtime = os.path.getmtime(sock_path)
            except Exception:
                mtime = 0
            active_sessions_with_mtime.append((sock_path, mtime))
            
    # Sort by mtime descending (most recently active first)
    active_sessions_with_mtime.sort(key=lambda x: x[1], reverse=True)
    return [sock_path for sock_path, _ in active_sessions_with_mtime]


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

        # Check if active session exists to warn early
        active_sessions = get_active_sessions()
        if not active_sessions:
            sublime.status_message("Pi: Warning - No active Pi session detected. Run 'pi' in a terminal.")
        else:
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
    Sends the prompt to the active Pi session over a Unix Domain Socket.
    """
    def run(self, edit):
        active_sessions = get_active_sessions()
        if not active_sessions:
            sublime.error_message(
                "Pi: No active Pi session detected.\n\n"
                "Please run 'pi' in a terminal session first, then try submitting again. "
                "Your typed prompt has been kept in the panel so you do not lose it."
            )
            return

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
                f"Context: {reference}:",
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

        # Send to the most recently active session
        target_socket = active_sessions[0]
        success = False
        
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2.0)  # Safe timeout for delivering the prompt
            s.connect(target_socket)
            s.sendall(result.encode("utf-8"))
            s.shutdown(socket.SHUT_WR)  # Signal EOF to Node.js
            
            # Read acknowledgment handshake
            response = s.recv(1024).decode("utf-8")
            s.close()
            if response == "OK":
                success = True
        except Exception:
            pass

        if success:
            sublime.status_message("Pi: Sent prompt to active session.")
            window = self.view.window()
            if window:
                window.run_command("hide_panel", {"panel": "output.pi_ask_panel"})
        else:
            sublime.error_message(
                "Pi: Failed to send prompt.\n\n"
                "The active session may have closed or timed out. Please check your terminal and try again."
            )


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
