import PyInstaller.__main__
import os
import shutil
import sys

def create_exe():
    # Obtenir le chemin absolu du répertoire de travail
    work_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Nettoyer les dossiers de build précédents
    for folder in ['build', 'dist']:
        folder_path = os.path.join(work_dir, folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    
    # S'assurer que nous sommes dans le bon répertoire
    os.chdir(work_dir)
    
    # Utiliser le fichier de spécification
    spec_path = os.path.join(work_dir, 'PDFCompressor.spec')
    if not os.path.exists(spec_path):
        print(f"Erreur: Le fichier {spec_path} n'existe pas.")
        return
    
    try:
        PyInstaller.__main__.run([
            spec_path,
            '--clean',
            '--noconfirm'
        ])
        print("\nBuild terminé ! L'exécutable se trouve dans le dossier 'dist'")
    except Exception as e:
        print(f"\nErreur lors du build: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_exe() 