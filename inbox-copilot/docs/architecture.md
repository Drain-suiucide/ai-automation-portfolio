# Architecture

```mermaid
flowchart TB
    subgraph Client["Frontend (Next.js)"]
        UI[Inbox UI]
        Detail[Email Detail + Draft Panel]
        Audit[Audit Log]
        Dash[Dashboard]
    end

    subgraph API["Backend (FastAPI)"]
        Router[API Routers]
        Pipeline[Pipeline Service]
        Classifier[Classifier]
        Extractor[Extractor]
        Prioritizer[Prioritizer]
        Drafter[Drafter]
        AuditLog[Audit Service]
    end

    subgraph LLM["LLM Gateway (LiteLLM)"]
        OR[OpenRouter / Nemotron]
        OL[Ollama / Llama 3.2]
    end

    DB[(PostgreSQL\n+ pgvector)]
    Redis[(Redis)]

    UI --> Router
    Detail --> Router
    Audit --> Router
    Dash --> Router

    Router --> Pipeline
    Router --> Drafter
    Router --> AuditLog

    Pipeline --> Classifier
    Pipeline --> Extractor
    Pipeline --> Prioritizer

    Classifier --> OR
    Extractor --> OR
    Prioritizer --> OR
    Drafter --> OR

    OR -. fallback .-> OL

    Pipeline --> DB
    Drafter --> DB
    AuditLog --> DB
    Router --> DB