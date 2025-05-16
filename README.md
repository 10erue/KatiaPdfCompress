# Compresseur de PDF

Ce script Python permet de compresser des fichiers PDF avec une interface graphique conviviale.

## Installation

1. Assurez-vous d'avoir Python 3.7+ installé sur votre système
2. Installez les dépendances requises :

```bash
pip install -r requirements.txt
```

## Utilisation

### Version Python

1. Lancez l'application :

```bash
python compress_pdf.py
```

2. Dans l'interface graphique :

   - Cliquez sur "Sélectionner PDF" pour choisir votre fichier
   - Ajustez la taille maximale souhaitée (en Mo)
   - Cliquez sur "Compresser"

3. Le fichier compressé sera automatiquement sauvegardé dans le dossier "PDF_Compressed" de vos Documents et le dossier s'ouvrira automatiquement.

### Version Exécutable

Pour créer l'exécutable Windows (.exe) :

1. Assurez-vous d'avoir installé toutes les dépendances
2. Exécutez le script de build :

```bash
python build.py
```

3. L'exécutable sera créé dans le dossier `dist` sous le nom `PDFCompressor.exe`

## Fonctionnalités

- Interface graphique intuitive
- Sélection facile des fichiers PDF
- Choix de la taille maximale de compression
- Sauvegarde automatique dans le dossier Documents
- Ouverture automatique du dossier contenant le fichier compressé
- Conservation de la qualité tout en réduisant la taille

## Notes

- Les fichiers compressés sont préfixés par "compressed\_"
- Si la compression ne permet pas d'atteindre la taille cible, un message d'avertissement sera affiché
- La qualité de compression est optimisée pour maintenir une bonne lisibilité
