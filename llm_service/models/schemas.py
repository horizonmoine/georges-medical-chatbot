"""
Schémas Pydantic v2 pour le microservice LLM Georges.
Définition des modèles de requêtes et réponses pour l'API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """Requête de génération de texte via le LLM."""
    message: str
    conversation_history: list = []
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    project_id: Optional[str] = None


class GenerateResponse(BaseModel):
    """Réponse de génération de texte."""
    response: str
    model_used: str
    latency_ms: float


class SummarizeRequest(BaseModel):
    """Requête de résumé de conversation patient."""
    messages: list
    language: str = "fr"


class SummarizeResponse(BaseModel):
    """Réponse contenant le résumé structuré du patient."""
    summary: str
    key_points: list = []
    medical_entities: dict = {}


class AnalyzeSymptomsRequest(BaseModel):
    """Requête d'analyse de symptômes."""
    symptoms: list[str]


class AnalyzeSymptomsResponse(BaseModel):
    """Réponse d'analyse de symptômes avec niveau de gravité."""
    analysis: str
    severity: str = "unknown"
    urgency: bool = False


class ExtractEntitiesRequest(BaseModel):
    """Requête d'extraction d'entités médicales depuis un texte libre."""
    text: str


class ExtractEntitiesResponse(BaseModel):
    """Réponse contenant les entités médicales extraites."""
    entities: dict


class HealthResponse(BaseModel):
    """Réponse du point de terminaison de santé du service."""
    status: str
    model: str
    timestamp: str
