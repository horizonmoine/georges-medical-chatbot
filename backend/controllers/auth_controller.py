"""
Contrôleur d'authentification pour Georges Medical Chatbot.
Inscription, connexion, déconnexion, confirmation email, refresh token.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from backend.core.security import require_auth

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Inscription d'un nouvel utilisateur."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        security = current_app.security_manager
        dm = current_app.data_manager

        # Validation des champs requis
        required_fields = ['email', 'password', 'nom', 'prenom', 'date_naissance']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400

        email = data['email'].strip().lower()
        password = data['password']
        nom = security.sanitize_input(data['nom'], max_length=100)
        prenom = security.sanitize_input(data['prenom'], max_length=100)
        date_naissance = security.sanitize_input(data['date_naissance'], max_length=20)

        # Validation email
        if not security.validate_email(email):
            return jsonify({'error': 'Format d\'email invalide'}), 400

        # Validation mot de passe
        is_valid, msg = security.validate_password_strength(password)
        if not is_valid:
            return jsonify({'error': msg}), 400

        # Vérifier si l'email existe déjà
        existing = dm.get_user_by_email(email)
        if existing:
            return jsonify({'error': 'Cet email est déjà utilisé'}), 409

        # Générer un token de confirmation
        confirmation_token = security.generate_secure_token()

        # Créer l'utilisateur
        role = data.get('role', 'patient')
        if role not in ('patient', 'medecin', 'investigateur'):
            role = 'patient'

        user = dm.create_user(
            email=email,
            password=password,
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            role=role,
            confirmation_token=confirmation_token
        )

        if not user:
            return jsonify({'error': 'Erreur lors de la création du compte'}), 500

        # Envoyer l'email de confirmation
        if hasattr(current_app, 'email_service') and current_app.email_service:
            current_app.email_service.send_confirmation_email(
                email, confirmation_token, current_app.config.get('FRONTEND_URL', '')
            )

        # Log analytics
        dm.record_analytics_event('user_signup', user_id=user['userId'])

        logger.info(f"Inscription réussie: {user['userId']}")
        return jsonify({
            'message': 'Inscription réussie. Veuillez confirmer votre email.',
            'userId': user['userId']
        }), 201

    except Exception as e:
        logger.error(f"Erreur d'inscription: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Connexion d'un utilisateur."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email et mot de passe requis'}), 400

        security = current_app.security_manager
        dm = current_app.data_manager

        # Vérifier les identifiants
        is_valid, user = dm.verify_user_password(email, password)
        if not is_valid or not user:
            current_app.audit_logger.log_action(
                user_id=email,
                action='login_failed',
                resource_type='auth',
                status='failure'
            )
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

        # Vérifier que le compte est actif
        if not user.get('is_active', True):
            return jsonify({'error': 'Compte désactivé'}), 403

        # Générer les tokens
        access_token = security.create_access_token(user['userId'], user['role'])
        refresh_token = security.create_refresh_token(user['userId'])

        # Créer la session
        current_app.session_manager.create_session(
            user_id=user['userId'],
            token=access_token,
            user_data={'role': user['role'], 'email': email}
        )

        # Log audit
        current_app.audit_logger.log_action(
            user_id=user['userId'],
            action='login',
            resource_type='auth',
            status='success'
        )

        dm.record_analytics_event('user_login', user_id=user['userId'])

        from backend.models.user import sanitize_user_response
        user_response = sanitize_user_response(user, include_sensitive=True)

        logger.info(f"Connexion réussie: {user['userId']}")
        return jsonify({
            'message': 'Connexion réussie',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_response
        }), 200

    except Exception as e:
        logger.error(f"Erreur de connexion: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@auth_bp.route('/login/ldap', methods=['POST'])
def login_ldap():
    """Connexion via LDAP (utilisateurs hospitaliers)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Identifiant et mot de passe requis'}), 400

        ldap_service = getattr(current_app, 'ldap_service', None)
        if not ldap_service or not ldap_service.enabled:
            return jsonify({'error': 'Authentification LDAP non configurée'}), 503

        security = current_app.security_manager
        dm = current_app.data_manager

        # Authentification LDAP
        success, user_info = ldap_service.authenticate(username, password)
        if not success or not user_info:
            current_app.audit_logger.log_action(
                user_id=username,
                action='ldap_login_failed',
                resource_type='auth',
                status='failure'
            )
            return jsonify({'error': 'Identifiants LDAP invalides'}), 401

        # Vérifier si l'utilisateur existe déjà en base
        email = user_info.get('email', username)
        user = dm.get_user_by_email(email)

        if not user:
            # Créer l'utilisateur automatiquement
            random_password = security.generate_secure_token(32)
            user = dm.create_user(
                email=email,
                password=random_password,
                nom=user_info.get('nom', ''),
                prenom=user_info.get('prenom', ''),
                date_naissance='',
                role=user_info.get('role', 'medecin')
            )
            if user:
                dm.update_user(user['userId'], {'is_confirmed': True})

        if not user:
            return jsonify({'error': 'Erreur de création du compte LDAP'}), 500

        # Générer les tokens
        access_token = security.create_access_token(user['userId'], user['role'])
        refresh_token = security.create_refresh_token(user['userId'])

        # Créer la session
        current_app.session_manager.create_session(
            user_id=user['userId'],
            token=access_token,
            user_data={'role': user['role'], 'email': email}
        )

        current_app.audit_logger.log_action(
            user_id=user['userId'],
            action='ldap_login',
            resource_type='auth',
            status='success'
        )

        from backend.models.user import sanitize_user_response
        user_response = sanitize_user_response(user, include_sensitive=True)

        return jsonify({
            'message': 'Connexion LDAP réussie',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_response
        }), 200

    except Exception as e:
        logger.error(f"Erreur de connexion LDAP: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth()
def logout():
    """Déconnexion de l'utilisateur."""
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split('Bearer ')[1].strip()

        current_app.session_manager.terminate_session(token)

        current_app.audit_logger.log_action(
            user_id=request.current_user['user_id'],
            action='logout',
            resource_type='auth',
            status='success'
        )

        return jsonify({'message': 'Déconnexion réussie'}), 200

    except Exception as e:
        logger.error(f"Erreur de déconnexion: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@auth_bp.route('/confirm-email/<token>', methods=['GET'])
def confirm_email(token):
    """Confirme l'adresse email d'un utilisateur."""
    try:
        dm = current_app.data_manager

        # Rechercher l'utilisateur par token de confirmation
        # Pour MongoDB
        if hasattr(dm, 'db'):
            user = dm.db.users.find_one({'confirmation_token': token})
        else:
            # Pour Elasticsearch
            result = dm.es.search(
                index=dm._index('users'),
                body={
                    'query': {'term': {'confirmation_token': token}},
                    'size': 1
                }
            )
            hits = result['hits']['hits']
            user = hits[0]['_source'] if hits else None

        if not user:
            return jsonify({'error': 'Token de confirmation invalide'}), 400

        # Confirmer l'email
        dm.update_user(user['userId'], {
            'is_confirmed': True,
            'confirmation_token': None
        })

        current_app.audit_logger.log_action(
            user_id=user['userId'],
            action='confirm_email',
            resource_type='user',
            status='success'
        )

        return jsonify({'message': 'Email confirmé avec succès'}), 200

    except Exception as e:
        logger.error(f"Erreur de confirmation email: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@auth_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Rafraîchit le token d'accès."""
    try:
        data = request.get_json()
        if not data or not data.get('refresh_token'):
            return jsonify({'error': 'Refresh token requis'}), 400

        security = current_app.security_manager
        dm = current_app.data_manager

        # Vérifier le refresh token
        is_valid, payload = security.verify_token(data['refresh_token'])
        if not is_valid:
            return jsonify({'error': 'Refresh token invalide ou expiré'}), 401

        if payload.get('type') != 'refresh':
            return jsonify({'error': 'Type de token invalide'}), 401

        user_id = payload.get('user_id')
        user = dm.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        if not user.get('is_active', True):
            return jsonify({'error': 'Compte désactivé'}), 403

        # Générer un nouveau token d'accès
        access_token = security.create_access_token(user['userId'], user['role'])

        # Créer une nouvelle session
        current_app.session_manager.create_session(
            user_id=user['userId'],
            token=access_token,
            user_data={'role': user['role']}
        )

        return jsonify({
            'access_token': access_token,
            'message': 'Token rafraîchi avec succès'
        }), 200

    except Exception as e:
        logger.error(f"Erreur de rafraîchissement du token: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500
