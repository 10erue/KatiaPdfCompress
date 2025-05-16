import os
import sys
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import img2pdf
import io
import tempfile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                            QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, 
                            QSpinBox, QMessageBox, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt, QDateTime
import subprocess
import fitz  # PyMuPDF
import shutil
from datetime import datetime, timedelta

def get_app_data_dir():
    """Retourne le chemin du dossier AppData pour l'application"""
    app_data = os.path.join(os.getenv('APPDATA'), 'PDFCompress')
    os.makedirs(app_data, exist_ok=True)
    return app_data

def get_temp_dir():
    """Retourne le chemin du dossier temporaire dans AppData"""
    temp_dir = os.path.join(get_app_data_dir(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    temp_dir = get_temp_dir()
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

def cleanup_old_batches():
    """Nettoie les dossiers de lots plus vieux qu'une journée"""
    app_data = get_app_data_dir()
    one_day_ago = datetime.now() - timedelta(days=1)
    
    for item in os.listdir(app_data):
        item_path = os.path.join(app_data, item)
        if os.path.isdir(item_path) and item.startswith('batch_'):
            try:
                # Vérifier la date de création du dossier
                creation_time = datetime.fromtimestamp(os.path.getctime(item_path))
                if creation_time < one_day_ago:
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Erreur lors du nettoyage du dossier {item}: {str(e)}")

def create_batch_folder():
    """Crée un nouveau dossier de lot avec un timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_dir = os.path.join(get_app_data_dir(), f'batch_{timestamp}')
    os.makedirs(batch_dir, exist_ok=True)
    return batch_dir

def compress_pdf(input_path, output_path, max_size_mb=1):
    """
    Compresse un fichier PDF pour qu'il fasse moins de max_size_mb Mo
    """
    # Vérifier si le fichier existe
    if not os.path.exists(input_path):
        return False, "Le fichier n'existe pas."

    # Vérifier la taille du fichier original
    original_size = os.path.getsize(input_path) / (1024 * 1024)  # Taille en Mo
    if original_size <= max_size_mb:
        # Si le fichier est déjà assez petit, on le copie simplement
        shutil.copy2(input_path, output_path)
        return True, f"Fichier déjà sous la taille limite ({original_size:.2f} Mo)"

    try:
        # Nettoyer les fichiers temporaires précédents
        cleanup_temp_files()
        
        # Ouvrir le PDF avec PyMuPDF
        pdf_document = fitz.open(input_path)
        writer = PdfWriter()

        # Traiter chaque page
        for page_num in range(len(pdf_document)):
            try:
                # Obtenir la page
                page = pdf_document[page_num]
                
                # Convertir la page en image avec une résolution plus basse
                pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))  # Résolution encore plus réduite
                
                # Sauvegarder l'image temporairement dans le dossier AppData
                temp_img_path = os.path.join(get_temp_dir(), f'page_{page_num}.jpg')
                pix.save(temp_img_path)
                
                # Ouvrir l'image avec PIL
                img = Image.open(temp_img_path)
                
                # Convertir en niveaux de gris si l'image est en noir et blanc
                if img.mode == 'RGB':
                    # Vérifier si l'image est principalement en noir et blanc
                    img_gray = img.convert('L')
                    if sum(1 for p in img_gray.getdata() if p < 128) / (img_gray.width * img_gray.height) > 0.95:
                        img = img_gray
                
                # Compresser l'image avec des paramètres plus agressifs
                img_byte_arr = io.BytesIO()
                if img.mode == 'L':  # Noir et blanc
                    img.save(img_byte_arr, format='JPEG', quality=20, optimize=True)
                else:  # Couleur
                    img.save(img_byte_arr, format='JPEG', quality=25, optimize=True)
                img_byte_arr.seek(0)
                
                # Convertir l'image compressée en PDF
                pdf_bytes = img2pdf.convert(img_byte_arr.getvalue())
                
                # Ajouter la page compressée au nouveau PDF
                temp_pdf = io.BytesIO(pdf_bytes)
                temp_reader = PdfReader(temp_pdf)
                writer.add_page(temp_reader.pages[0])
                
            except Exception as e:
                print(f"Erreur lors du traitement de la page {page_num}: {str(e)}")
                continue
            finally:
                # Nettoyer le fichier temporaire de la page
                if os.path.exists(temp_img_path):
                    os.unlink(temp_img_path)

        # Fermer le document PyMuPDF
        pdf_document.close()

        # Sauvegarder le PDF compressé
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        # Vérifier la taille du fichier compressé
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)  # Taille en Mo
        if compressed_size > max_size_mb:
            return False, f"Le fichier compressé fait toujours {compressed_size:.2f} Mo"
        
        return True, f"Compression réussie! Taille finale: {compressed_size:.2f} Mo"
    except Exception as e:
        return False, f"Erreur lors de la compression: {str(e)}"
    finally:
        # Nettoyer les fichiers temporaires à la fin
        cleanup_temp_files()

class PDFCompressorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compresseur de PDF")
        self.setMinimumWidth(800)
        self.setMinimumHeight(200)
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Zone de drop avec scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        scroll_area.setMaximumHeight(300)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Widget conteneur pour la zone de drop
        drop_container = QWidget()
        drop_container.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 2px dashed #aaa;
                border-radius: 5px;
            }
            QWidget:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Layout pour le conteneur
        drop_layout = QVBoxLayout()
        drop_container.setLayout(drop_layout)
        
        # Label de drop
        self.drop_label = QLabel("Glissez-déposez vos fichiers PDF ici\nou cliquez pour sélectionner")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setWordWrap(True)
        self.drop_label.mousePressEvent = self.select_files
        drop_layout.addWidget(self.drop_label)
        
        # Ajouter le conteneur à la zone de défilement
        scroll_area.setWidget(drop_container)
        layout.addWidget(scroll_area)
        
        # Taille maximale
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Taille maximale (Mo):"))
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(1, 100)
        self.size_spinbox.setValue(1)
        size_layout.addWidget(self.size_spinbox)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        # Journal d'activité
        log_label = QLabel("Journal d'activité:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)  # Hauteur réduite
        layout.addWidget(self.log_text)
        
        # Bouton de compression
        self.compress_btn = QPushButton("Compresser")
        self.compress_btn.clicked.connect(self.compress_pdfs)
        self.compress_btn.setEnabled(False)
        layout.addWidget(self.compress_btn)
        
        # Liste des fichiers à traiter
        self.files_to_process = []
        
        # Activer le drag and drop
        self.setAcceptDrops(True)
        
        # Nettoyer les anciens lots au démarrage
        cleanup_old_batches()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                files.append(file_path)
        
        if files:
            self.add_files(files)
    
    def select_files(self, event):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner des fichiers PDF",
            "",
            "PDF Files (*.pdf)"
        )
        if files:
            self.add_files(files)
    
    def add_files(self, files):
        self.files_to_process.extend(files)
        self.update_drop_label()
        self.compress_btn.setEnabled(True)
        self.log_message(f"{len(files)} nouveau(x) fichier(s) ajouté(s)")
    
    def update_drop_label(self):
        if not self.files_to_process:
            self.drop_label.setText("Glissez-déposez vos fichiers PDF ici\nou cliquez pour sélectionner")
        else:
            files_text = "\n".join([f"• {os.path.basename(f)}" for f in self.files_to_process])
            self.drop_label.setText(f"Fichiers sélectionnés ({len(self.files_to_process)}):\n{files_text}")
            # Ajuster la taille du label en fonction du contenu
            self.drop_label.adjustSize()
    
    def log_message(self, message):
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
        self.log_text.append(f"[{timestamp}] {message}")
        # Faire défiler jusqu'au bas
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        QApplication.processEvents()  # Mettre à jour l'interface immédiatement
    
    def compress_pdfs(self):
        if not self.files_to_process:
            return
        
        # Désactiver le bouton pendant la compression
        self.compress_btn.setEnabled(False)
        
        # Créer un nouveau dossier de lot
        batch_dir = create_batch_folder()
        self.log_message(f"Début du traitement dans le dossier: {os.path.basename(batch_dir)}")
        
        # Traiter chaque fichier
        success_count = 0
        error_count = 0
        
        for i, input_path in enumerate(self.files_to_process, 1):
            try:
                self.log_message(f"Traitement du fichier {i}/{len(self.files_to_process)}: {os.path.basename(input_path)}")
                
                # Nom du fichier de sortie
                output_filename = f"compressed_{os.path.basename(input_path)}"
                output_path = os.path.join(batch_dir, output_filename)
                
                # Compression
                success, message = compress_pdf(
                    input_path,
                    output_path,
                    self.size_spinbox.value()
                )
                
                if success:
                    success_count += 1
                    self.log_message(f"✓ {message}")
                else:
                    error_count += 1
                    self.log_message(f"✗ {message}")
                
            except Exception as e:
                error_count += 1
                self.log_message(f"✗ Erreur lors du traitement de {os.path.basename(input_path)}: {str(e)}")
        
        # Résumé
        self.log_message(f"\nTraitement terminé:")
        self.log_message(f"- {success_count} fichier(s) compressé(s) avec succès")
        self.log_message(f"- {error_count} échec(s)")
        
        # Ouvrir le dossier de sortie
        try:
            if sys.platform == 'win32':
                os.startfile(batch_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', batch_dir])
            else:  # Linux
                subprocess.run(['xdg-open', batch_dir])
        except Exception as e:
            self.log_message(f"⚠ Impossible d'ouvrir le dossier: {str(e)}")
        
        # Réinitialiser
        self.files_to_process = []
        self.update_drop_label()
        self.compress_btn.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFCompressorGUI()
    window.show()
    sys.exit(app.exec_()) 