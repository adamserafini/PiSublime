import * as fs from "node:fs";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Helper to convert plain file:line or file paths to OSC 8 terminal hyperlinks
function replaceWithClickableLinks(text: string): string {
  // Regex to match path-like structures with an optional line number:
  // e.g. /path/to/file.ext:123 or path/to/file.ext
  const regex = /(?:^|[\s"'`(])(\/?[\w_.-]+(?:\/[\w_.-]+)*\.[a-zA-Z0-9]+)(?::(\d+))?\b/g;

  return text.replace(regex, (match, filePath, line) => {
    // Keep prefix if there was a space, quote, or parenthesis
    const prefix = match.match(/^[^\w_.-]/)?.[0] || "";
    try {
      const absolutePath = path.resolve(filePath);
      if (fs.existsSync(absolutePath) && fs.statSync(absolutePath).isFile()) {
        const lineParam = line ? `&line=${line}` : "";
        const displayText = line ? `${filePath}:${line}` : filePath;
        const link = `\x1b]8;;subl://open?url=file://${absolutePath}${lineParam}\x1b\\${displayText}\x1b]8;;\x1b\\`;
        return prefix + link;
      }
    } catch (e) {
      // Ignore resolution errors
    }
    return match;
  });
}

export default function (pi: ExtensionAPI) {
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
}
