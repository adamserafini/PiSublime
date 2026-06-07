import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    const piDir = path.join(os.homedir(), ".pi");
    const triggerFile = path.join(piDir, "sublime-ask.txt");

    // Ensure directory and trigger file exist
    try {
      if (!fs.existsSync(piDir)) {
        fs.mkdirSync(piDir, { recursive: true });
      }
      if (!fs.existsSync(triggerFile)) {
        fs.writeFileSync(triggerFile, "");
      }
    } catch (e) {
      console.error("Pi Sublime Extension: Failed to initialize trigger file:", e);
    }

    // Watch the trigger file
    fs.watch(triggerFile, () => {
      try {
        if (!fs.existsSync(triggerFile)) return;
        const content = fs.readFileSync(triggerFile, "utf-8").trim();
        if (content) {
          // Clear the file immediately
          fs.writeFileSync(triggerFile, "");

          if (ctx.isIdle()) {
            pi.sendUserMessage(content);
          } else {
            pi.sendUserMessage(content, { deliverAs: "steer" });
            if (ctx.hasUI) {
              ctx.ui.notify("Sublime question queued as steering", "info");
            }
          }
        }
      } catch (e) {
        // File may be locked or temporarily inaccessible
      }
    });

    if (ctx.hasUI) {
      ctx.ui.notify("Pi Sublime integration active!", "info");
    }
  });
}
