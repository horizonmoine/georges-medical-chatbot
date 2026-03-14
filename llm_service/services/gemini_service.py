"""
Service LLM utilisant l'API Google Gemini.
Fournit les fonctionnalités de génération, résumé, analyse de symptômes
et extraction d'entités médicales pour l'hôpital HEGP.
"""

import json
import logging
from typing import List, Dict, Optional

import google.generativeai as genai

from services.base_llm import BaseLLMService

logger = logging.getLogger(__name__)

# Contexte médical spécifique à l'HEGP (Hôpital Européen Georges-Pompidou)
MEDICAL_CONTEXT = """Tu es Georges, un assistant médical virtuel de l'Hôpital Européen Georges-Pompidou (HEGP) à Paris.
Tu assistes les patients et le personnel soignant en fournissant des informations médicales fiables.

Règles importantes :
- Réponds toujours en français sauf indication contraire.
- Ne pose jamais de diagnostic définitif. Oriente toujours le patient vers un professionnel de santé.
- Sois empathique, clair et professionnel dans tes réponses.
- En cas d'urgence détectée, conseille immédiatement d'appeler le 15 (SAMU) ou le 112.
- Respecte la confidentialité des données patients (RGPD / HDS).
- Tu peux fournir des informations générales sur les pathologies, traitements et procédures.
- Cite tes sources quand c'est possible (HAS, OMS, sociétés savantes).
"""


class GeminiLLMService(BaseLLMService):
    """Service LLM basé sur Google Gemini pour le chatbot médical Georges."""

    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        """
        Initialise le service Gemini.

        Args:
            api_key: Clé API Google Generative AI.
            model_name: Nom du modèle Gemini à utiliser.
        """
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Service Gemini initialisé avec le modèle : {model_name}")

    def generate(
        self,
        message: str,
        conversation_history: list = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Génère une réponse à partir du message et de l'historique.

        Args:
            message: Message de l'utilisateur.
            conversation_history: Historique des échanges précédents.
            temperature: Contrôle la créativité de la réponse.
            max_tokens: Nombre maximum de tokens dans la réponse.

        Returns:
            Texte de la réponse générée.
        """
        try:
            # Construction du prompt complet avec contexte médical et historique
            full_prompt = MEDICAL_CONTEXT + "\n\n"

            if conversation_history:
                full_prompt += "Historique de la conversation :\n"
                for entry in conversation_history:
                    role = entry.get("role", "user")
                    content = entry.get("content", "")
                    if role == "user":
                        full_prompt += f"Patient : {content}\n"
                    else:
                        full_prompt += f"Georges : {content}\n"
                full_prompt += "\n"

            full_prompt += f"Patient : {message}\nGeorges :"

            # Configuration de la génération
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )

            return response.text

        except Exception as e:
            logger.error(f"Erreur lors de la génération Gemini : {e}")
            raise RuntimeError(f"Erreur de génération : {str(e)}")

    def summarize(self, messages: list) -> dict:
        """
        Génère un résumé structuré de la conversation patient.

        Args:
            messages: Liste des messages de la conversation.

        Returns:
            Dictionnaire avec summary, key_points et medical_entities.
        """
        try:
            # Formatage des messages pour le résumé
            conversation_text = "\n".join(
                [
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in messages
                ]
            )

            prompt = f"""{MEDICAL_CONTEXT}

Analyse la conversation suivante entre un patient et l'assistant médical Georges.
Produis un résumé structuré au format JSON avec les champs suivants :
- "summary" : résumé concis de la conversation (2-3 phrases)
- "key_points" : liste des points clés identifiés
- "medical_entities" : dictionnaire avec les clés "symptoms", "treatments", "conditions", "allergies"

Conversation :
{conversation_text}

Réponds uniquement avec le JSON valide, sans commentaires."""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Tentative de parsing JSON de la réponse
            # Nettoyage des balises markdown éventuelles
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            try:
                parsed = json.loads(response_text)
                return {
                    "summary": parsed.get("summary", response_text),
                    "key_points": parsed.get("key_points", []),
                    "medical_entities": parsed.get("medical_entities", {}),
                }
            except json.JSONDecodeError:
                # Si le JSON n'est pas valide, retourner le texte brut comme résumé
                return {
                    "summary": response_text,
                    "key_points": [],
                    "medical_entities": {},
                }

        except Exception as e:
            logger.error(f"Erreur lors du résumé Gemini : {e}")
            raise RuntimeError(f"Erreur de résumé : {str(e)}")

    def analyze_symptoms(self, symptoms: list) -> dict:
        """
        Analyse une liste de symptômes et retourne une évaluation structurée.

        Args:
            symptoms: Liste de symptômes rapportés par le patient.

        Returns:
            Dictionnaire avec analysis, severity et urgency.
        """
        try:
            symptoms_text = ", ".join(symptoms)

            prompt = f"""{MEDICAL_CONTEXT}

Analyse les symptômes suivants rapportés par un patient :
{symptoms_text}

Produis une réponse au format JSON avec les champs :
- "analysis" : analyse détaillée des symptômes, conditions possibles et recommandations
- "severity" : niveau de gravité parmi ["low", "moderate", "high", "critical"]
- "urgency" : booléen indiquant si une consultation urgente est nécessaire

IMPORTANT : Ne pose pas de diagnostic définitif. Oriente vers un professionnel.
Réponds uniquement avec le JSON valide."""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Nettoyage des balises markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            try:
                parsed = json.loads(response_text)
                return {
                    "analysis": parsed.get("analysis", response_text),
                    "severity": parsed.get("severity", "unknown"),
                    "urgency": parsed.get("urgency", False),
                }
            except json.JSONDecodeError:
                return {
                    "analysis": response_text,
                    "severity": "unknown",
                    "urgency": False,
                }

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des symptômes Gemini : {e}")
            raise RuntimeError(f"Erreur d'analyse des symptômes : {str(e)}")

    def extract_entities(self, text: str) -> dict:
        """
        Extrait les entités médicales d'un texte libre.

        Args:
            text: Texte libre du patient ou du dossier médical.

        Returns:
            Dictionnaire des entités extraites.
        """
        try:
            prompt = f"""{MEDICAL_CONTEXT}

Extrait les entités médicales du texte suivant.
Produis une réponse au format JSON avec les clés :
- "symptoms" : liste des symptômes mentionnés
- "treatments" : liste des traitements ou médicaments mentionnés
- "history" : liste des antécédents médicaux mentionnés
- "allergies" : liste des allergies mentionnées

Texte :
{text}

Réponds uniquement avec le JSON valide."""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Nettoyage des balises markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            try:
                parsed = json.loads(response_text)
                return parsed
            except json.JSONDecodeError:
                return {
                    "symptoms": [],
                    "treatments": [],
                    "history": [],
                    "allergies": [],
                }

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'entités Gemini : {e}")
            raise RuntimeError(f"Erreur d'extraction d'entités : {str(e)}")
