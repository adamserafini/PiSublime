# PiSublime

A Sublime Text 4 plugin to send code selections and prompts directly to your active `Pi` terminal session.

## Installation

Prerequisite: have the `subl` CLI [installed](https://www.sublimetext.com/docs/command_line.html).

### Step 1: Install the Sublime Text 4 Plugin

Clone this repository and symlink it into your Sublime Text packages directory:

```bash
# Clone the repository
git clone https://github.com/adamserafini/PiSublime.git
cd PiSublime

# Symlink it to your Sublime Text Packages directory
ln -s "$(pwd)" ~/Library/Application\ Support/Sublime\ Text/Packages/PiSublime
```

### Step 2: Install the Pi Extension

Install from the root of your cloned repository:

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

### Hyperlinking

The project includes a `SublHandler.applescript` that implements a basic `subl` OS-level protocol handler, which associates with URLs like this:

```text
subl://open?url=file:///Users/adamserafini/Code/PiSublime/extensions/pisublime.ts&line=78
```

This protocol handler is registered to the OS, allowing you to click file paths directly inside your Pi terminal outputs and have them instantly open at the correct line in Sublime Text.

## Features

- `pi.py`: Contains the `Pi: Ask` command. Prompt Pi about selected text.
- `Context.sublime-menu`: Adds the command to the right-click menu.
- `Main.sublime-menu`: Adds the command to the Tools > Pi menu.

## How It Works

The `Pi` extension starts a Unix Domain Socket server at `~/.pi/sublime-session-${uuid}.sock` for each terminal session and registers its workspace path (`cwd`) and activity time in a matching JSON file. When an agent starts responding to a prompt, the activity time is updated in this JSON file.

Before submitting a prompt, the Sublime plugin verifies active sessions by connecting to their sockets. Stale/crashed session files are deleted. The Sublime plugin selects the best matching session and writes the prompt to its socket. The `Pi` extension reads from the socket and injects the prompt as a user message.

On exit, the `Pi` extension cleans up the socket and file.

### Hyperlinking

The `pisublime` Pi extension intercepts assistant messages and tool execution results to find file paths (e.g., `src/main.ts:15` or `src/main.ts:78-91`). It converts these text patterns into interactive terminal links using OSC 8 escape sequences wrapping a `subl://open?url=file://...` protocol.

When you click a link in your terminal, the OS opens `SublHandler.app` (which is compiled from `SublHandler.applescript`). The app parses the file path and line number from the query parameters, then executes the `subl` binary to open the file and jump to the target line.

Crucially, the extension also hooks into the `"context"` event to strip these raw terminal escape sequences before they are sent back to the LLM. This keeps the prompt history clean, saves tokens, and prevents the LLM from trying to output raw terminal control characters or getting confused during tool calls.

## What I'm Not Happy About

### Tests

Hahaha. Good one.
