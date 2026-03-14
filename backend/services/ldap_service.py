"""
Service LDAP pour Georges Medical Chatbot.
Authentification des utilisateurs hospitaliers via annuaire LDAP.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from ldap3 import Server, Connection, ALL, SUBTREE
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    logger.warning("ldap3 package non disponible - authentification LDAP désactivée")


class LDAPService:
    """Service d'authentification LDAP pour les utilisateurs hospitaliers."""

    def __init__(self, server_url, base_dn, bind_dn=None, bind_password=None):
        """
        Initialise le service LDAP.

        Args:
            server_url: URL du serveur LDAP (ex: ldap://ldap.hospital.fr)
            base_dn: DN de base pour les recherches
            bind_dn: DN pour le bind de service (optionnel)
            bind_password: Mot de passe pour le bind de service (optionnel)
        """
        self.server_url = server_url
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.enabled = bool(server_url and base_dn and LDAP_AVAILABLE)

        if not LDAP_AVAILABLE:
            logger.warning("Service LDAP désactivé: ldap3 non installé")
        elif not server_url:
            logger.info("Service LDAP désactivé: LDAP_SERVER non configuré")

    def authenticate(self, username, password):
        """
        Authentifie un utilisateur via LDAP.

        Args:
            username: Nom d'utilisateur ou email
            password: Mot de passe

        Returns:
            tuple: (success: bool, user_info: dict ou None)
                   user_info contient: email, nom, prenom, role
        """
        if not self.enabled:
            logger.warning("Tentative d'authentification LDAP alors que le service est désactivé")
            return False, None

        try:
            server = Server(self.server_url, get_info=ALL)

            # Rechercher l'utilisateur d'abord si on a un bind de service
            user_dn = None
            if self.bind_dn and self.bind_password:
                conn = Connection(
                    server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    auto_bind=True
                )
                search_filter = f"(|(uid={username})(mail={username})(sAMAccountName={username}))"
                conn.search(
                    self.base_dn,
                    search_filter,
                    search_scope=SUBTREE,
                    attributes=['dn', 'mail', 'givenName', 'sn', 'uid',
                                'memberOf', 'cn']
                )
                if conn.entries:
                    user_dn = str(conn.entries[0].entry_dn)
                conn.unbind()

                if not user_dn:
                    logger.info(f"Utilisateur LDAP non trouvé: {username}")
                    return False, None
            else:
                # Tentative directe avec le DN construit
                user_dn = f"uid={username},{self.base_dn}"

            # Authentification par bind
            auth_conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True
            )

            if auth_conn.bound:
                # Récupérer les informations de l'utilisateur
                auth_conn.search(
                    user_dn,
                    '(objectClass=*)',
                    search_scope=SUBTREE,
                    attributes=['mail', 'givenName', 'sn', 'uid',
                                'memberOf', 'cn']
                )

                user_info = {
                    'email': '',
                    'nom': '',
                    'prenom': '',
                    'role': 'medecin'  # Rôle par défaut pour les utilisateurs LDAP
                }

                if auth_conn.entries:
                    entry = auth_conn.entries[0]
                    user_info['email'] = str(entry.mail) if hasattr(entry, 'mail') else username
                    user_info['nom'] = str(entry.sn) if hasattr(entry, 'sn') else ''
                    user_info['prenom'] = str(entry.givenName) if hasattr(entry, 'givenName') else ''

                auth_conn.unbind()
                logger.info(f"Authentification LDAP réussie pour: {username}")
                return True, user_info

            auth_conn.unbind()
            return False, None

        except Exception as e:
            logger.error(f"Erreur d'authentification LDAP: {e}")
            return False, None

    def search_user(self, username):
        """
        Recherche un utilisateur dans l'annuaire LDAP.

        Args:
            username: Nom d'utilisateur ou email

        Returns:
            dict ou None: Informations de l'utilisateur
        """
        if not self.enabled:
            return None

        try:
            server = Server(self.server_url, get_info=ALL)

            if self.bind_dn and self.bind_password:
                conn = Connection(
                    server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    auto_bind=True
                )
            else:
                conn = Connection(server, auto_bind=True)

            search_filter = f"(|(uid={username})(mail={username})(sAMAccountName={username}))"
            conn.search(
                self.base_dn,
                search_filter,
                search_scope=SUBTREE,
                attributes=['mail', 'givenName', 'sn', 'uid', 'cn', 'memberOf']
            )

            if conn.entries:
                entry = conn.entries[0]
                user_info = {
                    'email': str(entry.mail) if hasattr(entry, 'mail') else '',
                    'nom': str(entry.sn) if hasattr(entry, 'sn') else '',
                    'prenom': str(entry.givenName) if hasattr(entry, 'givenName') else '',
                    'uid': str(entry.uid) if hasattr(entry, 'uid') else '',
                    'dn': str(entry.entry_dn)
                }
                conn.unbind()
                return user_info

            conn.unbind()
            return None

        except Exception as e:
            logger.error(f"Erreur de recherche LDAP: {e}")
            return None
