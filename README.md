# PiSublime

A Sublime Text 4 plugin to send code selections and prompts directly to your active `Pi` terminal session.

## Installation

Clone this repository onto your computer. This plugin is currently tested only on **macOS** and only **manually**. It might work on Linux or Windows if the installation paths below were adjusted.

### Step 1: Install the Sublime Text 4 Plugin

```bash
ln -s "$(pwd)" ~/Library/Application\ Support/Sublime\ Text/Packages/PiSublime
```

### Step 2: Install the Pi Extension

```bash
mkdir -p ~/.pi/agent/extensions && ln -sf "$(pwd)/.pi/extensions/sublime.ts" ~/.pi/agent/extensions/sublime.ts
```

Now, whenever you run `pi` in your terminal, the extension will automatically load in the background. 

## Usage

Select some text or put the cursor where you want to prompt. Select the `Pi: Ask` command from Command Palette. A text box for prompt will appear, `Shift+Enter` for new line, `Enter` to submit.

If there is no running `Pi` session, user will be informed.

Otherwise, prompts you submit from Sublime Text will execute in a single `Pi` session using the following prioritisation:

1. **Single Session Default:** If there is exactly **one** active `Pi` session running on your system, it will be used regardless of directory matching.
2. **Directory Match:** If multiple sessions are running but only **one** matches the current file's folder (or any of its ancestor folders), that matching session will be used.
3. **Directory Recency Tie-Breaker:** If multiple sessions match the file's directory tree, the session that is **most recently active** (updated on each user prompt submission and session startup) will be used.
4. **Global Recency Fallback:** If multiple sessions are running but **none** match the current file's directory tree, the session that is **most recently active** globally will be used.

## Features
- `pi.py`: Contains the `Pi: Ask` command. Prompt Pi about selected text.
- `Context.sublime-menu`: Adds the command to the right-click menu.
- `Main.sublime-menu`: Adds the command to the Tools > Pi menu.

## How It Works

This integration is built on a high-performance, completely serverless, Unix-native architecture using **Unix Domain Sockets (UDS)**:

1. **Session Registration**:
   When you start a `Pi` terminal session, the Sublime extension generates a unique **UUID** and starts a local socket server. It writes two lightweight files to your `~/.pi/` directory:
   - `sublime-session-${uuid}.json`: Stores metadata including the working directory (`cwd`) and the last-active timestamp (updated on each user prompt submission).
   - `sublime-session-${uuid}.sock`: The Unix Domain Socket file, managed in-memory by the OS kernel.

2. **Liveness Verification & Crash Cleanup**:
   When you submit a prompt in Sublime, the plugin scans for `sublime-session-*.json` files. It attempts a socket connection to each to check liveness.
   - If a connection is refused, Sublime knows instantly that the process has exited or crashed, and automatically purges the stale `.json` and `.sock` files from disk.
   - If no sessions are alive, Sublime displays an error dialog and preserves your typed prompt in the panel.

3. **Prioritisation & Folder Matching**:
   If multiple terminal sessions are active, Sublime evaluates which one to send your prompt to by looking up the current file's folder tree:
   - If there is only one session active globally, it is used.
   - If only one session's working directory (`cwd`) matches the current file's folder (or any parent/ancestor folders), it is used.
   - If multiple sessions match the file's folder tree, or if zero sessions match, it falls back to the session that was **most recently active** (updated on each user prompt submission).

4. **Synchronous Handshake Delivery**:
   Once targeted, Sublime writes your selection and prompt directly into the socket and receives an `"OK"` handshake. The Pi extension feeds the message straight into the terminal, executing it instantly.