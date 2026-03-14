"""
Service d'envoi d'emails pour Georges Medical Chatbot.
Utilise Mailgun pour l'envoi transactionnel.
"""

import logging
import requests

logger = logging.getLogger(__name__)


class EmailService:
    """Service d'envoi d'emails via Mailgun."""

    def __init__(self, api_key, domain, sender_name='Georges Medical Chatbot'):
        """
        Initialise le service email.

        Args:
            api_key: Clé API Mailgun
            domain: Domaine Mailgun
            sender_name: Nom de l'expéditeur
        """
        self.api_key = api_key
        self.domain = domain
        self.sender_name = sender_name
        self.base_url = f"https://api.mailgun.net/v3/{domain}"
        self.enabled = bool(api_key and domain)

        if not self.enabled:
            logger.warning("Service email désactivé: MAILGUN_API_KEY ou MAILGUN_DOMAIN non configuré")

    def send_email(self, to, subject, html_body, text_body=None):
        """
        Envoie un email.

        Args:
            to: Adresse email du destinataire
            subject: Sujet de l'email
            html_body: Corps HTML de l'email
            text_body: Corps texte brut (optionnel)

        Returns:
            bool: True si l'envoi a réussi
        """
        if not self.enabled:
            logger.info(f"Email simulé vers {to}: {subject}")
            return True

        try:
            data = {
                'from': f"{self.sender_name} <noreply@{self.domain}>",
                'to': [to],
                'subject': subject,
                'html': html_body
            }
            if text_body:
                data['text'] = text_body

            response = requests.post(
                f"{self.base_url}/messages",
                auth=('api', self.api_key),
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"Email envoyé avec succès à {to}")
                return True
            else:
                logger.error(
                    f"Erreur d'envoi email: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.error(f"Timeout lors de l'envoi email à {to}")
            return False
        except Exception as e:
            logger.error(f"Erreur d'envoi email: {e}")
            return False

    def send_confirmation_email(self, to, token, frontend_url):
        """
        Envoie un email de confirmation d'inscription.

        Args:
            to: Adresse email du destinataire
            token: Token de confirmation
            frontend_url: URL de base du frontend
        """
        confirmation_url = f"{frontend_url}/confirm-email?token={token}"
        subject = "Confirmez votre inscription - Georges Medical Chatbot"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">Bienvenue sur Georges Medical Chatbot</h2>
            <p>Merci de votre inscription. Veuillez confirmer votre adresse email
            en cliquant sur le lien ci-dessous:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{confirmation_url}"
                   style="background-color: #3498db; color: white; padding: 12px 30px;
                          text-decoration: none; border-radius: 5px; font-size: 16px;">
                    Confirmer mon email
                </a>
            </p>
            <p style="color: #7f8c8d; font-size: 12px;">
                Si vous n'avez pas créé de compte, vous pouvez ignorer cet email.
                Ce lien expire dans 24 heures.
            </p>
        </body>
        </html>
        """
        text_body = (
            f"Bienvenue sur Georges Medical Chatbot.\n\n"
            f"Confirmez votre email en visitant: {confirmation_url}\n\n"
            f"Ce lien expire dans 24 heures."
        )
        return self.send_email(to, subject, html_body, text_body)

    def send_password_reset_email(self, to, token, frontend_url):
        """
        Envoie un email de réinitialisation de mot de passe.

        Args:
            to: Adresse email du destinataire
            token: Token de réinitialisation
            frontend_url: URL de base du frontend
        """
        reset_url = f"{frontend_url}/reset-password?token={token}"
        subject = "Réinitialisation de mot de passe - Georges Medical Chatbot"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">Réinitialisation de mot de passe</h2>
            <p>Vous avez demandé une réinitialisation de mot de passe.
            Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}"
                   style="background-color: #e74c3c; color: white; padding: 12px 30px;
                          text-decoration: none; border-radius: 5px; font-size: 16px;">
                    Réinitialiser mon mot de passe
                </a>
            </p>
            <p style="color: #7f8c8d; font-size: 12px;">
                Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
                Ce lien expire dans 1 heure.
            </p>
        </body>
        </html>
        """
        text_body = (
            f"Réinitialisation de mot de passe.\n\n"
            f"Visitez: {reset_url}\n\n"
            f"Ce lien expire dans 1 heure."
        )
        return self.send_email(to, subject, html_body, text_body)
