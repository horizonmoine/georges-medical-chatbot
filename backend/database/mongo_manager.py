"""
Gestionnaire MongoDB pour Georges Medical Chatbot.
Interface identique à ElasticDataManager pour interchangeabilité.
"""

import logging
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from backend.core.security import SecurityManager
from backend.core.audit import AuditLogger

logger = logging.getLogger(__name__)


class MongoDataManager:
    """Gestionnaire de données MongoDB avec chiffrement intégré."""

    def __init__(self, uri, db_name, encryption_key):
        """
        Initialise la connexion MongoDB.

        Args:
            uri: URI de connexion MongoDB
            db_name: Nom de la base de données
            encryption_key: Clé de chiffrement pour les données sensibles
        """
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.security = SecurityManager(encryption_key)
        self.audit = AuditLogger()
        logger.info(f"Connexion MongoDB initialisée: {db_name}")

    def initialize_collections(self):
        """Crée les collections et les index nécessaires."""
        try:
            # Users - email unique
            self.db.users.create_index([('email', ASCENDING)], unique=True)
            self.db.users.create_index([('userId', ASCENDING)], unique=True)

            # Conversations
            self.db.conversations.create_index([('conversationId', ASCENDING)], unique=True)
            self.db.conversations.create_index([('userId', ASCENDING)])
            self.db.conversations.create_index([('created_at', DESCENDING)])

            # Projects - slug unique
            self.db.projects.create_index([('slug', ASCENDING)], unique=True)
            self.db.projects.create_index([('projectId', ASCENDING)], unique=True)

            # Consents
            self.db.consents.create_index([('userId', ASCENDING)])
            self.db.consents.create_index([('projectId', ASCENDING)])

            # Audit logs
            self.db.audit_logs.create_index([('user_id', ASCENDING)])
            self.db.audit_logs.create_index([('timestamp', DESCENDING)])

            # Analytics
            self.db.analytics.create_index([('event_type', ASCENDING)])
            self.db.analytics.create_index([('timestamp', DESCENDING)])

            logger.info("Collections et index MongoDB initialisés")
        except Exception as e:
            logger.error(f"Erreur d'initialisation des collections: {e}")
            raise

    # ==================== USERS ====================

    def create_user(self, email, password, nom, prenom, date_naissance,
                    role='patient', confirmation_token=None):
        """Crée un nouvel utilisateur avec données chiffrées."""
        try:
            password_hash = self.security.hash_password(password)
            nom_encrypted = self.security.encrypt_data(nom)
            prenom_encrypted = self.security.encrypt_data(prenom)
            date_naissance_encrypted = self.security.encrypt_data(date_naissance)

            from backend.models.user import create_user_doc
            user_doc = create_user_doc(
                email=email,
                password_hash=password_hash,
                nom_encrypted=nom_encrypted,
                prenom_encrypted=prenom_encrypted,
                date_naissance_encrypted=date_naissance_encrypted,
                role=role,
                confirmation_token=confirmation_token
            )

            self.db.users.insert_one(user_doc)
            self.audit.log_action(
                user_id=user_doc['userId'],
                action='create',
                resource_type='user',
                resource_id=user_doc['userId'],
                status='success'
            )
            logger.info(f"Utilisateur créé: {user_doc['userId']}")
            return user_doc

        except DuplicateKeyError:
            logger.warning(f"Email déjà utilisé: {email}")
            return None
        except Exception as e:
            logger.error(f"Erreur de création utilisateur: {e}")
            raise

    def get_user_by_email(self, email):
        """Récupère un utilisateur par email avec déchiffrement."""
        try:
            user = self.db.users.find_one({'email': email})
            if user:
                user = self._decrypt_user_fields(user)
            return user
        except Exception as e:
            logger.error(f"Erreur de récupération utilisateur par email: {e}")
            return None

    def get_user_by_id(self, user_id):
        """Récupère un utilisateur par userId avec déchiffrement."""
        try:
            user = self.db.users.find_one({'userId': user_id})
            if user:
                user = self._decrypt_user_fields(user)
            return user
        except Exception as e:
            logger.error(f"Erreur de récupération utilisateur par ID: {e}")
            return None

    def update_user(self, user_id, updates):
        """Met à jour un utilisateur."""
        try:
            # Chiffrer les champs sensibles si présents
            encrypted_fields = ['nom', 'prenom', 'date_naissance']
            for field in encrypted_fields:
                if field in updates:
                    updates[field] = self.security.encrypt_data(updates[field])

            updates['updated_at'] = datetime.now(timezone.utc).isoformat()

            result = self.db.users.update_one(
                {'userId': user_id},
                {'$set': updates}
            )

            self.audit.log_action(
                user_id=user_id,
                action='update',
                resource_type='user',
                resource_id=user_id,
                status='success'
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur de mise à jour utilisateur: {e}")
            return False

    def verify_user_password(self, email, password):
        """Vérifie le mot de passe d'un utilisateur."""
        try:
            user = self.db.users.find_one({'email': email})
            if not user:
                return False, None

            if self.security.verify_password(password, user['password_hash']):
                user = self._decrypt_user_fields(user)
                return True, user
            return False, None
        except Exception as e:
            logger.error(f"Erreur de vérification mot de passe: {e}")
            return False, None

    def _decrypt_user_fields(self, user):
        """Déchiffre les champs sensibles d'un utilisateur."""
        try:
            if user.get('nom'):
                user['nom_decrypted'] = self.security.decrypt_data(user['nom'])
            if user.get('prenom'):
                user['prenom_decrypted'] = self.security.decrypt_data(user['prenom'])
            if user.get('date_naissance'):
                user['date_naissance_decrypted'] = self.security.decrypt_data(user['date_naissance'])
        except Exception as e:
            logger.error(f"Erreur de déchiffrement des champs utilisateur: {e}")
        return user

    # ==================== CONVERSATIONS ====================

    def create_conversation(self, user_id, project_id=None):
        """Crée une nouvelle conversation."""
        try:
            from backend.models.conversation import create_conversation_doc
            conv_doc = create_conversation_doc(user_id, project_id)
            self.db.conversations.insert_one(conv_doc)

            self.audit.log_action(
                user_id=user_id,
                action='create',
                resource_type='conversation',
                resource_id=conv_doc['conversationId'],
                status='success'
            )
            logger.info(f"Conversation créée: {conv_doc['conversationId']}")
            return conv_doc
        except Exception as e:
            logger.error(f"Erreur de création conversation: {e}")
            raise

    def add_message_to_conversation(self, conversation_id, role, content,
                                    metadata=None):
        """Ajoute un message chiffré à une conversation."""
        try:
            from backend.models.conversation import create_message_doc
            content_encrypted = self.security.encrypt_data(content)
            message_doc = create_message_doc(role, content_encrypted, metadata)

            self.db.conversations.update_one(
                {'conversationId': conversation_id},
                {
                    '$push': {'messages': message_doc},
                    '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}
                }
            )
            return message_doc
        except Exception as e:
            logger.error(f"Erreur d'ajout de message: {e}")
            raise

    def get_conversation(self, conversation_id, decrypt=True):
        """Récupère une conversation avec déchiffrement optionnel des messages."""
        try:
            conv = self.db.conversations.find_one(
                {'conversationId': conversation_id}
            )
            if conv and decrypt:
                conv = self._decrypt_conversation_messages(conv)
            return conv
        except Exception as e:
            logger.error(f"Erreur de récupération conversation: {e}")
            return None

    def get_user_conversations(self, user_id, limit=50, offset=0):
        """Récupère les conversations d'un utilisateur."""
        try:
            cursor = self.db.conversations.find(
                {'userId': user_id}
            ).sort('updated_at', DESCENDING).skip(offset).limit(limit)

            conversations = []
            for conv in cursor:
                # Ne pas déchiffrer tous les messages pour la liste
                conv['message_count'] = len(conv.get('messages', []))
                # Garder seulement le dernier message déchiffré
                if conv.get('messages'):
                    last_msg = conv['messages'][-1]
                    try:
                        last_msg['content_decrypted'] = self.security.decrypt_data(
                            last_msg['content']
                        )
                    except Exception:
                        last_msg['content_decrypted'] = '[Contenu indisponible]'
                    conv['last_message'] = last_msg
                conv.pop('messages', None)
                conversations.append(conv)

            total = self.db.conversations.count_documents({'userId': user_id})
            return conversations, total
        except Exception as e:
            logger.error(f"Erreur de récupération des conversations: {e}")
            return [], 0

    def delete_conversation(self, conversation_id, user_id):
        """Supprime une conversation."""
        try:
            result = self.db.conversations.delete_one({
                'conversationId': conversation_id,
                'userId': user_id
            })

            if result.deleted_count > 0:
                self.audit.log_action(
                    user_id=user_id,
                    action='delete',
                    resource_type='conversation',
                    resource_id=conversation_id,
                    status='success'
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur de suppression conversation: {e}")
            return False

    def _decrypt_conversation_messages(self, conversation):
        """Déchiffre tous les messages d'une conversation."""
        try:
            for msg in conversation.get('messages', []):
                try:
                    msg['content_decrypted'] = self.security.decrypt_data(
                        msg['content']
                    )
                except Exception:
                    msg['content_decrypted'] = '[Contenu indisponible]'
        except Exception as e:
            logger.error(f"Erreur de déchiffrement des messages: {e}")
        return conversation

    # ==================== CONSENTS ====================

    def add_user_consent(self, user_id, project_id, consent_type, granted,
                         ip_address):
        """Enregistre un consentement utilisateur."""
        try:
            from backend.models.consent import create_consent_doc
            consent_doc = create_consent_doc(
                user_id, project_id, consent_type, granted, ip_address
            )
            self.db.consents.insert_one(consent_doc)

            # Mettre à jour la liste de consentements de l'utilisateur
            self.db.users.update_one(
                {'userId': user_id},
                {'$push': {'consents': {
                    'consent_type': consent_type,
                    'granted': granted,
                    'timestamp': consent_doc['timestamp']
                }}}
            )

            self.audit.log_action(
                user_id=user_id,
                action='consent',
                resource_type='consent',
                resource_id=consent_doc['consentId'],
                status='success',
                details={'consent_type': consent_type, 'granted': granted}
            )
            return consent_doc
        except Exception as e:
            logger.error(f"Erreur d'enregistrement du consentement: {e}")
            raise

    def check_user_consent(self, user_id, consent_type, project_id=None):
        """Vérifie si un utilisateur a donné un consentement spécifique."""
        try:
            query = {
                'userId': user_id,
                'consent_type': consent_type,
                'granted': True,
                'revoked': False
            }
            if project_id:
                query['projectId'] = project_id

            consent = self.db.consents.find_one(
                query,
                sort=[('timestamp', DESCENDING)]
            )
            return consent is not None
        except Exception as e:
            logger.error(f"Erreur de vérification du consentement: {e}")
            return False

    # ==================== PROJECTS ====================

    def create_project(self, name, description, slug, created_by,
                       model_config=None, inclusion_criteria=None):
        """Crée un nouveau projet de recherche."""
        try:
            from backend.models.project import create_project_doc
            project_doc = create_project_doc(
                name, description, slug, created_by,
                model_config, inclusion_criteria
            )
            self.db.projects.insert_one(project_doc)

            self.audit.log_action(
                user_id=created_by,
                action='create',
                resource_type='project',
                resource_id=project_doc['projectId'],
                status='success'
            )
            logger.info(f"Projet créé: {project_doc['projectId']}")
            return project_doc

        except DuplicateKeyError:
            logger.warning(f"Slug de projet déjà utilisé: {slug}")
            return None
        except Exception as e:
            logger.error(f"Erreur de création projet: {e}")
            raise

    def get_project_by_slug(self, slug):
        """Récupère un projet par son slug."""
        try:
            return self.db.projects.find_one({'slug': slug})
        except Exception as e:
            logger.error(f"Erreur de récupération projet par slug: {e}")
            return None

    def get_project_by_id(self, project_id):
        """Récupère un projet par son projectId."""
        try:
            return self.db.projects.find_one({'projectId': project_id})
        except Exception as e:
            logger.error(f"Erreur de récupération projet par ID: {e}")
            return None

    def get_all_projects(self, status=None):
        """Récupère tous les projets, optionnellement filtrés par statut."""
        try:
            query = {}
            if status:
                query['status'] = status
            cursor = self.db.projects.find(query).sort('created_at', DESCENDING)
            return list(cursor)
        except Exception as e:
            logger.error(f"Erreur de récupération des projets: {e}")
            return []

    def update_project(self, project_id, updates):
        """Met à jour un projet."""
        try:
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            result = self.db.projects.update_one(
                {'projectId': project_id},
                {'$set': updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur de mise à jour projet: {e}")
            return False

    def add_access_request(self, project_id, user_id, message=''):
        """Ajoute une demande d'accès à un projet."""
        try:
            request_doc = {
                'requestId': str(uuid4()),
                'userId': user_id,
                'message': message,
                'status': 'pending',
                'requested_at': datetime.now(timezone.utc).isoformat(),
                'reviewed_at': None
            }
            self.db.projects.update_one(
                {'projectId': project_id},
                {'$push': {'access_requests': request_doc}}
            )

            self.audit.log_action(
                user_id=user_id,
                action='request_access',
                resource_type='project',
                resource_id=project_id,
                status='success'
            )
            return request_doc
        except Exception as e:
            logger.error(f"Erreur d'ajout demande d'accès: {e}")
            raise

    def approve_access_request(self, project_id, request_id, approved_by):
        """Approuve une demande d'accès à un projet."""
        try:
            # Mettre à jour le statut de la demande
            now = datetime.now(timezone.utc).isoformat()
            self.db.projects.update_one(
                {
                    'projectId': project_id,
                    'access_requests.requestId': request_id
                },
                {
                    '$set': {
                        'access_requests.$.status': 'approved',
                        'access_requests.$.reviewed_at': now,
                        'access_requests.$.reviewed_by': approved_by
                    }
                }
            )

            # Récupérer le userId de la demande pour l'ajouter aux participants
            project = self.get_project_by_id(project_id)
            if project:
                for req in project.get('access_requests', []):
                    if req['requestId'] == request_id:
                        self.db.projects.update_one(
                            {'projectId': project_id},
                            {'$addToSet': {'participants': req['userId']}}
                        )
                        break

            self.audit.log_action(
                user_id=approved_by,
                action='approve_access',
                resource_type='project',
                resource_id=project_id,
                status='success',
                details={'request_id': request_id}
            )
            return True
        except Exception as e:
            logger.error(f"Erreur d'approbation demande d'accès: {e}")
            return False

    # ==================== ANALYTICS ====================

    def record_analytics_event(self, event_type, user_id=None, data=None):
        """Enregistre un événement analytique."""
        try:
            event = {
                'eventId': str(uuid4()),
                'event_type': event_type,
                'user_id': user_id,
                'data': data or {},
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            self.db.analytics.insert_one(event)
            return event
        except Exception as e:
            logger.error(f"Erreur d'enregistrement analytics: {e}")
            return None

    def get_analytics_summary(self, days=30):
        """Récupère un résumé analytique des N derniers jours."""
        try:
            since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            total_users = self.db.users.count_documents({})
            active_users = self.db.users.count_documents({'is_active': True})
            total_conversations = self.db.conversations.count_documents({})
            total_projects = self.db.projects.count_documents({})

            # Conversations récentes
            recent_conversations = self.db.conversations.count_documents({
                'created_at': {'$gte': since}
            })

            # Événements récents par type
            pipeline = [
                {'$match': {'timestamp': {'$gte': since}}},
                {'$group': {'_id': '$event_type', 'count': {'$sum': 1}}}
            ]
            event_counts = {}
            for doc in self.db.analytics.aggregate(pipeline):
                event_counts[doc['_id']] = doc['count']

            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_conversations': total_conversations,
                'recent_conversations': recent_conversations,
                'total_projects': total_projects,
                'event_counts': event_counts,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Erreur de récupération analytics: {e}")
            return {}

    # ==================== MAINTENANCE ====================

    def cleanup_old_data(self, days=365):
        """Nettoie les données anciennes (conformité RGPD)."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            # Supprimer les anciennes entrées d'audit
            result = self.db.audit_logs.delete_many({
                'timestamp': {'$lt': cutoff}
            })
            logger.info(f"Nettoyage: {result.deleted_count} entrées d'audit supprimées")

            # Supprimer les anciens événements analytics
            result = self.db.analytics.delete_many({
                'timestamp': {'$lt': cutoff}
            })
            logger.info(f"Nettoyage: {result.deleted_count} événements analytics supprimés")

        except Exception as e:
            logger.error(f"Erreur de nettoyage des données: {e}")

    def close(self):
        """Ferme la connexion MongoDB."""
        try:
            self.client.close()
            logger.info("Connexion MongoDB fermée")
        except Exception as e:
            logger.error(f"Erreur de fermeture MongoDB: {e}")
