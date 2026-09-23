import express from "express";
import { Marp } from "@marp-team/marp-core";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

function buildSizeTheme(width, height, bgColor, baseTheme = "default") {
  return `
          /* @theme sized */
          @import '${baseTheme}';

          section {
            width: ${width}px !important;
            height: ${height}px !important;
            background-color: ${bgColor} !important;
          }
            `;
}

function injectSizeTheme(content) {
  
  // Get the frontmatter from the content
  const frontmatter_re = /^---\n([\s\S]*?)\n---/;
  const frontmatter_match = content.match(frontmatter_re);

  // Assume default theme if no theme is defined
  let basetheme = "default";

  // If a frontmatter exists
  if (frontmatter_match) {
   
    // Check if a theme is already defined in the frontmatter
    const theme_re = /theme:\s*(\w+)/;
    const frontmatter = frontmatter_match[1];
    const theme_match = frontmatter.match(theme_re);
    
    // If a theme is defined, replace it with "sized"
    if (theme_match) {
      basetheme = theme_match[1];
      const new_frontmatter = frontmatter.replace(theme_re, `theme: sized`);
      content = content.replace(frontmatter_re, `---\n${new_frontmatter}\n---`);
    }else{
      // If no theme is defined, add "theme: sized" to the frontmatter
      const new_frontmatter = `${frontmatter}\ntheme: sized`;
      content = content.replace(frontmatter_re, `---\n${new_frontmatter}\n---`);
    }
  }else{
    // If no frontmatter exists, add a new frontmatter with "marp: true" and "theme: sized"
    content = `---\nmarp: true\ntheme: sized\n---\n${content}`;
  }

  return { content, basetheme };
}

app.get("/", (req, res) => {
  res.send("Welcome to the Marp slide server!");
});

app.get("/.well-known/appspecific/com.chrome.devtools.json", (req, res) => {
  res.status(204).end();
});

app.post("/render", (req, res) => {
  try {
    const { content, width = 1280, height = 720, bgColor = 'white', theme = "default" } = req.body;
    // ensure a leading # for the bgColor if it's a hex color
    const normalizedBgColor = bgColor.startsWith('#') ? bgColor : `#${bgColor}`;
    const { content: updatedContent, basetheme } = injectSizeTheme(content);
    const marp = new Marp({ html: true, script: false });
    marp.themeSet.add(buildSizeTheme(width, height, normalizedBgColor, basetheme));
    const { html, css } = marp.render(updatedContent);

    const document = `<!DOCTYPE html>
        <html>
        <head>
          <style>
            html, body {
              margin: 0;
              padding: 0;
              overflow: hidden;
            }
            ${css}
          </style>
        </head>
        <body>
          ${html}
        </body>
        </html>`;
    res.json({ html: document });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
app.listen(3000);
