import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import * as net from "node:net";
import * as crypto from "node:crypto";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Helper to convert plain file:line or file paths to OSC 8 terminal hyperlinks
function replaceWithClickableLinks(text: string): string {
  // Regex to match path-like structures with an optional line number or range:
  // e.g. /path/to/file.ext:123 or path/to/file.ext:78-91 or path/to/file.ext
  const regex = /(?:^|[\s"'`(])(\/?[\w_.-]+(?:\/[\w_.-]+)*\.[a-zA-Z0-9]+)(?::(\d+)(?:-\d+)?)?\b/g;

  return text.replace(regex, (match, filePath, line) => {
    // Keep prefix if there was a space, quote, or parenthesis
    const prefix = match.match(/^[^\w_.-]/)?.[0] || "";
    try {
      const absolutePath = path.resolve(filePath);
      if (fs.existsSync(absolutePath) && fs.statSync(absolutePath).isFile()) {
        const lineParam = line ? `&line=${line}` : "";
        const displayText = match.slice(prefix.length);
        const link = `\x1b]8;;subl://open?url=file://${absolutePath}${lineParam}\x1b\\${displayText}\x1b]8;;\x1b\\`;
        return prefix + link;
      }
    } catch (e) {
      // Ignore resolution errors
    }
    return match;
  });
}

// Helper to strip OSC 8 terminal hyperlink escape sequences, preserving only display text
function stripClickableLinks(val: any): any {
  if (typeof val === "string") {
    return val.replace(/\x1b\]8;;[^\x1b]*\x1b\\([^\x1b]*)\x1b\]8;;\x1b\\/g, "$1");
  }
  if (Array.isArray(val)) {
    return val.map(stripClickableLinks);
  }
  if (val && typeof val === "object") {
    const res: any = {};
    for (const key of Object.keys(val)) {
      res[key] = stripClickableLinks(val[key]);
    }
    return res;
  }
  return val;
}

// Helper to strip OSC 8 links from message contents
function stripLinksFromMessageContent(content: any): any {
  if (typeof content === "string") {
    return stripClickableLinks(content);
  }
  if (Array.isArray(content)) {
    return content.map(block => {
      if (block && typeof block === "object") {
        if (block.type === "text" && typeof block.text === "string") {
          return {
            ...block,
            text: stripClickableLinks(block.text)
          };
        }
      }
      return block;
    });
  }
  return content;
}

export default function (pi: ExtensionAPI) {
  // --- Section 1: Sublime Text socket server and communication ---
  pi.on("session_start", async (_event, ctx) => {
    const piDir = path.join(os.homedir(), ".pi");
    const uuid = crypto.randomUUID();
    const sessionFile = path.join(piDir, `sublime-session-${uuid}.json`);
    const socketPath = path.join(piDir, `sublime-session-${uuid}.sock`);

    // Ensure directory exists
    try {
      if (!fs.existsSync(piDir)) {
        fs.mkdirSync(piDir, { recursive: true });
      }
    } catch (e) {
      console.error("PiSublime Extension: Failed to create .pi directory:", e);
      return;
    }

    const touchSessionFile = () => {
      try {
        fs.writeFileSync(
          sessionFile,
          JSON.stringify({
            uuid,
            cwd: process.cwd(),
            lastActivity: Date.now(),
          })
        );
      } catch (e) {
        // ignore
      }
    };

    // Spin up Unix Domain Socket Server with allowHalfOpen enabled
    const server = net.createServer({ allowHalfOpen: true }, (socket) => {
      // Handle socket errors gracefully so they don't crash Pi
      socket.on("error", (err) => {
        // Gracefully ignore connection/socket errors
      });

      let body = "";
      socket.on("data", (chunk) => {
        body += chunk.toString();
      });

      socket.on("end", () => {
        try {
          const content = body.trim();
          if (content) {
            if (ctx.isIdle()) {
              pi.sendUserMessage(content);
            } else {
              pi.sendUserMessage(content, { deliverAs: "steer" });
              if (ctx.hasUI) {
                ctx.ui.notify("Sublime prompt queued as steering.", "info");
              }
            }
          }
          // Send success handshake back to Sublime
          socket.write("OK");
        } catch (err) {
          // Ignore write errors on closed/closing socket
        } finally {
          socket.end();
        }
      });
    });

    // Start listening on the Unix Domain Socket
    server.listen(socketPath, () => {
      // Create session JSON file once socket is listening
      touchSessionFile();
    });

    // Update last activity when agent starts execution (corresponds with a user having submitted a prompt)
    pi.on("agent_start", () => {
      touchSessionFile();
    });

    const cleanup = () => {
      try {
        server.close();
        if (fs.existsSync(sessionFile)) {
          fs.unlinkSync(sessionFile);
        }
        if (fs.existsSync(socketPath)) {
          fs.unlinkSync(socketPath);
        }
      } catch (e) {
        // ignore
      }
    };

    // Clean up on exit
    process.on("exit", cleanup);
    process.on("SIGINT", () => {
      cleanup();
      process.exit();
    });
    process.on("SIGTERM", () => {
      cleanup();
      process.exit();
    });

    if (ctx.hasUI) {
      ctx.ui.notify("PiSublime integration is active.", "info");
    }
  });

  // --- Section 2: Interactive terminal link generation and formatting ---

  // Inject instructions to the system prompt to guide the LLM to write clickable links
  pi.on("before_agent_start", async (event, _ctx) => {
    const hint = "When referring to lines of code in specific files, always use the colon-notation format `path/to/file.ext:line` (e.g., `src/main.ts:15`)";
    
    return {
      systemPrompt: event.systemPrompt + "\n" + hint
    };
  });

  // Intercept tool results (like bash outputs or read results) to make files:lines clickable
  pi.on("tool_result", async (event, _ctx) => {
    if (!event.content) return;
    const newContent = event.content.map(block => {
      if (block.type === "text" && block.text) {
        return {
          ...block,
          text: replaceWithClickableLinks(block.text)
        };
      }
      return block;
    });
    return { content: newContent };
  });

  // Intercept assistant messages to make files:lines clickable
  pi.on("message_end", async (event, _ctx) => {
    if (event.message.role !== "assistant") return;
    
    if (typeof event.message.content === "string") {
      return {
        message: {
          ...event.message,
          content: replaceWithClickableLinks(event.message.content)
        }
      };
    } else if (Array.isArray(event.message.content)) {
      const newContent = event.message.content.map(block => {
        if (block.type === "text" && block.text) {
          return {
            ...block,
            text: replaceWithClickableLinks(block.text)
          };
        }
        return block;
      });
      return {
        message: {
          ...event.message,
          content: newContent
        }
      };
    }
  });

  // Clean up messages sent to the LLM so it never sees OSC 8 hyperlink escape sequences.
  // This prevents LLM confusion, token waste, and accidental raw escape sequence outputs in tool calls or code.
  pi.on("context", async (event, _ctx) => {
    const cleanedMessages = event.messages.map(m => {
      return {
        ...m,
        content: stripLinksFromMessageContent(m.content)
      };
    });
    return { messages: cleanedMessages };
  });

  // Clean up tool call arguments to strip any accidental OSC 8 sequences before execution.
  pi.on("tool_call", async (event, _ctx) => {
    if (event.input) {
      for (const key of Object.keys(event.input)) {
        event.input[key] = stripClickableLinks(event.input[key]);
      }
    }
  });
}
