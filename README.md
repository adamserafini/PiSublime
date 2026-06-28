<div align="center">
  <h1>PiSublime</h1>
  <p><strong>Sublime Text 4 plugin and <code>Pi</code> companion extension</strong></p>
  <p>
    <a href="#installation"><b>Installation</b></a> &bull;
    <a href="#usage"><b>Usage</b></a> &bull;
    <a href="#how-it-works"><b>How It Works</b></a>
  </p>
  <hr>
</div>

A Sublime Text 4 plugin and `Pi` companion extension that enables:

1. Sending selected context directly to your active `Pi` terminal session.
1. Hyperlinking from `Pi` terminal sessions to the relevant code in Sublime Text 4 using [OSC 8 escape sequences](https://github.com/Alhadis/OSC8-Adoption/).

So far, these are the *only* two integrations I need between an editor and a terminal-based coding harness.

The idea for context injection is stolen from `aider`'s [watch files feature](https://aider.chat/docs/usage/watch.html). But in our case, instead of the harness watching the files, the editor watches `Pi` sessions and figures out which one the user is most likely working on.

## Installation

Note: hyperlinking to ST4 from `Pi` only works on MacOSX.

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

### Context Injection

Select some text, put the cursor where you want to prompt or right-click a file or folder in the sidebar and select the `Pi: Ask` command from the context menu or Command Palette. A text box for prompt will appear, `Shift+Enter` for new line, `Enter` to submit.

If there is no running `Pi` session, user will be informed.

Otherwise, prompts you submit from Sublime Text will execute in a single `Pi` session using the following prioritisation:

1. **Single Session Default:** If there is exactly **one** active `Pi` session running on your system, it will be used regardless of directory matching.
1. **Directory Match:** If multiple sessions are running but only **one** matches the current file's folder (or any of its ancestor folders), that matching session will be used.
1. **Directory Recency Tie-Breaker:** If multiple sessions match the file's directory tree, the session that is **most recently active** (updated on each user prompt submission and session startup) will be used.
1. **Global Recency Fallback:** If multiple sessions are running but **none** match the current file's directory tree, the session that is **most recently active** globally will be used.

### Hyperlinking

If your terminal supports [OSC 8 escape sequences](https://github.com/Alhadis/OSC8-Adoption/), paths to files or lines of codes in a file in a `Pi` terminal session will be clickable hyperlinks and will open the file at the relevant line in ST4.

## How It Works

### Context Injection

The `Pi` extension starts a Unix Domain Socket server at `~/.pi/sublime-session-${uuid}.sock` for each terminal session and registers its workspace path (`cwd`) and activity time in a matching JSON file. When an agent starts responding to a prompt, the activity time is updated in this JSON file.

Before submitting a prompt, the Sublime plugin verifies active sessions by connecting to their sockets. Stale/crashed session files are deleted. The Sublime plugin selects the best matching session and writes the prompt to its socket. The `Pi` extension reads from the socket and injects the prompt as a user message.

On exit, the `Pi` extension cleans up the socket and file.

### Hyperlinking

The project includes a `SublHandler.applescript` implementing a basic `subl` OS-level protocol handler, associating itself with URLs like this:

```text
subl://open?url=file:///Some/path/pisublime.ts&line=78
```

This protocol handler gets compiled and registered to the OS when the Sublime plug-in is loaded, translating the URL to shell invocation of the `subl` CLI, which conveniently, accepts a `:line` suffix in its path argument.

The `Pi` extension makes a tiny modification to the system prompt, encouraging your LLM to write paths in the colon-notation format (`path/to/file.ext:line`). Assistant messages and tool execution results are intercepted to find file paths (e.g., `src/main.ts:15` or `src/main.ts:78-91`). It converts these text patterns into interactive terminal links using OSC 8 escape sequences wrapping the `subl://open?url=file://...` protocol.

Crucially, the extension also hooks into the `"context"` event to strip these raw terminal escape sequences before they are sent back to the LLM. This keeps the prompt history clean, saves tokens, and prevents the LLM from trying to output raw terminal control characters or getting confused during tool calls.

## Things I'm Not Happy About

As this is currently working for *me*, and I suspect the intersection between `Pi` and Sublime Text 4 users is quite small, my motivation to fix these problems is fairly low. But feel free to leave an issue or even make PRs if you'd like to inject me with additional enthusiasm.

### Tests

Hahaha. Good one. But seriously, the hyperlinking is surprisingly fiddly and involves regex. Some tests would probably illuminate whether it does, in fact, work as intended.

### Protocol

The OS-level protocol (`subl://`) only works on Mac OSX. To be honest, a `subl` protocol would be a useful, stand-alone, cross-OS project, but as I don't currently have requirements for one beyond this use-case, and it would involve testing on Windows and Linux, it's not a project I currently have any interest in.
