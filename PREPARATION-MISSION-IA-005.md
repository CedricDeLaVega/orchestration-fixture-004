# ORCHESTRATION — Mission IA fictive 005 (PRÉPARATION UNIQUEMENT)

**Statut** : NON EXÉCUTABLE / aucun workflow activé / aucune requête API autorisée.

## Périmètre
Dépôt public fictif `CedricDeLaVega/orchestration-fixture-004`. Ne jamais transférer des fichiers, secrets ou données de FILCKO dans ce dépôt. `OPENAI_API_KEY` est configuré par le Fondateur comme secret Actions (valeur inaccessible à ce document).

## Objectif
Une mission courte et entièrement fictive (« ALPHA doit précéder BETA ; produire un résumé de 2 phrases et une dépendance »), exécutée une seule fois par Codex en lecture seule. Résultat récupéré par un job distinct avec seulement `issues: write`, après vérification déterministe d'un GO limité. Aucune remontée de contenu non fictif.

## Conditions bloquantes avant toute activation
1. **GO d'exécution séparé** et explicite du Fondateur (ce document n'en constitue pas un).
2. Contrôle du statut *disabled* du précédent workflow `race.yml`.
3. Réduction du risque : permissions du job Codex `contents: read`, checkout `persist-credentials: false`, `permission-profile: read-only`; aucun secret GitHub transféré au job éditeur; action tierce épinglée à SHA validé.
4. Verrou déterministe et unique de consommation du GO : référence GitHub créée en HTTP 201, avec contrôle de dépôt, acteur, workflow SHA, échéance, mission, budget et nonce ; aucun GO fondé sur commentaire IA.
5. Mesure budgétaire : nombre d'exécutions = 1, aucun retry; temps d'exécution borné, modèle/prix vérifiés avant GO, limitation tokens si supportée, coût de la requête vérifié après exécution. Les 5 USD prépayés ne constituent pas un plafond absolu.
6. Gestion panne : disable manuel documenté, en plus du disable automatique si disponible; pas de relance sur erreur.
7. Authentification OpenAI : vérifier en test limité que la clé restreinte autorise `/v1/responses` et les fonctions réellement nécessaires à Codex, sans élargissement préventif.
8. À la clôture : coût API réel, coût GitHub, valeur de la mission et recommandation conserver/désactiver/supprimer l'essai.

## Définition de réussite
- Une seule mission IA fictive exécutée.
- Un seul résultat court publié automatiquement par job distinct.
- Aucune action d'écriture de Codex sur dépôt GitHub.
- Mesure du coût réel, journal auditable.
- Workflow désactivé après l'essai, preuve indépendante.
