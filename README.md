# PiSublime

A Sublime Text 4 plugin.

## Sublime Text 4 Installation

To load this plugin into Sublime Text 4, you can symlink this repository to your Sublime Text `Packages` directory:

**macOS:**
```bash
ln -s "$(pwd)" ~/Library/Application\ Support/Sublime\ Text/Packages/PiSublime
```

## Included Features
- `pi.py`: Contains the `Pi: Ask` command.
- `Context.sublime-menu`: Adds the command to the right-click menu.
- `Main.sublime-menu`: Adds the command to the Tools > Pi menu.

## Background Pi Session Integration (Optional)

This plugin includes an integration that instantly injects your typed questions directly into an active Pi terminal session.

To enable this globally across all your projects:

1. Create the global Pi extensions directory if it doesn't exist:
   ```bash
   mkdir -p ~/.pi/agent/extensions
   ```

2. Copy the included Sublime integration extension to your global folder:
   ```bash
   cp .pi/extensions/sublime.ts ~/.pi/agent/extensions/sublime.ts
   ```

Now, whenever you run `pi` in your terminal, the extension will automatically load in the background. Any questions you submit from Sublime Text will immediately run in your active terminal!
