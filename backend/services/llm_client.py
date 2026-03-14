"""
Client LLM pour Georges Medical Chatbot.
Communique avec le microservice FastAPI pour la génération de réponses.
"""

import logging
import requests

logger = logging.getLogger(__name__)


class LLMClient:
    """Client HTTP pour le microservice LLM FastAPI."""

    def __init__(self, base_url):
        """
        Initialise le client LLM.

        Args:
            base_url: URL de base du microservice (ex: http://localhost:8000)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = 60  # Timeout en secondes pour les requêtes LLM
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def generate_response(self, message, conversation_history=None,
                          model_name=None, project_id=None):
        """
        Génère une réponse via le microservice LLM.

        Args:
            message: Message de l'utilisateur
            conversation_history: Historique de la conversation
            model_name: Nom du modèle à utiliser
            project_id: Identifiant du projet (pour configuration spécifique)

        Returns:
            str: Réponse générée par le LLM
        """
        try:
            payload = {
                'message': message,
                'conversation_history': conversation_history or [],
            }
            if model_name:
                payload['model_name'] = model_name
            if project_id:
                payload['project_id'] = project_id

            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            return data.get('response', data.get('text', ''))

        except requests.exceptions.Timeout:
            logger.error("Timeout lors de la génération de réponse LLM")
            return "Désolé, le service de génération est temporairement lent. Veuillez réessayer."
        except requests.exceptions.ConnectionError:
            logger.error("Impossible de se connecter au service LLM")
            return "Désolé, le service de génération est temporairement indisponible."
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP du service LLM: {e}")
            return "Une erreur est survenue lors de la génération de la réponse."
        except Exception as e:
            logger.error(f"Erreur inattendue du client LLM: {e}")
            return "Une erreur inattendue est survenue."

    def generate_summary(self, messages):
        """
        Génère un résumé à partir d'une liste de messages.

        Args:
            messages: Liste de messages de conversation

        Returns:
            str: Résumé généré
        """
        try:
            payload = {'messages': messages}

            response = self.session.post(
                f"{self.base_url}/api/summarize",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            return data.get('summary', '')

        except requests.exceptions.Timeout:
            logger.error("Timeout lors de la génération du résumé")
            return ''
        except requests.exceptions.ConnectionError:
            logger.error("Impossible de se connecter au service LLM pour le résumé")
            return ''
        except Exception as e:
            logger.error(f"Erreur de génération du résumé: {e}")
            return ''

    def analyze_symptoms(self, symptoms):
        """
        Analyse une liste de symptômes via le LLM.

        Args:
            symptoms: Liste de symptômes à analyser

        Returns:
            dict: Résultat de l'analyse (suggestions, urgence, etc.)
        """
        try:
            payload = {'symptoms': symptoms}

            response = self.session.post(
                f"{self.base_url}/api/analyze-symptoms",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            logger.error("Timeout lors de l'analyse des symptômes")
            return {'error': 'Timeout', 'analysis': None}
        except requests.exceptions.ConnectionError:
            logger.error("Impossible de se connecter au service LLM pour l'analyse")
            return {'error': 'Service indisponible', 'analysis': None}
        except Exception as e:
            logger.error(f"Erreur d'analyse des symptômes: {e}")
            return {'error': str(e), 'analysis': None}

    def extract_medical_entities(self, text):
        """
        Extrait les entités médicales d'un texte.

        Args:
            text: Texte à analyser

        Returns:
            dict: Entités médicales extraites
        """
        try:
            payload = {'text': text}

            response = self.session.post(
                f"{self.base_url}/api/extract-entities",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            logger.error("Timeout lors de l'extraction d'entités médicales")
            return {'error': 'Timeout', 'entities': {}}
        except requests.exceptions.ConnectionError:
            logger.error("Impossible de se connecter au service LLM pour l'extraction")
            return {'error': 'Service indisponible', 'entities': {}}
        except Exception as e:
            logger.error(f"Erreur d'extraction d'entités: {e}")
            return {'error': str(e), 'entities': {}}

    def health_check(self):
        """
        Vérifie l'état de santé du microservice LLM.

        Returns:
            dict: État de santé du service
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error("Timeout lors du health check LLM")
            return {'status': 'unhealthy', 'error': 'Timeout'}
        except requests.exceptions.ConnectionError:
            logger.error("Impossible de se connecter au service LLM")
            return {'status': 'unhealthy', 'error': 'Connection refused'}
        except Exception as e:
            logger.error(f"Erreur de health check LLM: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
