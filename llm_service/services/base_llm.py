"""
Classe abstraite définissant l'interface commune pour tous les services LLM.
Chaque implémentation (Gemini, Dummy, etc.) doit hériter de cette classe.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseLLMService(ABC):
    @abstractmethod
    def generate(
        self,
        message: str,
        conversation_history: list = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Génère une réponse à partir d'un message et de l'historique de conversation."""
        pass

    @abstractmethod
    def summarize(self, messages: list) -> dict:
        """Produit un résumé structuré d'une conversation patient."""
        pass

    @abstractmethod
    def analyze_symptoms(self, symptoms: list) -> dict:
        """Analyse une liste de symptômes et retourne gravité, conditions possibles, recommandations."""
        pass

    @abstractmethod
    def extract_entities(self, text: str) -> dict:
        """Extrait les entités médicales (symptômes, traitements, antécédents, allergies) d'un texte."""
        pass
