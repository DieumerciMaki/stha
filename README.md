# Déchets urbains

Application du travail de fin d’étude pour importer des photographies, segmenter les déchets avec YOLO, consulter leurs coordonnées et vérifier les résultats. Le périmètre vient des objectifs et de la délimitation du Word dans REDACTION. L’interface reprend la maquette fournie.

## Utiliser sur ce PC

L’installation est réalisée. Ouvrez **http://127.0.0.1:8001** lorsque le serveur tourne. Pour un prochain lancement, double-cliquez **LANCER.cmd** dans ce dossier. Gardez sa fenêtre ouverte ; Ctrl+C arrête l’application. PostgreSQL du projet utilise le port 5433 et son dossier runtime/postgres.

1. Au premier lancement, créez votre compte administrateur. Choisissez un identifiant et un mot de passe de dix caractères minimum.
2. Cliquez **Ajouter une observation**. Importez une photographie, ou choisissez **Utiliser une image exemple**.
3. Renseignez le titre. Le quartier, la date de capture, les coordonnées et les notes sont facultatifs. Une paire latitude/longitude saisie est prioritaire sur le GPS EXIF.
4. Gardez **Lancer l’analyse après l’import** coché. Le traitement s’exécute en arrière-plan sur le CPU.
5. À la fin, examinez **Original**, **Segmentation** et **Masque**. Un administrateur ou un vérificateur peut accepter, rejeter ou laisser le résultat à vérifier.
6. Exportez le masque PNG, le résultat JSON ou le dossier de l’observation. Le registre propose CSV et la carte GeoJSON, pour l’ensemble des observations enregistrées.

Les trois exemples fournis viennent du dépôt CatSatOK ; ils ne constituent pas des observations de terrain à Goma. Leur import est volontaire. Aucun point géographique ni chiffre de la maquette n’est préchargé.

## Stack effectivement intégrée

| Partie | Technologie |
| --- | --- |
| Interface | React 19, TypeScript, Vite, Tailwind CSS 4, CSS de composants, Lucide |
| Carte | Leaflet 1.9, fond OpenStreetMap |
| API | Python 3.11, FastAPI |
| Données | PostgreSQL 18, SQLAlchemy, Alembic |
| Segmentation | YOLO11s-seg entraîné sur TACO, Ultralytics, PyTorch CPU |
| Traitement des masques | OpenCV, NumPy, Pillow pour lecture et orientation EXIF |
| Traitements locaux | File persistée en base, exécutée par un seul thread |
| Variante conteneurisée | Docker Compose, Celery, Redis ; configuration fournie, non exécutée sur ce PC sans Docker |
| Annotation | CVAT comme outil externe, export COCO polygonal et convertisseur fourni |

## Fichiers importants

- frontend/src : composants React, écrans, styles et appels à l’API.
- backend/app : API, comptes et sessions, base, segmentation et traitements.
- backend/migrations : évolution du schéma de base.
- models/active.json : modèle actif, révision, source et SHA256.
- samples/manifest.json : provenance des images exemples.
- scripts : installation du modèle, conversion des annotations, entraînement, évaluation et sauvegarde.
- docs/GUIDE_UTILISATION.docx : utilisation, fonctionnement, architecture et expérimentation.
- docs/COHERENCE_MEMOIRE.md : correspondance avec le Word et ambiguïtés restantes.

## Réinstaller et développer

Pré requis : Python 3.11, Node.js 22.12 ou supérieur, PostgreSQL installé sous Windows et espace disponible pour PyTorch. Dans PowerShell depuis PROJECT :

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Le lancement est limité à 127.0.0.1. Le fichier .env et runtime/database-credentials.json contiennent les accès de la base dédiée ; ne les publiez pas. L’installation de ce PC partage des fichiers de dépendances immuables par liens matériels pour économiser de l’espace. Les chemins de l’environnement PROJECT restent autonomes ; sa suppression n’exige pas de supprimer LOGICIEL.

Pour développer l’interface, lancez aussi `npm.cmd run dev` depuis frontend ; Vite transmet /api au serveur 8001. La version servie par FastAPI provient de `npm.cmd run build`.

## Entraîner et évaluer

Annotez les déchets dans CVAT avec des polygones. Exportez en COCO 1.0 et préparez les images dans un dossier. La conversion utilise une partition initiale 70/15/15 avec seed 42 ; séparez ensuite les photos du même site et de la même capture entre groupes, pour prévenir une fuite entre train et test.

```powershell
.venv\Scripts\python.exe scripts\convert_coco.py --annotations annotations.json --images images --output datasets\goma
.venv\Scripts\python.exe scripts\train.py --data datasets\goma\dataset.yaml --epochs 50 --device cpu
.venv\Scripts\python.exe scripts\register_model.py --weights runs\goma-segmentation\weights\best.pt --name "YOLO déchets Goma" --dataset "Goma polygones version 1"
.venv\Scripts\python.exe scripts\evaluate.py --data datasets\goma\dataset.yaml --weights models\goma-segmentation.pt --device cpu
```

Ultralytics peut suffixer le dossier runs si un entraînement précédent existe ; utilisez le chemin affiché par le terminal. Redémarrez le serveur après changement du modèle. L’évaluation utilise uniquement la partition test et enregistre les métriques de masque, l’empreinte du modèle et celle des images/annotations. Elle est affichée pour le modèle dont l’empreinte correspond. Un entraînement peut nécessiter longtemps sur CPU ; `--device 0` est réservé à une installation CUDA compatible.

## Vérification et sauvegarde

```powershell
.venv\Scripts\python.exe -m pytest tests -q
npm.cmd --prefix frontend run build
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe scripts\backup.py
```

Arrêtez d’abord l’API et attendez la fin des traitements pour faire une sauvegarde cohérente. PostgreSQL doit rester démarré. Le dossier backups contient le dump PostgreSQL et une archive des fichiers, des poids et des exemples. Consultez le guide pour la restauration.

En cas d’oubli du mot de passe, un responsable ayant accès au PC et aux fichiers du projet peut utiliser `.venv\Scripts\python.exe scripts\reset_password.py --login IDENTIFIANT`. Le nouveau mot de passe est demandé sans être affiché et les sessions du compte sont invalidées.

## Périmètre scientifique

Les masques sont des prédictions réelles du modèle externe. Le masque global est leur union, sans compter deux fois les recouvrements. La couverture est une fraction des pixels de l’image, pas une surface au sol ni un volume. Le nombre d’instances n’est pas le nombre de dépôts municipaux. Aucune précision sur Goma, amélioration de collecte ou garantie de segmentation volumique 3D n’est revendiquée. La fiche du modèle publie des performances modestes sur TACO ; l’évaluation du TFE exige des images annotées indépendantes de Goma.

Sources : [modèle et métriques publiées](https://huggingface.co/CatSat/yolov11-litter-materials), [code et exemples](https://github.com/CatSatOK/litter-detection-yolov11), [segmentation Ultralytics](https://docs.ultralytics.com/tasks/segment/), [licence du moteur](https://www.ultralytics.com/license), [CVAT](https://docs.cvat.ai/).
