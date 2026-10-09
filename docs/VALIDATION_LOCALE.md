# Validation locale du 8 octobre 2026

## Vérifications réalisées

- Interface React/TypeScript compilée avec Vite ; aucune erreur TypeScript. Dépendances frontend installées avec package-lock.json ; npm a signalé zéro vulnérabilité lors de cette installation.
- Environnement Python 3.11 dans PROJECT/.venv ; pip check ne signale aucune incompatibilité déclarée. Dépendances figées dans backend/requirements-lock.txt.
- PostgreSQL 18 : instance dédiée à PROJECT, port 5433, rôle applicatif et base waste_project. Migrations Alembic appliquées. Lancement Windows via start.ps1 exécuté avec succès sur 127.0.0.1:8001.
- Six tests automatisés réussis : authentification et protection des fichiers, validation des entrées et export géographique, union des masques avec trous et recouvrement, parcours API et rôles, conversion COCO polygonale et détection de doublons, migration initiale sur une base temporaire. Le parcours API unitaire utilise un prédicteur contrôlé ; il ne mesure pas la reconnaissance des déchets.
- Avertissement de dépréciation Starlette/httpx dans le client de test ; aucun échec. Base temporaire fermée et nettoyée en fin de session.
- Poids réels YOLO11s-seg téléchargés depuis CatSat/yolov11-litter-materials, révision 25a03cf200441cfd9e8e62ded5529e49562bd96b. Empreinte SHA256 vérifiée et classes de segmentation confirmées.
- Appel réel sur l’exemple externe 1 : cinq instances, masque raster, superposition et résultat JSON produits. L’appel API après normalisation JPEG a mesuré 3,583 % de couverture de pixels dans le dernier test navigateur. Cette valeur est une sortie de modèle, pas une vérité terrain.
- Navigateur Edge isolé : création du compte, import de l’exemple, inférence réelle, comparaison des images, décision enregistrée, historique, recherche, carte avec un point synthétique, navigation vers un dossier depuis le marqueur, paramètres et export GeoJSON. Aucune erreur JavaScript et aucun débordement horizontal à 390 pixels. Menu mobile ouvert puis refermé par navigation.
- Sauvegarde PostgreSQL et archive de fichiers produites. Dump restauré dans une nouvelle base temporaire puis vérifié ; base temporaire supprimée après contrôle. La vérification de restauration portait sur le schéma et l’état vide du registre après nettoyage, pas sur un jeu de terrain fourni par l’utilisateur.
- Les seuls comptes, observations et fichiers créés par les tests ont été retirés à partir de leurs identifiants enregistrés. État final : aucun compte précréé, registre vide, modèle et trois exemples disponibles. Le premier utilisateur choisit son compte administrateur.
- Guide Word de huit pages exporté avec Microsoft Word et contrôlé visuellement sur chaque page. Le renderer LibreOffice du skill Documents ne trouvait pas soffice.exe ; l’export Word et Poppler ont fourni les pages de contrôle.

## Périmètre accepté et limites

### Correction de la navigation et de la carte

La mention « Travail de fin d’étude · Vision par ordinateur » a été retirée de la connexion. La navigation est organisée en groupes, avec compte en bas et réduction aux icônes Lucide. Référence de structure : shadcn/ui ; le composant React adapté est `frontend/src/Sidebar.tsx`.

La politique globale `same-origin` supprimait le Referer pour les images de tuiles OpenStreetMap. La couche Leaflet définit désormais explicitement `referrerPolicy: strict-origin-when-cross-origin` : seule l’origine de l’application est envoyée. La protection des mutations de l’API est conservée.

Contrôle avec Edge : 33 réponses de tuiles, toutes HTTP 200, Referer `http://127.0.0.1:8001/`, carte de Goma inspectée visuellement, aucune erreur JavaScript. Navigation, réduction, menu du compte et fermeture par Échap, menu mobile et absence de débordement horizontal vérifiés. Les fixtures d’API sont interceptées dans le navigateur de contrôle seulement ; aucun compte ni observation n’a été ajouté à la base. Script et preuves : `docs/qa/sidebar_map_check.cjs`, `docs/qa/sidebar-map-evidence.json`. Compilation TypeScript/Vite réussie.

La segmentation 2D avec YOLO a été confirmée par l’utilisateur. Les nombres et lieux de la maquette ne sont pas des données de l’application. Les exemples externes sont attribués et sans coordonnées de Goma.

Pas de jeu de test annoté de Goma fourni : précision, rappel, mAP de terrain et bénéfices municipaux non mesurés. Le modèle externe ne garantit pas la segmentation complète de chaque amas. La couverture est en pixels, sans estimation de volume ou de surface physique.

Les scripts d’entraînement et d’évaluation sont fournis, mais aucun entraînement ni évaluation de terrain n’a été exécuté sans corpus annoté. CVAT est externe. Docker/Celery/Redis sont configurés mais non exécutés sur ce PC, où Docker n’est pas installé. Le parcours opérationnel vérifié est Windows avec PostgreSQL et traitement en arrière-plan local.
