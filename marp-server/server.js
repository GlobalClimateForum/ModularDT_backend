import express from "express";
import { Marp } from "@marp-team/marp-core";
import fs from "fs";
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


const SCALING_CSS = `
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: white;
  }
  body {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .marpit {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .marpit > svg,
  svg[data-marpit-svg] {
    width: 100% !important;
    height: 100% !important;
    max-width: 100%;
    max-height: 100%;
    display: block;
  }

  section { 
  border: none !important; 
  background: white !important; 
}
`;
// Render endpoint 
app.use(express.text({ type: "*/*", limit: "1mb" }));

app.post("/render", (req, res) => {
  try {
    const { html, css } = marp.render(req.body);
    res.json({ html, css: css + SCALING_CSS });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
app.listen(3000);

