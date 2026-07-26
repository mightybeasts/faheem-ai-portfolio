import os
import json
from dotenv import load_dotenv
from typing import Any
from pathlib import Path

load_dotenv()

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field


# App setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Config
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL = os.getenv(
    "MODEL",
    "llama-3.3-70b-versatile"
)

DATA_DIR = Path(__file__).parent.parent / "data"
RESUME_PATH = DATA_DIR / "resume.pdf"


# Load markdown files
def load_data():
    parts = []

    for file in sorted(DATA_DIR.glob("*.md")):
        parts.append(
            f"=== {file.name} ===\n"
            + file.read_text(encoding="utf-8")
        )

    return "\n\n".join(parts)


# System prompt
def build_system_prompt():

    data = load_data()

    return f"""
You are Faheem's AI Portfolio Assistant.

Your role is to speak as if you ARE Faheem talking directly to visitors.

The goal is to help people understand who I am, what I build, what I learn, my projects, experience, interests, and goals.

Communication style:

* Speak in first person naturally.
* Say "I built...", "I worked on...", "I'm interested in...", "I've explored..."
* Never say "Faheem has..." or "Faheem worked..."
* Sound human, conversational, friendly, and confident.
* Explain things naturally instead of listing facts.
* Give thoughtful responses with context.
* Keep responses concise but meaningful.
* Expand where useful instead of giving one-line answers.

Information rules:

* Use the provided portfolio data as the primary source.
* If exact information is unavailable, infer carefully using available projects, education, technologies, certifications, and interests.
* Connect related information to provide better explanations.
* Never invent companies, jobs, achievements, timelines, or experience.

Response behavior:

* Do not act like a customer support bot.
* Do not say:

  * "Reach Faheem directly"
  * "Faheem has..."
  * "Information unavailable"
  * "I don't know"

Instead:

* Explain what IS available.
* Provide context.
* Answer naturally.

Examples:

Question:
"Do you have work experience?"

Good response:
"I don't currently have formal industry experience yet, but I've gained practical experience through academic and independent projects. I've worked on AI-based systems, full-stack applications, and explored modern development workflows which gave me hands-on exposure to building and solving real problems."

Question:
"What are your strengths?"

Good response:
"I enjoy turning ideas into working systems. A big strength of mine is learning quickly and applying concepts through projects. I've explored AI, application development, backend systems, and experimenting with new technologies."

Question:
"Tell me about yourself"

Good response:
"I'm an MCA graduate interested in building practical software systems, especially around AI and full-stack development. I enjoy creating projects that solve real problems and continuously experimenting with new technologies and ideas."

Question:
"What are your interests?"

Good response:
"I'm interested in AI systems, full-stack development, cybersecurity, machine learning, and I also enjoy gaming and football outside tech."

=== MY PORTFOLIO DATA ===

{data}

=== END ===


{data}

=== END ===
"""



# Request model
class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, Any]] = Field(default_factory=list)


# Build messages
def build_messages(req):

    messages = [

        {
            "role": "system",
            "content": build_system_prompt()
        }

    ]

    for turn in req.history[-10:]:

        role = turn.get("role")
        content = turn.get("content")

        if role in {"user", "assistant"} and content:

            messages.append(
                {
                    "role": role,
                    "content": content
                }
            )

    messages.append(
        {
            "role": "user",
            "content": req.message
        }
    )

    return messages


# AI call
async def call_ai(messages, stream=False):

    async with httpx.AsyncClient(timeout=None) as client:

        # GROQ
        if USE_GROQ:

            headers = {
                "Authorization":
                f"Bearer {GROQ_API_KEY}"
            }

            payload = {
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7,
                "stream": stream,
                "max_tokens": 512
            }

            url = (
                "https://api.groq.com"
                "/openai/v1/chat/completions"
            )

            if not stream:

                r = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )

                r.raise_for_status()

                return (
                    r.json()
                    ["choices"][0]
                    ["message"]
                    ["content"]
                )

            return client.stream(
                "POST",
                url,
                headers=headers,
                json=payload
            )

        # OLLAMA
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "num_predict": 512
            }
        }

        if not stream:

            r = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload
            )

            r.raise_for_status()

            return (
                r.json()
                ["message"]
                ["content"]
            )

        return client.stream(
            "POST",
            f"{OLLAMA_URL}/api/chat",
            json=payload
        )


# Routes
@app.get("/")
async def root():

    return FileResponse(
        str(
            Path(__file__)
            .parent.parent
            / "frontend"
            / "index.html"
        )
    )


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "provider":
            "groq"
            if USE_GROQ
            else "ollama",
        "model": MODEL
    }




@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):

    async def generate():

        messages = build_messages(req)

        try:

            headers = {
                "Authorization":
                f"Bearer {GROQ_API_KEY}"
            }

            async with httpx.AsyncClient(
                timeout=None
            ) as client:

                async with client.stream(
                    "POST",
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "stream": True,
                        "max_tokens": 700
                    }
                ) as response:

                    response.raise_for_status()

                    async for chunk in response.aiter_text():

                        lines = chunk.split("\n")

                        for line in lines:

                            if not line.startswith(
                                "data: "
                            ):
                                continue

                            payload = line[6:].strip()

                            if payload == "[DONE]":
                                return

                            try:

                                data = json.loads(
                                    payload
                                )

                                token = (

                                    data

                                    .get(
                                        "choices",
                                        [{}]
                                    )[0]

                                    .get(
                                        "delta",
                                        {}
                                    )

                                    .get(
                                        "content",
                                        ""
                                    )

                                )

                                if token:

                                    yield token

                            except:

                                continue

        except Exception as e:

            yield (
                f"\nStreaming Error: {str(e)}"
            )

    return StreamingResponse(
        generate(),
        media_type=
        "text/plain"
    )



@app.get("/resume/download")
async def resume_download():

    if not RESUME_PATH.exists():

        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    return FileResponse(
        str(RESUME_PATH),
        media_type="application/pdf",
        filename="Faheem_K_Resume.pdf",
    )


# Serve frontend
frontend_path = (
    Path(__file__)
    .parent.parent
    / "frontend"
)

if frontend_path.exists():

    app.mount(
        "/static",
        StaticFiles(
            directory=str(frontend_path)
        ),
        name="static",
    )


# Run
if __name__ == "__main__":

    import uvicorn

    print(
        "\nFaheem AI Portfolio running\n"
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )