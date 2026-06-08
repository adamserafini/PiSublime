# PiSublime

A Sublime Text 4 plugin to send code selections and prompts directly to your active `Pi` terminal session.

## Installation

Clone this repository onto your computer. This plugin is currently tested only on **macOS**. It might work on Linux or Windows if the installation paths below were adjusted.

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

1. **Global Fallback:** If there is exactly **one** active `Pi` session running on your system, it will be used.
2. **Directory Match:** If multiple sessions are running but only **one** matches the current file's folder (or any of its ancestor folders), that matching session will be used.
3. **Recency Tie-Breaker:** If multiple sessions match the file's directory tree, the session that **most recently** received a user or assistant message will be used.

## Included Features
- `pi.py`: Contains the `Pi: Ask` command. Prompt Pi about selected text.
- `Context.sublime-menu`: Adds the command to the right-click menu.
- `Main.sublime-menu`: Adds the command to the Tools > Pi menu.
