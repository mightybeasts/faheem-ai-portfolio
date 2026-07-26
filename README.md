# Faheem AI Portfolio

An AI-powered personal portfolio site with a conversational assistant that can answer questions about my projects, skills, and experience.

🔗 **Live site:** [faheem-ai-portfolio.onrender.com](https://faheem-ai-portfolio.onrender.com/)

## Overview

This portfolio goes beyond a static resume page — it includes an integrated AI chat assistant that visitors can talk to directly, powered by an LLM backend that answers questions using my actual project and skill data.

## Tech Stack

- **Backend:** FastAPI (Python)
- **LLM:** Groq API (Llama 3.3) in production, Ollama for local development
- **Frontend:** HTML, CSS, JavaScript
- **Data:** Markdown files injected directly into prompts for context
- **Deployment:** Render (auto-deploy via GitHub)

## Project Structure

```
faheem-ai-portfolio/
├── backend/         # FastAPI app, LLM integration
├── frontend/        # HTML/CSS/JS UI
├── data/            # Markdown context files for the assistant
├── requirements.txt
└── .gitignore
```

## Running Locally

```bash
# clone the repo
git clone https://github.com/mightybeasts/faheem-ai-portfolio.git
cd faheem-ai-portfolio

# install dependencies
pip install -r requirements.txt

# run the backend
cd backend
uvicorn main:app --reload
```

Set up your local `.env` with the required API keys (Groq API key for production-style responses, or point to a local Ollama instance for development).

## About Me

I'm a final-semester MCA student, currently building AI/ML and full-stack projects while actively exploring software engineering roles. Other projects include:
- **SkillSight** — NLP-based resume-to-job matcher (TF-IDF + cosine similarity)
- **TripMind** — Gemini API-powered travel planner
- **BlackSpades** — Live React/Three.js esports client site

## Contact

Feel free to reach out via the links on the portfolio site itself.
