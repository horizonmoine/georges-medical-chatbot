# Georges — Chatbot Médical HEGP/APHP

Assistant médical intelligent pour l'Hôpital Européen Georges-Pompidou.
Architecture 3-tiers : Frontend Vue 3 → Flask API → FastAPI LLM.

---

## Démarrage rapide (Docker)

```bash
cp .env.example .env
# Remplir au minimum : SECRET_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY, GEMINI_API_KEY

docker-compose -f docker/docker-compose.yml up --build
```

| Service    | URL                        |
|------------|----------------------------|
| Frontend   | http://localhost:3000       |
| Backend    | http://localhost:5000/api   |
| LLM        | http://localhost:8000       |
| Elasticsearch | http://localhost:9200   |

> **MongoDB** est désactivé par défaut. Pour l'activer : `docker-compose --profile mongodb up`

---

## Développement local

### Backend (Python 3.12+)

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

FLASK_ENV=development python app.py
```

### LLM Service

```bash
cd llm_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## Architecture

```
frontend/          Vue 3 + Pinia + Bootstrap 5 + SCSS
  src/views/         Pages principales (Chat, Dashboard, Admin...)
  src/stores/        État global (auth, chat, project, summary...)
  src/components/    Composants réutilisables (chat/, admin/, common/)
  src/services/      Clients HTTP (api.js avec refresh token auto)
  src/router/        Routes + guards d'authentification

backend/           Flask (Python)
  app.py             Factory pattern, initialisation des services
  config.py          Configuration multi-environnements
  controllers/       Blueprints REST (auth, user, chat, project, admin, export)
  database/          ElasticDataManager + MongoDataManager (même interface)
  core/              SecurityManager (AES-256-CBC + JWT + bcrypt), AuditLogger
  middleware/        SessionManager (5min), RateLimiter, ErrorHandler
  services/          LLMClient, LDAPService, EmailService
  models/            Factories de documents (user, conversation, project...)

llm_service/       FastAPI (Python) — microservice IA
  main.py            Endpoints : /api/generate, /api/summarize, /api/health
  services/          GeminiService, DummyService (pour tests sans clé API)

docker/
  docker-compose.yml  5 services (mongodb optionnel via profil)
  Dockerfile.*        Images pour chaque service
  nginx.conf          Reverse proxy frontend
```

---

## Rôles utilisateurs

| Rôle          | Niveau | Description                                      |
|---------------|--------|--------------------------------------------------|
| `user`        | niv1   | Patient / utilisateur standard                   |
| `medecin`     | niv2   | Médecin investigateur (accès données cliniques)  |
| `tester`      | niv3   | Testeur (accès aux projets de test)              |
| `admin`       | niv3   | Admin projet (détient la clé de chiffrement)     |
| `super_admin` | niv99  | Super administrateur plateforme                  |

---

## Variables d'environnement clés

| Variable           | Requis | Description                                         |
|--------------------|--------|-----------------------------------------------------|
| `SECRET_KEY`       | ✅     | Clé de signature Flask (min 32 chars, hex aléatoire)|
| `JWT_SECRET_KEY`   | ✅     | Clé de signature JWT                               |
| `ENCRYPTION_KEY`   | ✅     | Clé AES-256 pour données patients (32 bytes, base64)|
| `GEMINI_API_KEY`   | ✅     | Clé API Google Gemini                              |
| `DB_BACKEND`       | —      | `elasticsearch` (défaut) ou `mongodb`              |
| `ELASTIC_HOST`     | —      | `http://localhost:9200` par défaut                 |
| `LDAP_SERVER`      | —      | URL LDAP APHP (optionnel)                          |
| `MAILGUN_API_KEY`  | —      | Pour les emails transactionnels                    |

Générer les clés :
```bash
python -c "import secrets; print(secrets.token_hex(32))"          # SECRET_KEY / JWT_SECRET_KEY
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"  # ENCRYPTION_KEY
```

---

## Sécurité

- Chiffrement AES-256-CBC des données patients sensibles dans Elasticsearch
- JWT access token : **5 minutes** / refresh token : 7 jours
- Session inactivité : **5 minutes** (déconnexion automatique)
- Authentification LDAP APHP disponible (`/api/auth/login/ldap`)
- Audit trail complet dans Elasticsearch
- RGPD : export données (`/api/user/data-export`), suppression compte (`/api/user/delete-account`)

---

## Tests

```bash
cd backend
pytest tests/ -v --cov=backend
```

---

## Ajouter un modèle LLM

1. Créer `llm_service/services/mon_service.py` héritant de `BaseLLMService`
2. Implémenter `generate()`, `summarize()`, `analyze_symptoms()`
3. Enregistrer dans `llm_service/main.py` → `get_llm_service()`
