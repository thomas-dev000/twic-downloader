# ♞ TWIC Downloader

**Téléchargeur automatique de parties d'échecs depuis [The Week In Chess](https://theweekinchess.com/twic)**

[English](#english) · [Français](#français)

---

![Version](https://img.shields.io/badge/version-2.2-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-MIT-orange)

> **⚠️ Outil non officiel**, sans affiliation avec theweekinchess.com.
> Usage personnel et éducatif uniquement.

---

## Français

### Qu'est-ce que c'est ?

TWIC (The Week In Chess) publie chaque lundi un fichier contenant toutes les parties d'échecs jouées dans le monde cette semaine-là. Ce programme automatise entièrement le processus :

- 📥 **Télécharge** automatiquement les fichiers TWIC
- 🔄 **Dédoublonne** les parties (même entre semaines différentes)
- 📁 **Organise** par année (TWIC 2020, TWIC 2021, etc.)
- ⭐ **Filtre par Elo** pour créer une base de joueurs forts (optionnel)
- ⏰ **Planifie** un téléchargement hebdomadaire automatique
- 🌐 **Multilingue** : français, anglais, espagnol, allemand, italien

### Installation

#### 🪟 Windows (le plus simple)

1. Va dans **[Releases](../../releases/latest)**
2. Télécharge **`TWIC.Downloader.exe`**
3. Double-clique pour lancer — **aucune installation requise**

> **Note :** Windows SmartScreen peut afficher un avertissement car le fichier n'est pas signé numériquement.
> Clique sur "Informations complémentaires" puis "Exécuter quand même".
> Si Smart App Control bloque le fichier : clic droit sur le `.exe` → Propriétés → coche "Débloquer" en bas → OK.

#### 🍎 macOS

1. Ouvre le **Terminal** (Applications → Utilitaires → Terminal)

2. Installe Python si ce n'est pas déjà fait :
   ```bash
   brew install python
   ```
   (Si `brew` n'est pas installé, va sur [brew.sh](https://brew.sh) d'abord)

3. Installe les dépendances :
   ```bash
   pip3 install requests python-chess
   ```

4. Télécharge l'application :
   ```bash
   curl -LO https://github.com/TON-PSEUDO/twic-downloader/releases/latest/download/twic_app.py
   ```

5. Lance :
   ```bash
   python3 twic_app.py
   ```

#### 🐧 Linux (Ubuntu / Debian / Fedora)

1. Ouvre un **terminal**

2. Installe Python et tkinter :
   ```bash
   # Ubuntu / Debian
   sudo apt install python3 python3-pip python3-tk

   # Fedora
   sudo dnf install python3 python3-pip python3-tkinter
   ```

3. Installe les dépendances et lance :
   ```bash
   pip3 install requests python-chess
   curl -LO https://github.com/TON-PSEUDO/twic-downloader/releases/latest/download/twic_app.py
   python3 twic_app.py
   ```

---

### Utilisation

L'application se présente sous forme d'un assistant en 6 étapes :

| Étape | Description |
|-------|-------------|
| 🌐 **Langue** | Choisis ta langue (FR, EN, ES, DE, IT) |
| 👋 **Bienvenue** | Présentation de l'outil |
| 📁 **Dossier** | Choisis où stocker les fichiers |
| 📅 **Période** | Depuis quelle date télécharger (raccourcis par année disponibles). Mode "entre deux dates" possible. |
| ⭐ **Filtre Elo** | Optionnel : saisir un Elo minimum (ex: 2250) pour créer une base de joueurs forts |
| ⏰ **Planification** | Optionnel : téléchargement automatique chaque semaine (jour et heure au choix) |

Après validation, le téléchargement démarre avec une barre de progression et un log en temps réel.

### Structure des fichiers créés

```
Dossier choisi/
├── TWIC 2020/
│   ├── TWIC_2020_cumulative.pgn       ← toutes les parties 2020
│   ├── weekly_clean/
│   │   ├── twic1313_clean.pgn         ← PGN hebdomadaire nettoyé
│   │   └── ...
│   ├── raw_downloads/                 ← ZIPs bruts archivés
│   └── seen_hashes.txt                ← empreintes anti-doublons
├── TWIC 2021/
├── ...
├── TWIC 2026/
├── TWIC_elite_2250+.pgn               ← base filtrée (si activé)
├── twic_state.json                    ← dernier TWIC traité
└── twic_config.json                   ← configuration
```

### Importer dans ChessBase

**Créer une base annuelle :**
1. Ouvre ChessBase → Fichier → Nouveau → Base de données
2. Nomme-la `TWIC_2025.cbh` dans le dossier `TWIC 2025/`
3. Glisse-dépose `TWIC_2025_cumulative.pgn` dessus

**Créer un livre d'ouvertures (.ctg) :**
1. Importe `TWIC_elite_2250+.pgn` dans une base `.cbh`
2. Sélectionne toutes les parties : `Ctrl+A`
3. Clic droit → "Ajouter au livre d'ouvertures" → Nouveau → nomme-le `Elite_2250.ctg`
4. Profondeur recommandée : 30 demi-coups

### Mise à jour automatique

Si la planification est activée, le programme se lance en arrière-plan chaque semaine.

Pour vérifier ou désactiver :

| OS | Vérifier | Désactiver |
|---|---|---|
| Windows | `schtasks /Query /TN "TWIC Auto Downloader"` | `schtasks /Delete /TN "TWIC Auto Downloader" /F` |
| macOS | `launchctl list \| grep twic` | `launchctl unload ~/Library/LaunchAgents/com.twic.downloader.plist` |
| Linux | `crontab -l \| grep TWIC` | `crontab -e` puis supprimer la ligne TWIC |

---

### Compiler le .exe soi-même

```bash
pip install pyinstaller requests python-chess
pyinstaller --onefile --windowed --name "TWIC Downloader" --icon chess_knight.ico twic_app.py
```

Le `.exe` se trouve dans `dist/`. Pour compiler sur Mac ou Linux, lancer la même commande sur ces plateformes.

---

## English

### What is this?

TWIC (The Week In Chess) publishes every Monday a file containing all chess games played worldwide that week. This program fully automates the retrieval:

- 📥 **Downloads** TWIC files automatically
- 🔄 **Deduplicates** games (even across weeks)
- 📁 **Organizes** by year (TWIC 2020, TWIC 2021, etc.)
- ⭐ **Filters by Elo** to create a strong-players database (optional)
- ⏰ **Schedules** automatic weekly downloads
- 🌐 **Multilingual**: French, English, Spanish, German, Italian

### Installation

#### 🪟 Windows (easiest)

1. Go to **[Releases](../../releases/latest)**
2. Download **`TWIC.Downloader.exe`**
3. Double-click to run — **no installation needed**

> **Note:** Windows SmartScreen may show a warning. Click "More info" then "Run anyway".
> If Smart App Control blocks it: right-click the `.exe` → Properties → check "Unblock" → OK.

#### 🍎 macOS

```bash
brew install python
pip3 install requests python-chess
curl -LO https://github.com/TON-PSEUDO/twic-downloader/releases/latest/download/twic_app.py
python3 twic_app.py
```

#### 🐧 Linux

```bash
# Ubuntu / Debian
sudo apt install python3 python3-pip python3-tk
pip3 install requests python-chess
curl -LO https://github.com/TON-PSEUDO/twic-downloader/releases/latest/download/twic_app.py
python3 twic_app.py
```

### Usage

The app is a 6-step wizard:

| Step | Description |
|------|-------------|
| 🌐 **Language** | Choose your language |
| 👋 **Welcome** | Tool overview |
| 📁 **Folder** | Choose download location |
| 📅 **Period** | Select start date or custom range (year shortcuts available) |
| ⭐ **Elo filter** | Optional: keep only games from strong players (custom threshold) |
| ⏰ **Schedule** | Optional: auto-download every week |

### Import into ChessBase

1. ChessBase → File → New → Database → `TWIC_2025.cbh`
2. Drag & drop `TWIC_2025_cumulative.pgn` onto it
3. For an opening book (.ctg): import the elite PGN, Ctrl+A, right-click → "Add to opening book"

### Build from source

```bash
pip install pyinstaller requests python-chess
pyinstaller --onefile --windowed --name "TWIC Downloader" --icon chess_knight.ico twic_app.py
```

---

## FAQ

**Le téléchargement a été interrompu. Dois-je tout recommencer ? / Download was interrupted?**
Non / No. Relance simplement l'application, elle reprend là où elle s'est arrêtée. / Just restart the app, it picks up where it left off.

**Comment mettre à jour l'application ? / How to update?**
Télécharge la dernière version depuis Releases. / Download the latest version from Releases.

**Les parties sont-elles dupliquées entre semaines ? / Are games duplicated across weeks?**
Non / No. Chaque partie reçoit une empreinte unique (hash SHA1). / Each game gets a unique fingerprint (SHA1 hash).

**Quel Elo choisir ? / Which Elo threshold?**
| Seuil / Threshold | Résultat / Result |
|---|---|
| 2000+ | Joueurs de club forts / Strong club players → large database |
| 2200+ | Maîtres FIDE / FIDE Masters → good balance |
| 2500+ | Grands Maîtres / Grandmasters → specialized |
| 2700+ | Super élite / Super elite → small, focused |

---

## Crédits / Credits

- Data: [The Week In Chess](https://theweekinchess.com) by Mark Crowther
- PGN library: [python-chess](https://github.com/niklasf/python-chess) by Niklas Fiekas
- Icon: royalty-free chess knight

## Licence / License

MIT — Free to use, modify and distribute.
