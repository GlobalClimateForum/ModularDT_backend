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

// Render endpoint 
app.use(express.text({ type: "*/*", limit: "1mb" }));

app.post("/render", (req, res) => {
  try {
    const { html, css } = marp.render(req.body);
    res.json({ html, css });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
    
app.listen(3000);