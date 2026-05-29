# PropertyYards Backend

Service backend basé sur FastAPI pour la plateforme immobilière PropertyYards avec des fonctionnalités complètes incluant la gestion des propriétés, l'authentification des utilisateurs, le système de récompenses et la mise en cache avancée.

## 🚀 Fonctionnalités

### Fonctionnalités Principales
- **Gestion des Propriétés**: Opérations CRUD des propriétés avec recherche et filtrage avancés
- **Authentification des Utilisateurs**: Authentification basée sur JWT avec contrôle d'accès basé sur les rôles
- **Traitement des Paiements**: Intégration de paiements sécurisés avec plusieurs fournisseurs
- **Système de Récompenses**: Système complet de points et commissions avec options de conversion
- **Analytique**: Capacités d'analyse et de reporting en temps réel
- **Intégration IA**: Recommandations de propriétés alimentées par IA et optimisation SEO

### Fonctionnalités Avancées
- **Sécurité**: Détection avancée des menaces, limitation de débit et assainissement des entrées
- **Mise en Cache**: Mise en cache multicouche basée sur Redis avec invalidation intelligente
- **Surveillance**: Surveillance des performances et vérifications de santé
- **Documentation API**: Documentation OpenAPI/Swagger générée automatiquement

## 🛠️ Stack Technique

- **Framework**: FastAPI 0.104.1
- **Base de Données**: MongoDB avec Motor (pilote async)
- **Cache**: Redis avec aioredis
- **Authentification**: JWT avec python-jose
- **Sécurité**: bcrypt, slowapi pour la limitation de débit
- **Tests**: pytest avec support async
- **Documentation**: OpenAPI/Swagger

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.8+
- MongoDB
- Redis
- Git

### Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/your-org/propertyyards-backend.git
   cd propertyyards-backend
   ```

2. **Créer l'environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec votre configuration
   ```

5. **Démarrer les services**
   ```bash
   # Démarrer MongoDB et Redis (avec Docker)
   docker-compose up -d mongodb redis

   # Exécuter l'application
   python run.py
   ```

### Configuration Docker

```bash
# Construire et exécuter avec Docker
docker-compose up -d

# Voir les logs
docker-compose logs -f backend
```

## ⚙️ Configuration

### Variables d'Environnement

```bash
# Base de Données
MONGODB_URL=mongodb://localhost:27017/housing_db
MONGO_ROOT_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
DEBUG=False
SECRET_KEY=your_app_secret
API_V1_STR=/api/v1
```

## 📚 Documentation API

Une fois le serveur démarré, visitez :
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📁 Structure du Projet

```
backend/
├── app/                    # Code de l'application
│   ├── api/               # Routes API
│   ├── auth.py            # Logique d'authentification
│   ├── cache.py           # Couche de cache
│   ├── config.py          # Configuration
│   ├── database.py        # Connexion base de données
│   ├── models.py          # Modèles de données
│   ├── security.py        # Middleware de sécurité
│   └── services/          # Logique métier
├── tests/                 # Suite de tests
├── scripts/               # Scripts utilitaires
├── requirements.txt       # Dépendances Python
├── pyproject.toml         # Configuration projet
├── Dockerfile             # Configuration Docker
├── docker-compose.yml     # Services de développement
└── README.md              # Ce fichier
```

## 🧪 Développement

### Exécuter les Tests

```bash
# Exécuter tous les tests
pytest

# Exécuter avec couverture
pytest --cov=app

# Exécuter un fichier de test spécifique
pytest tests/test_auth.py
```

### Qualité de Code

```bash
# Formater le code
black app/ tests/

# Analyser le code
flake8 app/ tests/

# Vérification des types
mypy app/
```

### Migrations de Base de Données

```bash
# Initialiser la base de données
python -m app.init_db

# Créer les index
python -m app.create_indexes
```

## 🔌 Endpoints API

### Authentification
- `POST /api/auth/login` - Connexion utilisateur
- `POST /api/auth/register` - Inscription utilisateur
- `POST /api/auth/refresh` - Token de rafraîchissement
- `POST /api/auth/logout` - Déconnexion utilisateur

