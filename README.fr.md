# REA-Video-Pro-Max

## Décryptez le montage. Créez un nouveau contenu dans son style.

**Transformez une vidéo de référence en timeline étayée et en modèle de style réutilisable. Associez un autre script et d’autres médias pour rendre votre propre vidéo.**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[Démonstration enregistrée](docs/index.html) · [Vidéo A](docs/media/reference.mp4) · [Vidéo B](docs/media/adapted.mp4) · [Vérification (English)](docs/VALIDATION.md)

Un bon montage rassemble des décisions : où couper, comment grouper les mots, lequel souligner, quand arrêter un mouvement et comment synchroniser le son. REA-Video-Pro-Max rend les éléments pris en charge inspectables et réutilisables.

```text
Vidéo A → analyse + timeline inférée → modèle de style + nouveau contenu → projet éditable → vidéo B
```

La démonstration utilise des médias synthétiques appartenant au projet. A et B ont des textes et médias différents. Le site statique montre un résultat enregistré ; il n’exécute pas d’inférence en direct et ne téléverse pas les vidéos des visiteurs.

## Que pouvez-vous demander ?

- Décomposer toute la vidéo en plans, sous-titres, style, mouvement, repères audio et timeline avec preuves horodatées.
- Analyser la typographie, la mise en page et les couleurs d’une image. Une image seule ne permet pas d’établir l’animation ou le son.
- Appliquer le style extrait à un nouveau script, à des images ou à de nouvelles prises de vue pour créer une autre vidéo.
- Livrer uniquement la timeline et les fichiers d’analyse lorsque c’est la tâche demandée.

```text
Utilise REA-Video-Pro-Max pour analyser la timeline et le style de reference.mp4. Avec mon nouveau script et mes médias, crée une autre vidéo aux sous-titres, mouvements et rythme similaires. Livre le modèle, le projet, la vidéo et les limites encore non vérifiées.
```

## Obtenir un premier résultat

Il faut Python 3.11+, FFmpeg et FFprobe. Le runtime Python utilise Pillow, NumPy et PyAV. Tesseract est facultatif pour l’OCR ; les données linguistiques installées déterminent les langues disponibles. Voir le [périmètre vérifié (English)](docs/SUPPORT-MATRIX.md).

macOS est la plateforme de développement mesurée. Linux est une cible CI prévue ; le rendu natif sous Windows n’est pas certifié. La vérification de création exige le reçu exact du rendu et une passe OCR indépendante : le parcours complet nécessite donc Tesseract avec les données `eng`.

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

Les commandes utilisent l’arborescence du checkout Git. Dans le paquet de skill extrait, le point d’entrée est `scripts/rea-video-pro-max.py` ; conservez ensemble `lib`, `assets` et `references`. Utilisez le Python contenant les dépendances, sans copier seulement le script.

## Apporter votre contenu

`examples/content.json` est un exemple synthétique de content binding : chaque nouvelle scène comporte `id`, `text`, `duration`, `background`, `accent` et un chemin `asset` facultatif. `width`, `height`, `fps` règlent la sortie ; `audio` et `font` sont facultatifs. Les chemins sont résolus par rapport au fichier de bindings. Le projet copie les médias et consigne leurs empreintes, sans remplacer discrètement le nouveau contenu par les images ou la musique de A. De nouvelles paroles demandent de nouveaux temps ; la méthode d’estimation est précisée en l’absence d’alignement exact.

Le son des vidéos de scène est coupé ; fournissez une nouvelle liaison `audio` pour le son. Les séquences courtes conservent leur dernière image. Le rendu natif exige des médias correctement orientés à pixels carrés. CSV exporte uniquement les lignes de plans. Vérifiez les limites de composition et de regroupement pour les écritures complexes ou bidirectionnelles.

## Utiliser avec Claude Code / Codex

Copiez tout le dossier `skills/rea-video-pro-max` dans le répertoire de skills de votre hôte, ou demandez à l’agent de l’installer depuis ce checkout. Les emplacements de projet courants sont `.claude/skills/rea-video-pro-max` et `.agents/skills/rea-video-pro-max`. Installer la skill n’installe ni FFmpeg, ni langues OCR, ni poids de modèles. Compte, permissions d’exécution et politique de données de l’hôte sont distincts. La [skill](skills/rea-video-pro-max/SKILL.md) et les références techniques sont en English.

## Fichiers et exportation

- Le JSON natif conserve analyse, timeline, données de sous-titres/style/mouvement/audio, modèles et projets. Le CSV sert à inspecter les données éditoriales.
- SRT/WebVTT/ASS exportent le texte et les temps selon leurs capacités. Le SRT ne conserve pas toute la typographie ou le mouvement.
- Utilisez seulement les adaptateurs de timeline déclarés disponibles par la version installée. Le reçu précise le sous-ensemble, les approximations et les pertes ; il ne garantit pas tous les effets dans tous les éditeurs.
- Le moteur logiciel compose le nouveau contenu et l’encode avec FFmpeg. Il ne nécessite pas les filtres facultatifs `drawtext`, `ass` ou `subtitles`.

## Limites importantes

Métadonnées mesurées, OCR, ajustements de style et hypothèses de montage sont des preuves différentes. Une vidéo aplatie ne détermine pas de manière unique les clips source, couches cachées, police, plug-in, projet d’édition ou prompt IA d’origine. Le périmètre initial cible les temps, sous-titres et primitives 2D compatibles. Ce n’est ni un décompilateur universel ni un leader démontré du marché. Occlusions complexes, reconstruction 3D, mastering HDR et allers-retours NLE arbitraires sont hors du périmètre vérifié. Les écritures complexes exigent shaping et tests propres ; neuf traductions ne certifient pas neuf langues d’OCR ou de rendu.

La vidéo B est vérifiée selon son nouveau contenu, son contrat de style et sa lecture, pas selon une identité des pixels de l’image entière avec A. Vérification technique et jugement créatif humain restent distincts. [Preuves et limites (English)](docs/VALIDATION.md).

## Traitement local et crédits

Le noyau fonctionne localement, sans exiger d’API payante, téléverser de vidéo vers une inférence hébergée ou publier des médias. Installer des dépendances ou utiliser un fournisseur facultatif peut nécessiter le réseau. Les politiques de l’hôte Claude/Codex sont distinctes. [Privacy (English)](docs/PRIVACY.md). Inspiré par JuneYaooo/rea-video, ce produit indépendant n’est pas une mise à niveau officielle. Les licences du code, des polices, médias, codecs et modèles s’appliquent séparément.

Les rapports locaux copient par défaut le média de référence et les preuves. `report --no-media` omet seulement la copie complète du média ; le texte OCR, les chemins locaux et les recadrages restent présents. Vérifiez avant de partager.

[Assistance (English)](SUPPORT.md) · [Maintenance (English)](docs/MAINTENANCE.md) · Aucune révision professionnelle des traductions par des locuteurs natifs n’est revendiquée.

[Parole locale et mouvement avancé (référence technique en anglais)](skills/rea-video-pro-max/references/speech-and-motion.md).
