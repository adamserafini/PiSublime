# PiSublime

A Sublime Text 4 plugin to send code selections and prompts directly to your active Pi terminal session.

## Installation

Clone this repository onto your computer.

### Step 1: Install the Sublime Text 4 Plugin
Symlink this repository to your Sublime Text `Packages` directory:

**macOS:**
```bash
ln -s "$(pwd)" ~/Library/Application\ Support/Sublime\ Text/Packages/PiSublime
```

### Step 2: Install the Pi Extension

```bash
mkdir -p ~/.pi/agent/extensions && ln -sf "$(pwd)/.pi/extensions/sublime.ts" ~/.pi/agent/extensions/sublime.ts
```

Now, whenever you run `pi` in your terminal, the extension will automatically load in the background, and any prompts you submit from Sublime Text will instantly execute in your active terminal.

## Included Features
- `pi.py`: Contains the `Pi: Ask` command. Prompt Pi about selected text.
- `Context.sublime-menu`: Adds the command to the right-click menu.
- `Main.sublime-menu`: Adds the command to the Tools > Pi menu.
