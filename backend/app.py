"""
Application Flask principale pour Georges Medical Chatbot.
Factory pattern avec initialisation des services et enregistrement des blueprints.
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from backend.config import config
from backend.core.security import SecurityManager
from backend.core.audit import AuditLogger
from backend.middleware.rate_limiter import get_limiter
from backend.middleware.error_handler import register_error_handlers
from backend.middleware.session_manager import SessionManager
from backend.services.llm_client import LLMClient
from backend.services.email_service import EmailService

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """
    Factory function pour créer l'application Flask.

    Args:
        config_name: Nom de la configuration (development, staging, production, testing, default)

    Returns:
        Flask: Instance de l'application Flask configurée
    """
    # Déterminer la configuration
    config_name = os.environ.get('FLASK_ENV', config_name)
    if config_name not in config:
        config_name = 'default'

    app_config = config[config_name]

    # Valider la configuration
    warnings, errors = app_config.validate()
    for w in warnings:
        logger.warning(f"Config warning: {w}")
    for e in errors:
        logger.error(f"Config error: {e}")

    # En production, les erreurs de config sont fatales
    if errors and config_name == 'production':
        raise RuntimeError(f"Erreurs de configuration en production: {errors}")

    # Créer l'application Flask
    app = Flask(__name__)
    app.config.from_object(app_config)

    # ==================== CORS ====================
    CORS(app, origins=app_config.CORS_ORIGINS, supports_credentials=True)

    # ==================== Rate Limiter ====================
    limiter = get_limiter(app)
    app.limiter = limiter

    # ==================== Error Handlers ====================
    register_error_handlers(app)

    # ==================== Security Manager ====================
    security_manager = SecurityManager(app_config.ENCRYPTION_KEY)
    security_manager.jwt_secret = app_config.JWT_SECRET_KEY
    app.security_manager = security_manager

    # ==================== Session Manager ====================
    session_manager = SessionManager(session_timeout_minutes=30)
    app.session_manager = session_manager

    # ==================== Data Manager (MongoDB ou Elasticsearch) ====================
    db_backend = app_config.DB_BACKEND

    if db_backend == 'elasticsearch':
        try:
            from backend.database.elastic_manager import ElasticDataManager
            data_manager = ElasticDataManager(
                host=app_config.ELASTIC_HOST,
                index_prefix=app_config.ELASTIC_INDEX_PREFIX,
                encryption_key=app_config.ENCRYPTION_KEY
            )
            data_manager.initialize_indices()
            logger.info("Elasticsearch DataManager initialisé")
        except ImportError:
            logger.error("elasticsearch package non disponible, fallback sur MongoDB")
            db_backend = 'mongodb'
        except Exception as e:
            logger.error(f"Erreur d'initialisation Elasticsearch: {e}, fallback sur MongoDB")
            db_backend = 'mongodb'

    if db_backend == 'mongodb':
        from backend.database.mongo_manager import MongoDataManager
        data_manager = MongoDataManager(
            uri=app_config.MONGO_URI,
            db_name=app_config.MONGO_DB_NAME,
            encryption_key=app_config.ENCRYPTION_KEY
        )
        data_manager.initialize_collections()
        logger.info("MongoDB DataManager initialisé")

    app.data_manager = data_manager

    # ==================== Audit Logger ====================
    if db_backend == 'elasticsearch':
        audit_logger = AuditLogger(elastic_manager=data_manager)
    else:
        audit_logger = AuditLogger()
    app.audit_logger = audit_logger

    # ==================== LLM Client ====================
    llm_client = LLMClient(base_url=app_config.LLM_SERVICE_URL)
    app.llm_client = llm_client

    # ==================== Email Service ====================
    email_service = EmailService(
        api_key=app_config.MAILGUN_API_KEY,
        domain=app_config.MAILGUN_DOMAIN
    )
    app.email_service = email_service

    # ==================== LDAP Service (optionnel) ====================
    app.ldap_service = None
    if app_config.LDAP_SERVER:
        try:
            from backend.services.ldap_service import LDAPService
            ldap_service = LDAPService(
                server_url=app_config.LDAP_SERVER,
                base_dn=app_config.LDAP_BASE_DN,
                bind_dn=app_config.LDAP_BIND_DN,
                bind_password=os.environ.get('LDAP_BIND_PASSWORD', '')
            )
            app.ldap_service = ldap_service
            logger.info("Service LDAP initialisé")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser le service LDAP: {e}")

    # ==================== Enregistrement des Blueprints ====================
    from backend.controllers.auth_controller import auth_bp
    from backend.controllers.user_controller import user_bp
    from backend.controllers.conversation_controller import conversation_bp
    from backend.controllers.chat_controller import chat_bp
    from backend.controllers.project_controller import project_bp
    from backend.controllers.admin_controller import admin_bp
    from backend.controllers.export_controller import export_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(export_bp)

    # Appliquer le rate limiter aux routes spécifiques
    limiter.limit("5 per hour")(auth_bp)

    # ==================== Health Check ====================
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Endpoint de vérification de l'état de santé de l'application."""
        health = {
            'status': 'healthy',
            'app_name': app_config.APP_NAME,
            'version': app_config.VERSION,
            'db_backend': db_backend
        }

        # Vérifier la connexion à la base de données
        try:
            if hasattr(data_manager, 'db'):
                data_manager.db.command('ping')
                health['database'] = 'connected'
            elif hasattr(data_manager, 'es'):
                if data_manager.es.ping():
                    health['database'] = 'connected'
                else:
                    health['database'] = 'disconnected'
                    health['status'] = 'degraded'
        except Exception as e:
            health['database'] = 'error'
            health['database_error'] = str(e)
            health['status'] = 'degraded'

        # Vérifier le service LLM
        try:
            llm_health = llm_client.health_check()
            health['llm_service'] = llm_health.get('status', 'unknown')
        except Exception:
            health['llm_service'] = 'unknown'

        status_code = 200 if health['status'] == 'healthy' else 503
        return jsonify(health), status_code

    logger.info(f"{app_config.APP_NAME} v{app_config.VERSION} démarré ({config_name})")
    return app


if __name__ == '__main__':
    app = create_app()

    # Planifier le nettoyage des sessions expirées
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=app.session_manager.cleanup_expired_sessions,
            trigger='interval',
            minutes=5,
            id='session_cleanup'
        )
        scheduler.start()
        logger.info("Planificateur de nettoyage des sessions démarré")
    except ImportError:
        logger.warning("APScheduler non disponible, nettoyage des sessions désactivé")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
