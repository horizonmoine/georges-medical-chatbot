"""
Gestionnaire Elasticsearch pour Georges Medical Chatbot.
Interface complète pour la gestion des données avec chiffrement intégré.
"""

import logging
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from backend.core.security import SecurityManager
from backend.core.audit import AuditLogger

logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch, NotFoundError
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False
    logger.warning("elasticsearch package non disponible")


class ElasticDataManager:
    """Gestionnaire de données Elasticsearch avec chiffrement intégré."""

    def __init__(self, host, index_prefix, encryption_key):
        """
        Initialise la connexion Elasticsearch.

        Args:
            host: URL du serveur Elasticsearch
            index_prefix: Préfixe des index
            encryption_key: Clé de chiffrement pour les données sensibles
        """
        if not ES_AVAILABLE:
            raise ImportError("Le package elasticsearch est requis pour ElasticDataManager")

        self.es = Elasticsearch([host])
        self.index_prefix = index_prefix
        self.security = SecurityManager(encryption_key)
        self.audit = AuditLogger(elastic_manager=self)
        logger.info(f"Connexion Elasticsearch initialisée: {host}")

    def _index(self, name):
        """Retourne le nom complet de l'index."""
        return f"{self.index_prefix}_{name}"

    def initialize_indices(self):
        """Crée les index et mappings nécessaires."""
        try:
            indices = {
                'users': {
                    'mappings': {
                        'properties': {
                            'userId': {'type': 'keyword'},
                            'email': {'type': 'keyword'},
                            'password_hash': {'type': 'keyword', 'index': False},
                            'nom': {'type': 'text', 'index': False},
                            'prenom': {'type': 'text', 'index': False},
                            'date_naissance': {'type': 'text', 'index': False},
                            'role': {'type': 'keyword'},
                            'is_active': {'type': 'boolean'},
                            'is_confirmed': {'type': 'boolean'},
                            'confirmation_token': {'type': 'keyword'},
                            'consents': {'type': 'nested'},
                            'created_at': {'type': 'date'},
                            'updated_at': {'type': 'date'}
                        }
                    }
                },
                'conversations': {
                    'mappings': {
                        'properties': {
                            'conversationId': {'type': 'keyword'},
                            'userId': {'type': 'keyword'},
                            'projectId': {'type': 'keyword'},
                            'messages': {'type': 'nested'},
                            'status': {'type': 'keyword'},
                            'created_at': {'type': 'date'},
                            'updated_at': {'type': 'date'}
                        }
                    }
                },
                'projects': {
                    'mappings': {
                        'properties': {
                            'projectId': {'type': 'keyword'},
                            'name': {'type': 'text'},
                            'description': {'type': 'text'},
                            'slug': {'type': 'keyword'},
                            'created_by': {'type': 'keyword'},
                            'status': {'type': 'keyword'},
                            'participants': {'type': 'keyword'},
                            'created_at': {'type': 'date'},
                            'updated_at': {'type': 'date'}
                        }
                    }
                },
                'consents': {
                    'mappings': {
                        'properties': {
                            'consentId': {'type': 'keyword'},
                            'userId': {'type': 'keyword'},
                            'projectId': {'type': 'keyword'},
                            'consent_type': {'type': 'keyword'},
                            'granted': {'type': 'boolean'},
                            'revoked': {'type': 'boolean'},
                            'timestamp': {'type': 'date'}
                        }
                    }
                },
                'audit_logs': {
                    'mappings': {
                        'properties': {
                            'audit_id': {'type': 'keyword'},
                            'user_id': {'type': 'keyword'},
                            'action': {'type': 'keyword'},
                            'resource_type': {'type': 'keyword'},
                            'resource_id': {'type': 'keyword'},
                            'status': {'type': 'keyword'},
                            'timestamp': {'type': 'date'},
                            'ip_address': {'type': 'ip'}
                        }
                    }
                },
                'analytics': {
                    'mappings': {
                        'properties': {
                            'eventId': {'type': 'keyword'},
                            'event_type': {'type': 'keyword'},
                            'user_id': {'type': 'keyword'},
                            'timestamp': {'type': 'date'}
                        }
                    }
                }
            }

            for name, body in indices.items():
                index_name = self._index(name)
                if not self.es.indices.exists(index=index_name):
                    self.es.indices.create(index=index_name, body=body)
                    logger.info(f"Index créé: {index_name}")

            logger.info("Index Elasticsearch initialisés")
        except Exception as e:
            logger.error(f"Erreur d'initialisation des index: {e}")
            raise

    # ==================== USERS ====================

    def create_user(self, email, password, nom, prenom, date_naissance,
                    role='patient', confirmation_token=None):
        """Crée un nouvel utilisateur avec données chiffrées."""
        try:
            # Vérifier unicité email
            existing = self.get_user_by_email(email)
            if existing:
                logger.warning(f"Email déjà utilisé: {email}")
                return None

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

            self.es.index(
                index=self._index('users'),
                id=user_doc['userId'],
                document=user_doc,
                refresh='wait_for'
            )

            self.audit.log_action(
                user_id=user_doc['userId'],
                action='create',
                resource_type='user',
                resource_id=user_doc['userId'],
                status='success'
            )
            logger.info(f"Utilisateur créé: {user_doc['userId']}")
            return user_doc

        except Exception as e:
            logger.error(f"Erreur de création utilisateur: {e}")
            raise

    def get_user_by_email(self, email):
        """Récupère un utilisateur par email avec déchiffrement."""
        try:
            result = self.es.search(
                index=self._index('users'),
                body={
                    'query': {'term': {'email': email}},
                    'size': 1
                }
            )
            hits = result['hits']['hits']
            if hits:
                user = hits[0]['_source']
                return self._decrypt_user_fields(user)
            return None
        except Exception as e:
            logger.error(f"Erreur de récupération utilisateur par email: {e}")
            return None

    def get_user_by_id(self, user_id):
        """Récupère un utilisateur par userId avec déchiffrement."""
        try:
            result = self.es.get(index=self._index('users'), id=user_id)
            user = result['_source']
            return self._decrypt_user_fields(user)
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Erreur de récupération utilisateur par ID: {e}")
            return None

    def update_user(self, user_id, updates):
        """Met à jour un utilisateur."""
        try:
            encrypted_fields = ['nom', 'prenom', 'date_naissance']
            for field in encrypted_fields:
                if field in updates:
                    updates[field] = self.security.encrypt_data(updates[field])

            updates['updated_at'] = datetime.now(timezone.utc).isoformat()

            self.es.update(
                index=self._index('users'),
                id=user_id,
                body={'doc': updates},
                refresh='wait_for'
            )

            self.audit.log_action(
                user_id=user_id,
                action='update',
                resource_type='user',
                resource_id=user_id,
                status='success'
            )
            return True
        except Exception as e:
            logger.error(f"Erreur de mise à jour utilisateur: {e}")
            return False

    def verify_user_password(self, email, password):
        """Vérifie le mot de passe d'un utilisateur."""
        try:
            result = self.es.search(
                index=self._index('users'),
                body={
                    'query': {'term': {'email': email}},
                    'size': 1
                }
            )
            hits = result['hits']['hits']
            if not hits:
                return False, None

            user = hits[0]['_source']
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
                user['date_naissance_decrypted'] = self.security.decrypt_data(
                    user['date_naissance']
                )
        except Exception as e:
            logger.error(f"Erreur de déchiffrement des champs utilisateur: {e}")
        return user

    # ==================== CONVERSATIONS ====================

    def create_conversation(self, user_id, project_id=None):
        """Crée une nouvelle conversation."""
        try:
            from backend.models.conversation import create_conversation_doc
            conv_doc = create_conversation_doc(user_id, project_id)

            self.es.index(
                index=self._index('conversations'),
                id=conv_doc['conversationId'],
                document=conv_doc,
                refresh='wait_for'
            )

            self.audit.log_action(
                user_id=user_id,
                action='create',
                resource_type='conversation',
                resource_id=conv_doc['conversationId'],
                status='success'
            )
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

            self.es.update(
                index=self._index('conversations'),
                id=conversation_id,
                body={
                    'script': {
                        'source': 'ctx._source.messages.add(params.message); ctx._source.updated_at = params.now',
                        'params': {
                            'message': message_doc,
                            'now': datetime.now(timezone.utc).isoformat()
                        }
                    }
                },
                refresh='wait_for'
            )
            return message_doc
        except Exception as e:
            logger.error(f"Erreur d'ajout de message: {e}")
            raise

    def get_conversation(self, conversation_id, decrypt=True):
        """Récupère une conversation avec déchiffrement optionnel."""
        try:
            result = self.es.get(
                index=self._index('conversations'),
                id=conversation_id
            )
            conv = result['_source']
            if decrypt:
                conv = self._decrypt_conversation_messages(conv)
            return conv
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Erreur de récupération conversation: {e}")
            return None

    def get_user_conversations(self, user_id, limit=50, offset=0):
        """Récupère les conversations d'un utilisateur."""
        try:
            result = self.es.search(
                index=self._index('conversations'),
                body={
                    'query': {'term': {'userId': user_id}},
                    'sort': [{'updated_at': {'order': 'desc'}}],
                    'size': limit,
                    'from': offset
                }
            )

            conversations = []
            for hit in result['hits']['hits']:
                conv = hit['_source']
                conv['message_count'] = len(conv.get('messages', []))
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

            total = result['hits']['total']['value']
            return conversations, total
        except Exception as e:
            logger.error(f"Erreur de récupération des conversations: {e}")
            return [], 0

    def delete_conversation(self, conversation_id, user_id):
        """Supprime une conversation."""
        try:
            conv = self.get_conversation(conversation_id, decrypt=False)
            if not conv or conv.get('userId') != user_id:
                return False

            self.es.delete(
                index=self._index('conversations'),
                id=conversation_id,
                refresh='wait_for'
            )

            self.audit.log_action(
                user_id=user_id,
                action='delete',
                resource_type='conversation',
                resource_id=conversation_id,
                status='success'
            )
            return True
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

            self.es.index(
                index=self._index('consents'),
                id=consent_doc['consentId'],
                document=consent_doc,
                refresh='wait_for'
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
            must = [
                {'term': {'userId': user_id}},
                {'term': {'consent_type': consent_type}},
                {'term': {'granted': True}},
                {'term': {'revoked': False}}
            ]
            if project_id:
                must.append({'term': {'projectId': project_id}})

            result = self.es.search(
                index=self._index('consents'),
                body={
                    'query': {'bool': {'must': must}},
                    'sort': [{'timestamp': {'order': 'desc'}}],
                    'size': 1
                }
            )
            return len(result['hits']['hits']) > 0
        except Exception as e:
            logger.error(f"Erreur de vérification du consentement: {e}")
            return False

    # ==================== PROJECTS ====================

    def create_project(self, name, description, slug, created_by,
                       model_config=None, inclusion_criteria=None):
        """Crée un nouveau projet de recherche."""
        try:
            existing = self.get_project_by_slug(slug)
            if existing:
                logger.warning(f"Slug de projet déjà utilisé: {slug}")
                return None

            from backend.models.project import create_project_doc
            project_doc = create_project_doc(
                name, description, slug, created_by,
                model_config, inclusion_criteria
            )

            self.es.index(
                index=self._index('projects'),
                id=project_doc['projectId'],
                document=project_doc,
                refresh='wait_for'
            )

            self.audit.log_action(
                user_id=created_by,
                action='create',
                resource_type='project',
                resource_id=project_doc['projectId'],
                status='success'
            )
            return project_doc
        except Exception as e:
            logger.error(f"Erreur de création projet: {e}")
            raise

    def get_project_by_slug(self, slug):
        """Récupère un projet par son slug."""
        try:
            result = self.es.search(
                index=self._index('projects'),
                body={
                    'query': {'term': {'slug': slug}},
                    'size': 1
                }
            )
            hits = result['hits']['hits']
            return hits[0]['_source'] if hits else None
        except Exception as e:
            logger.error(f"Erreur de récupération projet par slug: {e}")
            return None

    def get_project_by_id(self, project_id):
        """Récupère un projet par son projectId."""
        try:
            result = self.es.get(
                index=self._index('projects'),
                id=project_id
            )
            return result['_source']
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Erreur de récupération projet par ID: {e}")
            return None

    def get_all_projects(self, status=None):
        """Récupère tous les projets."""
        try:
            body = {
                'sort': [{'created_at': {'order': 'desc'}}],
                'size': 1000
            }
            if status:
                body['query'] = {'term': {'status': status}}
            else:
                body['query'] = {'match_all': {}}

            result = self.es.search(
                index=self._index('projects'),
                body=body
            )
            return [hit['_source'] for hit in result['hits']['hits']]
        except Exception as e:
            logger.error(f"Erreur de récupération des projets: {e}")
            return []

    def update_project(self, project_id, updates):
        """Met à jour un projet."""
        try:
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            self.es.update(
                index=self._index('projects'),
                id=project_id,
                body={'doc': updates},
                refresh='wait_for'
            )
            return True
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

            self.es.update(
                index=self._index('projects'),
                id=project_id,
                body={
                    'script': {
                        'source': 'ctx._source.access_requests.add(params.request)',
                        'params': {'request': request_doc}
                    }
                },
                refresh='wait_for'
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
            now = datetime.now(timezone.utc).isoformat()
            self.es.update(
                index=self._index('projects'),
                id=project_id,
                body={
                    'script': {
                        'source': """
                            for (int i = 0; i < ctx._source.access_requests.size(); i++) {
                                if (ctx._source.access_requests[i].requestId == params.request_id) {
                                    ctx._source.access_requests[i].status = 'approved';
                                    ctx._source.access_requests[i].reviewed_at = params.now;
                                    ctx._source.access_requests[i].reviewed_by = params.approved_by;
                                    if (!ctx._source.participants.contains(ctx._source.access_requests[i].userId)) {
                                        ctx._source.participants.add(ctx._source.access_requests[i].userId);
                                    }
                                }
                            }
                        """,
                        'params': {
                            'request_id': request_id,
                            'now': now,
                            'approved_by': approved_by
                        }
                    }
                },
                refresh='wait_for'
            )

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
            self.es.index(
                index=self._index('analytics'),
                document=event,
                refresh='wait_for'
            )
            return event
        except Exception as e:
            logger.error(f"Erreur d'enregistrement analytics: {e}")
            return None

    def get_analytics_summary(self, days=30):
        """Récupère un résumé analytique des N derniers jours."""
        try:
            since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            # Total utilisateurs
            user_count = self.es.count(
                index=self._index('users'),
                body={'query': {'match_all': {}}}
            )['count']

            # Utilisateurs actifs
            active_count = self.es.count(
                index=self._index('users'),
                body={'query': {'term': {'is_active': True}}}
            )['count']

            # Total conversations
            conv_count = self.es.count(
                index=self._index('conversations'),
                body={'query': {'match_all': {}}}
            )['count']

            # Conversations récentes
            recent_conv = self.es.count(
                index=self._index('conversations'),
                body={'query': {'range': {'created_at': {'gte': since}}}}
            )['count']

            # Total projets
            project_count = self.es.count(
                index=self._index('projects'),
                body={'query': {'match_all': {}}}
            )['count']

            return {
                'total_users': user_count,
                'active_users': active_count,
                'total_conversations': conv_count,
                'recent_conversations': recent_conv,
                'total_projects': project_count,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Erreur de récupération analytics: {e}")
            return {}

    # ==================== MAINTENANCE ====================

    def cleanup_old_data(self, days=365):
        """Nettoie les données anciennes."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            for index_name in ['audit_logs', 'analytics']:
                self.es.delete_by_query(
                    index=self._index(index_name),
                    body={
                        'query': {
                            'range': {'timestamp': {'lt': cutoff}}
                        }
                    }
                )
                logger.info(f"Nettoyage effectué sur {index_name}")
        except Exception as e:
            logger.error(f"Erreur de nettoyage des données: {e}")

    def close(self):
        """Ferme la connexion Elasticsearch."""
        try:
            self.es.close()
            logger.info("Connexion Elasticsearch fermée")
        except Exception as e:
            logger.error(f"Erreur de fermeture Elasticsearch: {e}")
