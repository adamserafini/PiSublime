# PiSublime

A Sublime Text 4 plugin to send code selections and prompts directly to your active `Pi` terminal session.

## Installation

Clone this repository onto your computer. This plugin is currently tested only on **macOS** and only **manually**. It might work on Linux or Windows if the installation paths below were adjusted.

### Step 1: Install the Sublime Text 4 Plugin

```bash
ln -s "$(pwd)" ~/Library/Application\ Support/Sublime\ Text/Packages/PiSublime
```

### Step 2: Install the Pi Extension

Install the Pi extension package directly into your global Pi settings. This registers the background socket server and enables clickable terminal hyperlinks to open files and line ranges directly in Sublime Text.

You can install it directly from GitHub:

```bash
pi install git:github.com/adamserafini/PiSublime
```

Or, if you are developing locally, install from the root of your cloned repository:

```bash
pi install .
```

## Usage

Select some text or put the cursor where you want to prompt. Select the `Pi: Ask` command from Command Palette. A text box for prompt will appear, `Shift+Enter` for new line, `Enter` to submit.

If there is no running `Pi` session, user will be informed.

Otherwise, prompts you submit from Sublime Text will execute in a single `Pi` session using the following prioritisation:

1. **Single Session Default:** If there is exactly **one** active `Pi` session running on your system, it will be used regardless of directory matching.
1. **Directory Match:** If multiple sessions are running but only **one** matches the current file's folder (or any of its ancestor folders), that matching session will be used.
1. **Directory Recency Tie-Breaker:** If multiple sessions match the file's directory tree, the session that is **most recently active** (updated on each user prompt submission and session startup) will be used.
1. **Global Recency Fallback:** If multiple sessions are running but **none** match the current file's directory tree, the session that is **most recently active** globally will be used.

## Features

- `pi.py`: Contains the `Pi: Ask` command. Prompt Pi about selected text.
- `Context.sublime-menu`: Adds the command to the right-click menu.
- `Main.sublime-menu`: Adds the command to the Tools > Pi menu.

## How It Works

The `Pi` extension starts a Unix Domain Socket server at `~/.pi/sublime-session-${uuid}.sock` for each terminal session and registers its workspace path (`cwd`) and activity time in a matching JSON file. When an agent starts responding to a prompt, the activity time is updated in this JSON file.

Before submitting a prompt, the Sublime plugin verifies active sessions by connecting to their sockets. Stale/crashed session files are deleted. The Sublime plugin selects the best matching session and writes the prompt to its socket. The `Pi` extension reads from the socket and injects the prompt as a user message.

On exit, the `Pi` extension cleans up the socket and file.
