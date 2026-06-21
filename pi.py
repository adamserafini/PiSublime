import glob
import json
import os
import socket
import sublime
import sublime_plugin
import subprocess
import plistlib


def is_ancestor_or_same(ancestor, path):
    """
    Returns True if ancestor is the same directory as path, or is a parent/ancestor of path.
    """
    if not ancestor or not path:
        return False
        
    ancestor = os.path.abspath(ancestor)
    path = os.path.abspath(path)
    
    # On case-insensitive systems (like macOS/Windows), compare case-insensitively
    ancestor_lower = ancestor.lower()
    path_lower = path.lower()
    
    if ancestor_lower == path_lower:
        return True
        
    # Add trailing path separator to prevent matching /usr/local-foo with /usr/local
    prefix = ancestor_lower if ancestor_lower.endswith(os.sep) else ancestor_lower + os.sep
    return path_lower.startswith(prefix)


def get_active_sessions():
    """
    Returns a list of active Pi session info dicts:
    {"uuid", "pid", "cwd", "socket_path", "last_activity"}
    by scanning for sublime-session-*.json files and verifying socket connectivity.
    Stale session and socket files are automatically cleaned up.
    """
    home = os.path.expanduser("~")
    pi_dir = os.path.join(home, ".pi")
    pattern = os.path.join(pi_dir, "sublime-session-*.json")
    session_files = glob.glob(pattern)
    
    active_sessions = []
    
    for f_path in session_files:
        filename = os.path.basename(f_path)
        try:
            uuid = filename.replace("sublime-session-", "").replace(".json", "")
            if not uuid:
                continue
        except Exception:
            continue
            
        # Try loading the session JSON
        try:
            with open(f_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cwd = data.get("cwd")
            last_activity = data.get("lastActivity", 0)
            socket_path = f_path.replace(".json", ".sock")
        except Exception:
            # Corrupted JSON, clean it up
            try:
                os.remove(f_path)
            except Exception:
                pass
            continue
            
        # Verify socket connectivity
        is_active = False
        if socket_path and os.path.exists(socket_path):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(0.1)  # Extremely fast connection check
            try:
                s.connect(socket_path)
                s.close()
                is_active = True
            except Exception:
                pass
                
        if is_active:
            active_sessions.append({
                "uuid": uuid,
                "cwd": cwd,
                "socket_path": socket_path,
                "last_activity": last_activity
            })
        else:
            # Socket is dead or stale, clean up both the json and socket files
            try:
                os.remove(f_path)
            except Exception:
                pass
            if socket_path and os.path.exists(socket_path):
                try:
                    os.remove(socket_path)
                except Exception:
                    pass
                    
    return active_sessions


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


class PiSidebarAskCommand(sublime_plugin.WindowCommand):
    """
    Opens the Pi Ask panel with the right-clicked file/directory from the sidebar as context.
    """
    def run(self, paths=None, files=None):
        if not paths and files:
            paths = files
        if not paths:
            sublime.status_message("Pi: No file or directory selected in the sidebar.")
            return

        # Take the first selected path
        target_path = paths[0]
        
        # Configure the panel context
        selected_text = ""
        reference = target_path

        window = self.window
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
        settings.set("pi_ask_file_name", target_path)

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

    def is_visible(self, paths=None, files=None):
        if not paths and files:
            paths = files
        return bool(paths)


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
    Sends the prompt to the matched Pi session over a Unix Domain Socket.
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

        # Match the target session based on directory and recency
        if file_name and os.path.isdir(file_name):
            file_dir = file_name
        else:
            file_dir = os.path.dirname(file_name) if file_name else ""

        target_session = None
        
        # Rule 1: Global Fallback - If exactly one session exists, use it
        if len(active_sessions) == 1:
            target_session = active_sessions[0]
        else:
            # Find sessions where cwd is same as or ancestor of file_dir
            matching_sessions = []
            if file_dir:
                for s in active_sessions:
                    cwd = s.get("cwd")
                    if cwd and is_ancestor_or_same(cwd, file_dir):
                        matching_sessions.append(s)
            
            # Rule 2: Directory Match - If exactly one matches, use it
            if len(matching_sessions) == 1:
                target_session = matching_sessions[0]
            # Rule 3: Recency Tie-Breaker
            elif len(matching_sessions) > 1:
                # Multiple matches: pick most recently active match
                matching_sessions.sort(key=lambda x: x.get("last_activity", 0), reverse=True)
                target_session = matching_sessions[0]
            else:
                # No matches: pick most recently active globally
                active_sessions.sort(key=lambda x: x.get("last_activity", 0), reverse=True)
                target_session = active_sessions[0]

        success = False
        target_socket = target_session.get("socket_path") if target_session else None
        
        if target_socket:
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
                "The target session may have closed or timed out. Please check your terminal and try again."
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


def plugin_loaded():
    # Only run on macOS
    if os.name != "posix" or subprocess.check_output(["uname"]).decode("utf-8").strip() != "Darwin":
        return

    package_dir = os.path.dirname(__file__)
    app_path = os.path.join(package_dir, "SublHandler.app")
    applescript_path = os.path.join(package_dir, "SublHandler.applescript")

    if not os.path.exists(applescript_path):
        print("PiSublime: SublHandler.applescript missing.")
        return

    if os.path.exists(app_path):
        # Only skip if the compiled app is newer than or equal to the source AppleScript
        if os.path.getmtime(applescript_path) <= os.path.getmtime(app_path):
            return

    try:
        # Compile using osacompile directly from our file
        subprocess.run(["osacompile", "-o", app_path, applescript_path], check=True)

        # Inject CFBundleURLTypes into Info.plist
        plist_path = os.path.join(app_path, "Contents/Info.plist")
        if os.path.exists(plist_path):
            with open(plist_path, "rb") as fp:
                pl = plistlib.load(fp)

            pl["CFBundleURLTypes"] = [
                {
                    "CFBundleURLName": "Sublime Text URL Handler",
                    "CFBundleURLSchemes": ["subl"],
                }
            ]

            with open(plist_path, "wb") as fp:
                plistlib.dump(pl, fp)

        # Register with Launch Services
        subprocess.run([
            "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister",
            "-f", app_path
        ], check=True)


    except Exception as e:
        print("PiSublime: Failed to bootstrap SublHandler.app:", e)