### Propriétés
- `GET /api/properties` - Lister les propriétés
- `POST /api/properties` - Créer une propriété
- `GET /api/properties/{id}` - Obtenir une propriété
- `PUT /api/properties/{id}` - Mettre à jour une propriété
- `DELETE /api/properties/{id}` - Supprimer une propriété

### Récompenses
- `GET /api/rewards/wallet` - Obtenir le portefeuille de récompenses
- `POST /api/rewards/convert-points` - Convertir des points en argent
- `GET /api/rewards/conversion/history` - Historique des conversions
- `GET /api/rewards/referral/code` - Obtenir le code de parrainage

### Administration
- `GET /api/admin/stats` - Statistiques système
- `POST /api/admin/process-commission` - Traiter la commission
- `GET /api/admin/users` - Gestion des utilisateurs

## 🔒 Fonctionnalités de Sécurité

### Détection de Menaces
- Protection contre l'injection SQL
- Détection d'attaques XSS
- Prévention du parcours de chemin
- Limitation de débit par endpoint
- Blocage IP pour activité suspecte

### Authentification et Autorisation
- Authentification basée sur les tokens JWT
- Contrôle d'accès basé sur les rôles (RBAC)
- Gestion des sessions
- Support d'authentification multifactorielle

### Protection des Données
- Assainissement et validation des entrées
- Hachage des mots de passe avec bcrypt
- Configuration CORS
- Middleware d'en-têtes de sécurité

## 🚀 Stratégie de Mise en Cache

### Mise en Cache Multicouche
- **L1**: Mise en cache au niveau de l'application
- **L2**: Mise en cache distribuée Redis
- **L3**: Mise en cache des requêtes base de données

### Fonctionnalités de Cache
- Invalidation intelligente
- Réchauffement du cache pour les données fréquemment accédées
- Surveillance des performances et métriques
- Mécanismes de secours pour les échecs de cache

## 📊 Surveillance et Journalisation

### Vérifications de Santé
- `/health` - Vérification de santé de base
- `/health/detailed` - Santé détaillée du système
- `/metrics` - Métriques de l'application

### Journalisation
- Journalisation structurée JSON
- Journalisation des requêtes/réponses
- Suivi des erreurs et alertes
- Surveillance des performances

## 🚀 Déploiement

### Déploiement de Production

```bash
# Construire l'image de production
docker build -t propertyyards-backend .

# Exécuter avec la configuration de production
docker run -d --name backend \
  -e MONGODB_URL=mongodb://mongo:27017/housing_db \
  -e REDIS_URL=redis://redis:6379/0 \
  -p 8000:8000 \
  propertyyards-backend
```

### Configurations Spécifiques à l'Environnement

- **Développement**: Mode débogage, bases de données locales
- **Staging**: Configuration similaire à production avec données de test
- **Production**: Configuration optimisée, surveillance activée

## 🎯 Optimisation des Performances

### Optimisation de Base de Données
- Stratégie d'indexation MongoDB
- Mise en commun des connexions
- Optimisation des requêtes
- Politiques d'archivage des données

### Optimisation API
- Compression des réponses
- Pagination pour les grands ensembles de données
- Stratégies de mise en cache
- Modèles async/await

### Gestion de la Mémoire
- Réutilisation des connexions
- Profilage de la mémoire
- Optimisation du ramasse-miettes
- Nettoyage des ressources

## 🤝 Contribution

1. Forker le dépôt
2. Créer une branche de fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Valider les changements (`git commit -m 'Add amazing feature'`)
4. Pousser vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour les détails.

## 📞 Support

- **Documentation**: [Documentation API](http://localhost:8000/docs)
- **Problèmes**: [Problèmes GitHub](https://github.com/your-org/propertyyards-backend/issues)
- **Discussions**: [Discussions GitHub](https://github.com/your-org/propertyyards-backend/discussions)

## 🔗 Dépôts Connexes

- [Dépôt Frontend](https://github.com/your-org/propertyyards-frontend)
- [Dépôt Infrastructure](https://github.com/your-org/propertyyards-infrastructure)
- [Dépôt Documentation](https://github.com/your-org/propertyyards-docs)
