import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import * as net from "node:net";
import * as crypto from "node:crypto";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
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
      console.error("Pi Sublime Extension: Failed to create .pi directory:", e);
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
            // Update last activity whenever we receive a message from Sublime
            touchSessionFile();

            if (ctx.isIdle()) {
              pi.sendUserMessage(content);
            } else {
              pi.sendUserMessage(content, { deliverAs: "steer" });
              if (ctx.hasUI) {
                ctx.ui.notify("Sublime prompt queued as steering", "info");
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

    // Also update last activity when agent starts a turn
    pi.on("agent_start", async () => {
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
      ctx.ui.notify("Pi Sublime integration active!", "info");
    }
  });
}
