# Correspondance avec le mémoire

Source relue : fichier Word original de REDACTION, 929Travail_From_MOLO_MBASA_Joaquim_1788783009 corrigÃ©️ complet.docx. Le fichier original n’a pas été modifié. Maquette visuelle conservée dans MAQUETTE_REFERENCE.png.

## Choix d’implémentation

| Passage du Word | Fonction réalisée | Limite et interprétation |
| --- | --- | --- |
| 0.6.1 Détecter et segmenter les zones contenant des déchets à partir d’images | Import, YOLO11s-seg, masques d’instances, masque binaire global, contours OpenCV | Modèle externe de déchets individuels ; l’union des masques ne garantit pas le contour complet d’un amas |
| 0.6.1 Localiser les zones | Coordonnées saisies ou GPS EXIF, Leaflet, export GeoJSON | La photo sans GPS ne permet pas de retrouver automatiquement une adresse |
| 0.6.2 Interface pour gestionnaires municipaux | Dashboard, registre, historique des analyses, carte, vérifications et exports | Compteurs issus des observations enregistrées, jamais des nombres de la maquette |
| 0.7.1 Approche expérimentale | Scripts d’annotation COCO, contrôle des partitions, entraînement, évaluation test, hashes | Pas de corpus de terrain fourni ; l’efficacité scientifique à Goma reste à mesurer |
| 0.7.2 Images, aide à la décision, Goma | Application locale centrée sur photographies et résultats vérifiés | Pas de gestion industrielle ou d’organisation automatique de la collecte |
| Théorie OpenCV et YOLO | YOLO via Ultralytics/PyTorch ; OpenCV/NumPy pour pixels, union, contours et fichiers | Instance segmentation, puis union sémantique déchets/fond ; aucune preuve de supériorité expérimentale |

## Points du manuscrit à harmoniser

Le document contient encore un titre de parking souterrain, des plans de contrôle d’accès, une année 2019–2020, des sections répétées et une référence à Kinshasa. Les objectifs et la délimitation propres au sujet désignent Goma et 2025–2026. Ces restes de gabarit ne servent pas à définir les modules de l’application.

Les questions de recherche parlent aussi de vidéo en temps réel, mais la délimitation 0.7.2 retient uniquement les images. Le logiciel livré suit cette délimitation. Il ne prétend donc pas répondre expérimentalement à l’hypothèse d’une amélioration des services par un flux vidéo en temps réel.

Le chapitre théorique annonce des cartes topologiques combinatoires 3D, Euler et Betti. Aucun capteur de profondeur, corpus volumique ou algorithme spécifié n’accompagne cette proposition. L’application produit des masques 2D et ne réalise pas cette méthode 3D. Le périmètre 2D avec YOLO a été confirmé par l’utilisateur le 8 octobre 2026. Le passage 3D doit donc être harmonisé dans le mémoire avec l’encadreur. Une photo monoculaire ne justifie pas un volume de déchets.

Les métriques TACO affichées dans la page Modèle sont celles publiées par l’auteur externe, clairement séparées d’une future évaluation de terrain. Les décisions des utilisateurs constituent un journal de vérification ; elles ne remplacent pas des annotations de référence indépendantes.

## Licence et provenance

Le poids livré est issu de CatSat/yolov11-litter-materials, révision 25a03cf200441cfd9e8e62ded5529e49562bd96b, SHA256 e48518a798b05ef6a8a123526aedc6ee9afe508796dd0b1bc37c0c2eb333a164. Le fournisseur déclare MIT pour son dépôt. Ultralytics demeure soumis à ses propres conditions AGPL-3.0 ou Enterprise. Les trois exemples sont attribués au dépôt CatSatOK et laissés sans coordonnées.

CVAT reste un outil externe d’annotation ; le convertisseur et les commandes d’entraînement sont intégrés au projet. La variante Docker/Celery/Redis est fournie séparément du mode Windows local. Sa disponibilité dans les fichiers ne vaut pas un déploiement ni une validation Docker sur cette machine.
