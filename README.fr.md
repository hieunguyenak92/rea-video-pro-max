# REA-Video-Pro-Max

## Donnez à Claude et Codex le regard d’un monteur.

**Décomposez le rythme, les sous-titres et les mouvements d’une vidéo de référence. Transformez ces choix en style réutilisable. Créez le rendu d’une nouvelle vidéo avec vos propres mots et médias.**

Les beaux montages ont leur langage. Faites-en un outil de création.

[**▶ Explorez la démo en ligne**](https://hieunguyenak92.github.io/rea-video-pro-max/) · [**Téléchargez le skill**](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) · [Version v0.1.1](https://github.com/hieunguyenak92/rea-video-pro-max/releases/tag/v0.1.1)

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

**Skill Claude Code / Codex · CLI + MCP facultatif · Traitement local · Apache-2.0**

---

## De « J’adore ce montage » à « Voici ma version ».

Vous trouvez une vidéo qui dégage exactement l’énergie recherchée : le rythme des coupes, l’apparition des sous-titres, un surlignage qui parcourt chaque phrase, un zoom qui anime une image fixe.

REA-Video-Pro-Max transforme les éléments pris en charge de ce style en quelque chose que vous pouvez examiner, ajuster et réutiliser. Apportez un nouveau script, des images, des séquences ou une narration. Vous repartez avec un projet modifiable et une vidéo réellement rendue.

| Référence A | Votre nouvelle vidéo B |
| :---: | :---: |
| [![Image de la vidéo de référence créée pour le projet](docs/media/readme-reference.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) | [![Image rendue avec de nouveaux mots et des médias indépendants](docs/media/readme-new-video.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) |
| Étudiez le rythme des plans et le traitement des sous-titres. | Appliquez le style réutilisable à une autre histoire. |

*Images réelles de la démo créée pour le projet et incluse dans le dépôt. B utilise de nouveaux textes, des médias générés indépendamment et un nouveau minutage des sous-titres. Le [parcours interactif](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) permet de parcourir les deux vidéos et d’examiner la timeline enregistrée, le modèle de style, le projet et la vérification.*

```text
Reference video → editing evidence + timeline → reusable style
                                                   + your new content
                                                   → editable project + Video B
```

## Faites travailler une référence

| Ce que vous voulez faire | Ce que vous obtenez |
| --- | --- |
| Comprendre ce qui donne son caractère à un montage | Intervalles des plans, texte visible, apparence des sous-titres, mouvement apparent et indices audio, reliés à des horodatages et à des preuves. |
| Transposer un traitement de sous-titres dans une nouvelle histoire | Typographie, disposition et palettes de surlignage réutilisables, appliquées aux nouveaux mots avec leur propre minutage. |
| Construire un format vidéo récurrent | Un modèle de style à associer à un autre script et à un autre ensemble de ressources. |
| Diriger le résultat | Une timeline/un projet natif en JSON, avec ressources copiées et empreintes, que vous pouvez examiner, modifier et rendre à nouveau. |
| Intégrer l’analyse à votre propre chaîne de production | Fichiers structurés, inspecteur hors ligne, exports de sous-titres et échanges de timelines aux limites définies. |

Utilisez-le pour présenter un produit, créer une capsule pédagogique, construire une série de contenus, étudier un montage ou développer un outil vidéo sur mesure. Si vous avez seulement besoin de la décomposition, l’analyse et la timeline constituent à elles seules des livrables complets.

## Un prompt pour lancer le travail

Installez le skill fourni, donnez à votre agent la référence et votre nouveau contenu, puis formulez la demande suivante. Ce prompt en anglais est prêt à l’emploi :

```text
Use REA-Video-Pro-Max to break down reference.mp4: shot rhythm,
subtitle layout, highlight colors and supported motion.
Extract a reusable style, then use my new script and assets to make
an original video with a similar editing language.
Render the video, keep the editable project, verify the new content,
and show me any effects that need an approximation.
```

Vous dirigez l’histoire. Le skill donne à l’agent un processus concret et des outils exécutables pour analyser, composer, rendre et vérifier.

## Ce qui rend ce processus utile

- **Un montage que vous pouvez examiner.** Les horodatages de présentation décodés, les preuves par image et la couverture rendent la timeline traçable. Les signaux mesurés, les résultats de modèles et les choix de montage inférés conservent des étiquettes distinctes.
- **Des détails de sous-titres qui arrivent jusqu’au projet.** Estimez la taille visible, la position, le remplissage et le contour ; conservez les différentes palettes de surlignage et variantes de style observées. Réorganisez les nouveaux mots et recalculez leur minutage pendant la composition.
- **Du mouvement qui garde sa direction.** Ajustez des modèles bornés de mouvement de similitude/affine et des courbes temporelles candidates. Le moteur de rendu natif peut réutiliser la composante de zoom prise en charge avec son signe, y compris un zoom arrière.
- **Un projet pour continuer à créer.** Les nouvelles images, séquences, polices et pistes audio facultatives sont copiées dans un projet portable. Les associations explicites et les empreintes permettent d’examiner le contenu choisi.
- **La voix quand le travail l’exige.** L’ASR local facultatif avec faster-whisper fournit des intervalles de mots issus du modèle. Une correspondance stricte entre script et audio peut les associer au nouveau contenu ; un modèle local explicitement indiqué est requis.
- **Un résultat que vous pouvez contrôler.** Vérifiez la correspondance entre projet et sortie, décodez la vidéo rendue et contrôlez le texte des sous-titres avec un OCR indépendant. Conservez les preuves avec le résultat.

Le moteur de rendu natif prend en charge les **sous-titres statiques / fade / pop / slide**, les **transitions cut / dissolve / fade / wipe** et les **arrière-plans statiques / panzoom avec direction conservée**. L’analyse peut retenir des observations de mouvement plus riches que ce que le moteur natif sait reproduire. [Prise en charge exacte (anglais)](docs/SUPPORT-MATRIX.md).

## Obtenez votre premier résultat

### 1. Préparez l’environnement d’exécution

Utilisez **Python 3.11+**, **FFmpeg + FFprobe** et une version de FFmpeg intégrant **libx264**. Installez **Tesseract avec les données linguistiques `eng`** pour exécuter l’exemple inclus d’OCR et de vérification des sous-titres. Les dépendances Python sont installées ci-dessous.

```sh
git clone https://github.com/hieunguyenak92/rea-video-pro-max.git
cd rea-video-pro-max
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
rea-video-pro-max doctor
```

Ces commandes shell visent macOS/Linux. Le CI de la version a réussi sous Linux et macOS ; le rendu natif sous Windows n’est pas certifié. `doctor` indique les outils réellement disponibles sur votre machine.

### 2. Donnez le skill à votre agent

Copiez le dossier **entier** `skills/rea-video-pro-max` dans le répertoire de skills de votre projet :

| Environnement | Destination dans le projet |
| --- | --- |
| Claude Code | `.claude/skills/rea-video-pro-max` |
| Codex | `.agents/skills/rea-video-pro-max` |

Vous pouvez également y extraire le [ZIP du skill](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip). Gardez `lib`, `assets`, `scripts` et `references` ensemble. Pour une installation depuis le ZIP seul, installez ses dépendances Python avec `python -m pip install -r /path/to/rea-video-pro-max/requirements.txt` ; le point d’entrée est `python /path/to/rea-video-pro-max/scripts/rea-video-pro-max.py`. Les commandes de console ci-dessous proviennent de l’installation du dépôt décrite plus haut. Votre agent doit utiliser l’interpréteur contenant ces dépendances.

### 3. Exécutez l’exemple A → B inclus

```sh
rea-video-pro-max analyze examples/reference.mp4 --out work/analysis --ocr required --ocr-lang eng
rea-video-pro-max template work/analysis/analysis.json --out work/style-template.json
rea-video-pro-max compose work/style-template.json --content examples/content.json --out work/project
rea-video-pro-max render work/project/project.json --out work/video-b.mp4
rea-video-pro-max verify work/project/project.json --mode style-transfer --render work/video-b.mp4 --ocr-lang eng
```

Ouvrez `work/video-b.mp4`. Votre projet portable se trouve dans `work/project/` ; l’analyse de la référence est dans `work/analysis/`. Utilisez un nouveau répertoire de sortie pour chaque composition. Pour générer un inspecteur d’analyse hors ligne, lancez :

```sh
rea-video-pro-max report work/analysis/analysis.json --out work/report
```

Puis ouvrez `work/report/timeline.html` localement. La [CLI, le skill et le MCP facultatif partagent le même noyau (anglais)](skills/rea-video-pro-max/references/runtime-and-support.md).

<details>
<summary><strong>À vous de jouer : que contient une association de contenu ?</strong></summary>

Une association de contenu est un fichier JSON qui définit vos nouvelles scènes, textes et médias, ainsi que l’audio et la police facultatifs. Votre agent peut le créer à partir d’un brief ordinaire. Commencez avec [examples/content.json](examples/content.json).

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 24,
  "scenes": [
    {
      "id": "intro",
      "text": "Your next story starts here",
      "duration": 3.0,
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

Ajoutez un chemin `asset` pour une image ou une vidéo, et `audio` pour une bande-son ou une narration explicite. Les chemins des médias sont résolus par rapport à ce fichier JSON. Le moteur de rendu utilise le nouveau contenu choisi ; réutiliser les médias exacts de la référence nécessite une activation explicite.

Les nouveaux mots reçoivent un nouveau minutage. Le minutage pondéré par le nombre de caractères reste une estimation. Fournissez de nouveaux intervalles de mots ou utilisez un ASR local avec correspondance stricte lorsque la synchronisation de la parole compte. [Guide voix et mouvement (anglais)](skills/rea-video-pro-max/references/speech-and-motion.md).

</details>

## Voyez le travail derrière la promesse

**La v0.1.1 a réussi 176 tests locaux**, dont le cas réel d’ASR local facultatif. [Le CI hébergé a réussi trois jobs Linux/macOS](https://github.com/hieunguyenak92/rea-video-pro-max/actions/runs/43324016397). Les six artefacts publiés de la version ont été téléchargés et comparés aux octets et sommes de contrôle locaux.

Les preuves comprennent une reproduction complète créée pour le projet de **A → analyse → style → nouveau B**, une tâche indépendante en vietnamien avec typographie/contour corrigés et deux traitements de surlignage, ainsi qu’une tâche de mouvement qui conserve la direction du zoom avant/arrière. Ces cas de test internes sont délimités : ils établissent le processus démontré, sans prouver une précision générale pour tous les genres ou toutes les langues.

[Examiner l’analyse](docs/evidence/reference-analysis.json) · [Lire le modèle de style](docs/evidence/style-template.json) · [Ouvrir le projet](docs/evidence/project.json) · [Contrôler la vérification](docs/evidence/verification.json) · [Détails de validation (anglais)](docs/VALIDATION.md)

## Gardez le résultat. Étendez le système.

| Format | Ce qu’il contient |
| --- | --- |
| JSON natif | Analyse, timelines, données de sous-titres/style/mouvement/audio, modèles de style et projets natifs modifiables. |
| CSV | Lignes de plans pour inspection et traitement ultérieur. |
| SRT / WebVTT | Texte visible et intervalles des sous-titres. |
| ASS | Minutage des sous-titres avec un style de substitution explicite ; l’apparence observée et l’incertitude restent dans les preuves natives. |
| OTIO / EDL | Extraits facultatifs de la référence en OTIO avec annotations ; EDL pour les coupes mesurées à cadence constante entière. Les comptes rendus d’export décrivent les pertes. |
| MP4 + HTML hors ligne | La nouvelle vidéo et un rapport d’analyse local que vous pouvez examiner. |

Le projet natif est du JSON modifiable. Cette version n’exporte pas de projets natifs Premiere, Resolve, After Effects ou CapCut, ni de FCPXML. L’importation des fichiers d’échange pris en charge dans des logiciels de montage externes reste non vérifiée. [Limites des exporteurs et du moteur de rendu (anglais)](docs/SUPPORT-MATRIX.md).

## Connaissez les limites créatives

La version actuelle se concentre sur les preuves de montage observables et sur la réutilisation des styles **2D** pris en charge. Les polices d’origine exactes, calques cachés, plugins, ressources sources et historique du projet peuvent rester inconnus. L’OCR et les ajustements de mouvement peuvent se tromper ; la couverture échantillonnée et l’incertitude restent visibles.

Les séquences associées doivent être orientées correctement, avec des pixels carrés. Leur audio de scène est coupé ; fournissez l’audio explicitement. Les écritures complexes nécessitent des polices et une mise en forme typographique adaptées ; les sous-titres bidirectionnels sont refusés. Les neuf traductions du README décrivent le produit et ne certifient pas neuf langues d’OCR/rendu. L’évaluation du style créatif et du son conserve une part de revue humaine. [Matrice complète de prise en charge (anglais)](docs/SUPPORT-MATRIX.md).

Le traitement principal est local et ne nécessite ni API de modèle payante ni envoi de contenu. Les dépendances et la préparation des modèles facultatifs peuvent nécessiter un accès réseau ; l’environnement Claude/Codex a ses propres règles relatives aux données. Les rapports locaux incluent par défaut les médias de référence et les recadrages. `report --no-media` omet la copie complète de la référence, tandis que le texte et les recadrages sont conservés. [Confidentialité (anglais)](docs/PRIVACY.md).

## Participez au prochain workflow de montage

**Si vous voulez ce processus dans votre boîte à outils créative, donnez une étoile au projet.** Vous aiderez d’autres créateurs et développeurs d’IA à découvrir ce travail.

**Créez un fork pour construire votre propre vocabulaire de montage :** ajoutez un traitement de sous-titres, développez un adaptateur de rendu, étendez un export ou proposez un exemple créé par vos soins, de la référence au résultat. Apportez des preuves reproductibles pour que chaque nouvelle capacité mérite sa place.

[**⭐ Donnez une étoile sur GitHub**](https://github.com/hieunguyenak92/rea-video-pro-max) · [**🍴 Créez un fork et construisez**](https://github.com/hieunguyenak92/rea-video-pro-max/fork) · [Contribuer (anglais)](CONTRIBUTING.md) · [Proposer une tâche](https://github.com/hieunguyenak92/rea-video-pro-max/issues)

Projet indépendant, inspiré de [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video). [Apache-2.0](LICENSE) ; les conditions propres aux polices, codecs et modèles sont conservées dans [NOTICE](NOTICE).

[Assistance (anglais)](SUPPORT.md) · [Maintenance (anglais)](docs/MAINTENANCE.md) · [Instructions du skill (anglais)](skills/rea-video-pro-max/SKILL.md)
