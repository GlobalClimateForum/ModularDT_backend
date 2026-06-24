import express from "express";
import { Marp } from "@marp-team/marp-core";
import cors from "cors";

// Initialize Express app and Marp instance
const app = express();
app.use(cors());
const marp = new Marp({ html: true, script: false });

// Default endpoint
app.get("/", (req, res) => {
  res.send("Welcome to the Marp slide server! Access /api/slides to get the rendered slides.");
});

// To silence chrome "DevTools"
app.get("/.well-known/appspecific/com.chrome.devtools.json", (req, res) => {
  res.status(204).end();
});

const ALLOWED_ASPECT_RATIOS = new Set(["16:9", "4:3"]);

// Injects `size:` into existing front matter, or creates a front-matter block if none exists.
// Respects a caller-authored `size:` directive if the markdown already has one.
function withSizeDirective(markdown, aspectRatio) {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) return `---\nsize: ${aspectRatio}\n---\n\n${markdown}`;
  if (/^size:/m.test(match[1])) return markdown;
  return `---\n${match[1]}\nsize: ${aspectRatio}\n---\n${markdown.slice(match[0].length)}`;
}

// Marp already sizes the slide's viewBox/font/padding for the chosen aspect ratio;
// this just lets the SVG fill whatever box it's displayed in while preserving that ratio.
const fitting_css = `
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }
  div.marpit > svg { display: block !important; width: 100% !important; height: 100% !important; }
  section { border: none !important; }
`;

// Render endpoint
app.use(express.json());

app.post("/render", (req, res) => {
  try {
    const aspectRatio = ALLOWED_ASPECT_RATIOS.has(req.body.aspectRatio) ? req.body.aspectRatio : "16:9";
    const { html, css } = marp.render(withSizeDirective(req.body.content, aspectRatio));

    res.json({ html, css: css + fitting_css });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
app.listen(3000);
