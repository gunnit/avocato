import express from 'express';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config();

const app = express();

// Middleware for basic request logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Serve static files
app.use(express.static('public'));

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({ status: "attivo", service: "API Assistente Legale Italiano" });
});

// Session token endpoint for legal consultations
app.get("/session", async (req, res) => {
  try {
    const r = await fetch("https://api.openai.com/v1/realtime/sessions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-realtime-preview-2024-12-17",
        voice: "onyx", // Using a more formal voice for legal context
      }),
    });
    const data = await r.json();
    res.json(data);
  } catch (error) {
    console.error('Errore di inizializzazione sessione:', error);
    res.status(500).json({ 
      error: 'Impossibile inizializzare la sessione di consulenza legale',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Errore del server:', err);
  res.status(500).json({
    error: 'Errore interno del server',
    details: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server Assistente Legale Italiano in esecuzione sulla porta ${PORT}`);
  console.log(`Ambiente: ${process.env.NODE_ENV || 'development'}`);
});
