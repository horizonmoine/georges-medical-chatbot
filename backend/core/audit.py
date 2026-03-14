"""
Module d'audit pour Georges Medical Chatbot.
Journalisation des actions utilisateur pour conformité et traçabilité.
"""

import logging
import json
import os
from datetime import datetime, timezone
from uuid import uuid4
from flask import request

logger = logging.getLogger(__name__)


class AuditLogger:
    """Journalisation d'audit avec support Elasticsearch ou fichier."""

    def __init__(self, elastic_manager=None):
        self.elastic_manager = elastic_manager
        self.audit_log_file = os.environ.get('AUDIT_LOG_FILE', 'audit.log')
        self._file_logger = None

        if not self.elastic_manager:
            self._setup_file_logger()

    def _setup_file_logger(self):
        """Configure un logger fichier pour les entrées d'audit."""
        self._file_logger = logging.getLogger('audit_file')
        self._file_logger.setLevel(logging.INFO)
        if not self._file_logger.handlers:
            handler = logging.FileHandler(self.audit_log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S%z'
            ))
            self._file_logger.addHandler(handler)

    def log_action(self, user_id, action, resource_type, resource_id=None,
                   status='success', details=None):
        """
        Enregistre une action d'audit.

        Args:
            user_id: Identifiant de l'utilisateur
            action: Action effectuée (create, read, update, delete, login, etc.)
            resource_type: Type de ressource (user, conversation, project, etc.)
            resource_id: Identifiant de la ressource concernée
            status: Statut de l'action (success, failure, error)
            details: Détails supplémentaires
        """
        try:
            ip_address = None
            user_agent = None
            try:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')
            except RuntimeError:
                # Pas de contexte de requête Flask
                pass

            audit_entry = {
                'audit_id': str(uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'status': status,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent
            }

            if self.elastic_manager:
                try:
                    self.elastic_manager.es.index(
                        index=f"{self.elastic_manager.index_prefix}_audit_logs",
                        document=audit_entry
                    )
                except Exception as e:
                    logger.error(f"Erreur d'écriture audit dans Elasticsearch: {e}")
                    self._log_to_file(audit_entry)
            else:
                self._log_to_file(audit_entry)

        except Exception as e:
            logger.error(f"Erreur lors de la journalisation d'audit: {e}")

    def _log_to_file(self, audit_entry):
        """Écrit l'entrée d'audit dans le fichier de log."""
        try:
            if self._file_logger:
                self._file_logger.info(json.dumps(audit_entry, ensure_ascii=False))
            else:
                logger.info(f"AUDIT: {json.dumps(audit_entry, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"Erreur d'écriture dans le fichier d'audit: {e}")

    def get_user_audit_trail(self, user_id, limit=100):
        """
        Récupère le journal d'audit d'un utilisateur.

        Args:
            user_id: Identifiant de l'utilisateur
            limit: Nombre maximum d'entrées à retourner

        Returns:
            Liste des entrées d'audit
        """
        try:
            if self.elastic_manager:
                try:
                    result = self.elastic_manager.es.search(
                        index=f"{self.elastic_manager.index_prefix}_audit_logs",
                        body={
                            'query': {'term': {'user_id': user_id}},
                            'sort': [{'timestamp': {'order': 'desc'}}],
                            'size': limit
                        }
                    )
                    return [hit['_source'] for hit in result['hits']['hits']]
                except Exception as e:
                    logger.error(f"Erreur de lecture audit depuis Elasticsearch: {e}")
                    return []
            else:
                # Lecture depuis le fichier de log
                return self._read_audit_from_file(user_id, limit)

        except Exception as e:
            logger.error(f"Erreur de récupération du journal d'audit: {e}")
            return []

    def _read_audit_from_file(self, user_id, limit=100):
        """Lit les entrées d'audit depuis le fichier pour un utilisateur donné."""
        entries = []
        try:
            if not os.path.exists(self.audit_log_file):
                return entries

            with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # Le format est: timestamp - json_data
                        parts = line.strip().split(' - ', 1)
                        if len(parts) == 2:
                            entry = json.loads(parts[1])
                            if entry.get('user_id') == user_id:
                                entries.append(entry)
                    except (json.JSONDecodeError, IndexError):
                        continue

            # Trier par timestamp décroissant et limiter
            entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return entries[:limit]

        except Exception as e:
            logger.error(f"Erreur de lecture du fichier d'audit: {e}")
            return []
