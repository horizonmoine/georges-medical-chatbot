"""
Service LLM factice pour les tests et le développement sans clé API.
Retourne des réponses prédéfinies en français pour simuler le comportement du LLM.
"""

import logging
from typing import List, Dict, Optional

from services.base_llm import BaseLLMService

logger = logging.getLogger(__name__)


class DummyLLMService(BaseLLMService):
    """Service LLM factice pour le développement et les tests sans API Gemini."""

    def __init__(self):
        """Initialise le service factice."""
        self.model_name = "dummy-model"
        logger.info("Service LLM factice initialisé (mode test, pas de clé API)")

    def generate(
        self,
        message: str,
        conversation_history: list = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Retourne une réponse médicale générique en français.

        Args:
            message: Message de l'utilisateur.
            conversation_history: Historique (ignoré en mode factice).
            temperature: Paramètre de température (ignoré).
            max_tokens: Nombre max de tokens (ignoré).

        Returns:
            Réponse générique en français.
        """
        return (
            "Bonjour, je suis Georges, l'assistant médical virtuel de l'Hôpital "
            "Européen Georges-Pompidou. Je fonctionne actuellement en mode test. "
            f"Vous avez dit : \"{message}\". "
            "En conditions normales, je vous fournirais une réponse médicale "
            "personnalisée. Pour toute urgence, veuillez appeler le 15 (SAMU) "
            "ou vous rendre aux urgences les plus proches."
        )

    def summarize(self, messages: list) -> dict:
        """
        Retourne un résumé patient modèle.

        Args:
            messages: Liste des messages de la conversation.

        Returns:
            Résumé structuré modèle.
        """
        num_messages = len(messages) if messages else 0
        return {
            "summary": (
                f"Résumé de la conversation ({num_messages} messages). "
                "Le patient a échangé avec l'assistant médical Georges. "
                "Ce résumé est généré en mode test."
            ),
            "key_points": [
                "Conversation en mode test",
                f"Nombre de messages échangés : {num_messages}",
                "Aucune analyse médicale réelle effectuée",
            ],
            "medical_entities": {
                "symptoms": [],
                "treatments": [],
                "conditions": [],
                "allergies": [],
            },
        }

    def analyze_symptoms(self, symptoms: list) -> dict:
        """
        Retourne une analyse de symptômes modèle.

        Args:
            symptoms: Liste des symptômes.

        Returns:
            Analyse structurée modèle.
        """
        symptoms_text = ", ".join(symptoms) if symptoms else "aucun symptôme fourni"
        return {
            "analysis": (
                f"Analyse factice des symptômes suivants : {symptoms_text}. "
                "En mode test, aucune analyse médicale réelle n'est effectuée. "
                "Veuillez consulter un professionnel de santé pour un avis médical. "
                "En cas d'urgence, appelez le 15 (SAMU) ou le 112."
            ),
            "severity": "unknown",
            "urgency": False,
        }

    def extract_entities(self, text: str) -> dict:
        """
        Retourne un dictionnaire d'entités vide (mode test).

        Args:
            text: Texte à analyser.

        Returns:
            Dictionnaire d'entités médicales vide.
        """
        return {
            "symptoms": [],
            "treatments": [],
            "history": [],
            "allergies": [],
        }
