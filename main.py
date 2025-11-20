import os
from typing import List, Optional, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    llm: Literal["gpt-4o", "gpt-4.1", "claude-3.5", "gemini-1.5", "llama-3.1", "mistral-large"] = Field(
        ..., description="Target model identifier"
    )
    project_name: str = Field(..., description="Name of the website or brand")
    site_type: Literal[
        "landing", "marketing", "portfolio", "blog", "docs", "saas", "ecommerce"
    ] = Field(..., description="Type of website")
    tone: Literal[
        "professional", "friendly", "playful", "minimal", "luxury", "technical"
    ] = "professional"
    target_audience: Optional[str] = ""
    brand_colors: Optional[str] = ""
    features: List[str] = []
    pages: List[str] = []
    seo_keywords: List[str] = []
    constraints: Optional[str] = ""
    preferred_stack: List[str] = []  # e.g. ["React", "Tailwind", "Next.js"]
    deliverables: List[str] = [
        "site map",
        "content outline",
        "wireframe description",
        "component list",
        "responsive behavior",
        "SEO meta tags",
        "accessibility checklist",
    ]
    output_format: Literal["markdown", "plain", "json"] = "markdown"

class PromptResponse(BaseModel):
    prompt: str
    llm: str

@app.get("/")
def read_root():
    return {"message": "AI Prompt Assistant Backend"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db  # type: ignore
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:  # pragma: no cover
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (optional)"
    except Exception as e:  # pragma: no cover
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# --- Prompt generation logic ---
MODEL_STYLES = {
    "gpt-4o": {
        "system": "You are a senior product + UX + frontend architect. Produce precise, concise, implementation-ready instructions.",
        "notes": "Favor bullet points and code-ready sections."
    },
    "gpt-4.1": {
        "system": "You are a meticulous technical writer and UI engineer.",
        "notes": "Prefer structured lists and explicit acceptance criteria."
    },
    "claude-3.5": {
        "system": "You are thoughtful and reflective. Explain trade-offs and propose alternatives.",
        "notes": "Provide checklists and reasoning sections."
    },
    "gemini-1.5": {
        "system": "You are multi-modal product designer + engineer.",
        "notes": "If images are referenced, describe them. Keep steps explicit."
    },
    "llama-3.1": {
        "system": "You are an open-source web architect. Be explicit and deterministic.",
        "notes": "Avoid ambiguity; include clear file/component breakdowns."
    },
    "mistral-large": {
        "system": "You are a pragmatic frontend tech lead.",
        "notes": "Use concise instructions with numbered steps."
    },
}

def bjoin(items: List[str]) -> str:
    return "\n".join([f"- {i}" for i in items]) if items else "- (none)"

@app.post("/api/generate-prompt", response_model=PromptResponse)
def generate_prompt(req: PromptRequest):
    style = MODEL_STYLES.get(req.llm)
    if not style:
        raise HTTPException(status_code=400, detail="Unsupported model")

    features = bjoin(req.features)
    pages = bjoin(req.pages)
    keywords = bjoin(req.seo_keywords)
    stack = bjoin(req.preferred_stack)
    deliverables = bjoin(req.deliverables)

    header = f"Model: {req.llm}\nProject: {req.project_name}\nType: {req.site_type}\nTone: {req.tone}\n"

    core = f"""
[SYSTEM]
{style['system']}
Additional notes: {style['notes']}

[OBJECTIVE]
Design and outline a complete website for "{req.project_name}".

[CONTEXT]
Target audience: {req.target_audience or 'General web audience'}
Brand colors or theme: {req.brand_colors or 'To be proposed'}
Constraints: {req.constraints or 'None specified'}
Preferred stack: \n{stack}

[WEBSITE TYPE]
{req.site_type}

[FEATURES]
{features}

[PAGES]
{pages}

[SEO]
Primary keywords:\n{keywords}

[DELIVERABLES]
Produce the following, optimized for the selected model:\n{deliverables}

[STYLE GUIDE]
- Voice and tone: {req.tone}
- Accessibility: WCAG 2.2 AA; include landmarks, color contrast, keyboard nav.
- Performance: lazy-load media, compress assets, minimal JavaScript where possible.

[OUTPUT]
Preferred output format: {req.output_format}
Provide sections with clear headings. Include copy examples, component names, and acceptance criteria for each page. Where relevant, provide Tailwind utility examples.
""".strip()

    return PromptResponse(prompt=f"{header}\n\n{core}", llm=req.llm)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
