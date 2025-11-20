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
        ..., description="Identificador do modelo alvo"
    )
    project_name: str = Field(..., description="Nome do site ou marca")
    site_type: Literal[
        "landing", "marketing", "portfolio", "blog", "docs", "saas", "ecommerce"
    ] = Field(..., description="Tipo de site")
    tone: Literal[
        "professional", "friendly", "playful", "minimal", "luxury", "technical"
    ] = "professional"
    target_audience: Optional[str] = ""
    brand_colors: Optional[str] = ""
    features: List[str] = []
    pages: List[str] = []
    seo_keywords: List[str] = []
    constraints: Optional[str] = ""
    preferred_stack: List[str] = []  # ex.: ["React", "Tailwind", "Next.js"]
    deliverables: List[str] = [
        "mapa do site",
        "roteiro de conteúdo",
        "descrição de wireframe",
        "lista de componentes",
        "comportamento responsivo",
        "metas de SEO",
        "checklist de acessibilidade",
    ]
    output_format: Literal["markdown", "plain", "json"] = "markdown"

class PromptResponse(BaseModel):
    prompt: str
    llm: str

@app.get("/")
def read_root():
    return {"message": "Backend do Assistente de Prompts de IA"}

@app.get("/api/hello")
def hello():
    return {"message": "Olá da API do backend!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Em execução",
        "database": "❌ Indisponível",
        "database_url": None,
        "database_name": None,
        "connection_status": "Não conectado",
        "collections": []
    }
    try:
        from database import db  # type: ignore
        if db is not None:
            response["database"] = "✅ Disponível"
            response["database_url"] = "✅ Configurada"
            response["database_name"] = getattr(db, "name", "✅ Conectado")
            response["connection_status"] = "Conectado"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Conectado e funcionando"
            except Exception as e:  # pragma: no cover
                response["database"] = f"⚠️  Conectado, mas erro: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Disponível, porém não inicializado"
    except ImportError:
        response["database"] = "❌ Módulo de banco de dados não encontrado (opcional)"
    except Exception as e:  # pragma: no cover
        response["database"] = f"❌ Erro: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Definida" if _os.getenv("DATABASE_URL") else "❌ Não definida"
    response["database_name"] = "✅ Definido" if _os.getenv("DATABASE_NAME") else "❌ Não definido"
    return response

# --- Lógicas de geração de prompt ---
MODEL_STYLES = {
    "gpt-4o": {
        "system": "Você é um(a) arquiteto(a) sênior de produto + UX + frontend. Produza instruções precisas, concisas e prontas para implementação.",
        "notes": "Prefira listas objetivas e seções prontas para código."
    },
    "gpt-4.1": {
        "system": "Você é um(a) redator(a) técnico(a) e engenheiro(a) de UI meticuloso(a).",
        "notes": "Prefira listas estruturadas e critérios de aceite explícitos."
    },
    "claude-3.5": {
        "system": "Você é reflexivo(a) e ponderado(a). Explique trade-offs e proponha alternativas.",
        "notes": "Inclua checklists e seções de raciocínio."
    },
    "gemini-1.5": {
        "system": "Você é designer de produto multimodal + engenheiro(a).",
        "notes": "Se houver imagens, descreva-as. Mantenha passos explícitos."
    },
    "llama-3.1": {
        "system": "Você é um(a) arquiteto(a) web open-source. Seja explícito(a) e determinístico(a).",
        "notes": "Evite ambiguidades; inclua divisão clara de arquivos/componentes."
    },
    "mistral-large": {
        "system": "Você é um(a) tech lead pragmático(a) de frontend.",
        "notes": "Use instruções concisas com passos numerados."
    },
}


def bjoin(items: List[str]) -> str:
    return "\n".join([f"- {i}" for i in items]) if items else "- (nenhum)"


@app.post("/api/generate-prompt", response_model=PromptResponse)
def generate_prompt(req: PromptRequest):
    style = MODEL_STYLES.get(req.llm)
    if not style:
        raise HTTPException(status_code=400, detail="Modelo não suportado")

    features = bjoin(req.features)
    pages = bjoin(req.pages)
    keywords = bjoin(req.seo_keywords)
    stack = bjoin(req.preferred_stack)
    deliverables = bjoin(req.deliverables)

    header = f"Modelo: {req.llm}\nProjeto: {req.project_name}\nTipo: {req.site_type}\nTom: {req.tone}\n"

    core = f"""
[SISTEMA]
{style['system']}
Notas adicionais: {style['notes']}

[OBJETIVO]
Projete e descreva um site completo para "{req.project_name}".

[CONTEXTO]
Público-alvo: {req.target_audience or 'Público geral da web'}
Cores/tema da marca: {req.brand_colors or 'A definir'}
Restrições: {req.constraints or 'Nenhuma especificada'}
Stack preferida: \n{stack}

[TIPO DE SITE]
{req.site_type}

[FUNCIONALIDADES]
{features}

[PÁGINAS]
{pages}

[SEO]
Palavras-chave principais:\n{keywords}

[ENTREGÁVEIS]
Produza o seguinte, otimizando para o modelo selecionado:\n{deliverables}

[GUIA DE ESTILO]
- Voz e tom: {req.tone}
- Acessibilidade: WCAG 2.2 AA; inclua landmarks, contraste de cores e navegação por teclado.
- Desempenho: lazy-load de mídia, compressão de assets, mínimo de JavaScript quando possível.

[SAÍDA]
Formato de saída preferido: {req.output_format}
Forneça seções com títulos claros. Inclua exemplos de copy, nomes de componentes e critérios de aceite para cada página. Quando relevante, forneça exemplos de utilitários do Tailwind.
""".strip()

    return PromptResponse(prompt=f"{header}\n\n{core}", llm=req.llm)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
