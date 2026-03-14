"""
Point d'entrée du microservice LLM pour le chatbot médical Georges.
API FastAPI exposant les endpoints de génération, résumé, analyse et extraction.
"""

import time
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import LLMConfig
from models.schemas import (
    GenerateRequest,
    GenerateResponse,
    SummarizeRequest,
    SummarizeResponse,
    AnalyzeSymptomsRequest,
    AnalyzeSymptomsResponse,
    ExtractEntitiesRequest,
    ExtractEntitiesResponse,
    HealthResponse,
)
from services.base_llm import BaseLLMService

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Service LLM actif (initialisé au démarrage)
llm_service: BaseLLMService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application : initialisation du service LLM."""
    global llm_service

    if LLMConfig.GEMINI_API_KEY:
        try:
            from services.gemini_service import GeminiLLMService

            llm_service = GeminiLLMService(
                api_key=LLMConfig.GEMINI_API_KEY,
                model_name=LLMConfig.DEFAULT_MODEL,
            )
            logger.info(
                f"Service Gemini initialisé avec le modèle : {LLMConfig.DEFAULT_MODEL}"
            )
        except Exception as e:
            logger.warning(
                f"Impossible d'initialiser Gemini ({e}), basculement vers le service factice."
            )
            from services.dummy_service import DummyLLMService

            llm_service = DummyLLMService()
    else:
        logger.info(
            "Aucune clé API Gemini détectée. Utilisation du service factice (DummyLLMService)."
        )
        from services.dummy_service import DummyLLMService

        llm_service = DummyLLMService()

    yield

    # Nettoyage au shutdown (si nécessaire)
    logger.info("Arrêt du microservice LLM Georges.")


# Création de l'application FastAPI
app = FastAPI(
    title="Georges LLM Service",
    description="Microservice LLM pour le chatbot médical Georges de l'HEGP",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Génère une réponse médicale à partir du message et de l'historique.
    Mesure la latence de la requête.
    """
    try:
        start_time = time.time()

        model_name = request.model_name or LLMConfig.DEFAULT_MODEL

        response_text = llm_service.generate(
            message=request.message,
            conversation_history=request.conversation_history,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        latency_ms = (time.time() - start_time) * 1000

        return GenerateResponse(
            response=response_text,
            model_used=model_name,
            latency_ms=round(latency_ms, 2),
        )

    except Exception as e:
        logger.error(f"Erreur lors de la génération : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération de la réponse : {str(e)}",
        )


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """Génère un résumé structuré de la conversation patient."""
    try:
        result = llm_service.summarize(messages=request.messages)

        return SummarizeResponse(
            summary=result.get("summary", ""),
            key_points=result.get("key_points", []),
            medical_entities=result.get("medical_entities", {}),
        )

    except Exception as e:
        logger.error(f"Erreur lors du résumé : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du résumé : {str(e)}",
        )


@app.post("/api/analyze-symptoms", response_model=AnalyzeSymptomsResponse)
async def analyze_symptoms(request: AnalyzeSymptomsRequest):
    """Analyse les symptômes du patient et retourne une évaluation."""
    try:
        result = llm_service.analyze_symptoms(symptoms=request.symptoms)

        return AnalyzeSymptomsResponse(
            analysis=result.get("analysis", ""),
            severity=result.get("severity", "unknown"),
            urgency=result.get("urgency", False),
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des symptômes : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse des symptômes : {str(e)}",
        )


@app.post("/api/extract-entities", response_model=ExtractEntitiesResponse)
async def extract_entities(request: ExtractEntitiesRequest):
    """Extrait les entités médicales d'un texte libre."""
    try:
        entities = llm_service.extract_entities(text=request.text)

        return ExtractEntitiesResponse(entities=entities)

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction d'entités : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'extraction des entités : {str(e)}",
        )


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Vérifie l'état de santé du service et retourne les informations du modèle."""
    model_name = getattr(llm_service, "model_name", "unknown")
    return HealthResponse(
        status="ok",
        model=model_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/models")
async def list_models():
    """Liste les modèles LLM disponibles."""
    models = [
        {
            "id": "gemini-pro",
            "name": "Gemini Pro",
            "provider": "Google",
            "description": "Modèle Gemini Pro pour la génération de texte",
        },
        {
            "id": "gemini-pro-vision",
            "name": "Gemini Pro Vision",
            "provider": "Google",
            "description": "Modèle Gemini Pro avec capacités visuelles",
        },
        {
            "id": "dummy-model",
            "name": "Modèle Factice",
            "provider": "Local",
            "description": "Modèle factice pour les tests sans clé API",
        },
    ]

    # Identifier le modèle actuellement actif
    active_model = getattr(llm_service, "model_name", "unknown")

    return {
        "models": models,
        "active_model": active_model,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=LLMConfig.HOST,
        port=LLMConfig.PORT,
        reload=True,
    )
