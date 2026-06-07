# PiSublime

A Sublime Text 4 plugin to instantly send code selections and prompts directly to your active Pi terminal session.

## Installation

To install and enable this plugin, you need to complete two quick steps:

### Step 1: Install the Sublime Text 4 Plugin
Symlink this repository to your Sublime Text `Packages` directory:

**macOS:**
```bash
ln -s "$(pwd)" ~/Library/Application\ Support/Sublime\ Text/Packages/PiSublime
```

### Step 2: Install the Pi Extension (Required)
To allow Sublime Text to instantly inject your typed prompts directly into your active Pi terminal session, run this command from the root of this repository to create your global Pi extensions folder and symlink the integration extension:

```bash
mkdir -p ~/.pi/agent/extensions && ln -sf "$(pwd)/.pi/extensions/sublime.ts" ~/.pi/agent/extensions/sublime.ts
```

Now, whenever you run `pi` in your terminal, the extension will automatically load in the background, and any prompts you submit from Sublime Text will instantly execute in your active terminal!

## Included Features
- `pi.py`: Contains the `Pi: Ask` command.
- `Context.sublime-menu`: Adds the command to the right-click menu.
- `Main.sublime-menu`: Adds the command to the Tools > Pi menu.
