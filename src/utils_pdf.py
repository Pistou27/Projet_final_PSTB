"""
Utilitaires pour l'extraction des numéros de page des PDFs
"""
import PyPDF2
from typing import Dict, List, Tuple
import os

class PDFPageExtractor:
    """Extracteur de pages PDF avec numérotation"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.page_contents = {}
        self._extract_pages()
    
    def _extract_pages(self):
        """Extraire le contenu de chaque page avec numérotation"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text.strip():  # Ignorer les pages vides
                            self.page_contents[page_num] = text.strip()
                    except Exception as e:
                        print(f"Erreur lors de l'extraction de la page {page_num}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Erreur lors de l'ouverture du PDF {self.pdf_path}: {e}")
    
    def get_page_for_text(self, search_text: str, min_length: int = 50) -> List[int]:
        """
        Trouver les pages contenant un texte donné
        
        Args:
            search_text: Texte à rechercher
            min_length: Longueur minimale du texte pour être considéré
            
        Returns:
            Liste des numéros de page contenant le texte
        """
        if len(search_text) < min_length:
            return []
            
        matching_pages = []
        search_text_lower = search_text.lower()
        
        for page_num, page_text in self.page_contents.items():
            if search_text_lower in page_text.lower():
                matching_pages.append(page_num)
        
        return matching_pages
    
    def get_all_pages_content(self) -> List[Tuple[int, str]]:
        """
        Retourner tout le contenu avec numéros de page
        
        Returns:
            Liste de tuples (numéro_page, contenu)
        """
        return [(page_num, content) for page_num, content in self.page_contents.items()]
    
    def get_page_content(self, page_num: int) -> str:
        """Retourner le contenu d'une page spécifique"""
        return self.page_contents.get(page_num, "")
    
    def get_total_pages(self) -> int:
        """Retourner le nombre total de pages"""
        return len(self.page_contents)

def create_page_metadata(pdf_path: str, chunk_text: str) -> Dict:
    """
    Créer des métadonnées avec numéro de page pour un chunk de texte
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        chunk_text: Texte du chunk
        
    Returns:
        Dictionnaire avec métadonnées incluant les pages
    """
    filename = os.path.basename(pdf_path)
    
    try:
        extractor = PDFPageExtractor(pdf_path)
        pages = extractor.get_page_for_text(chunk_text)
        
        metadata = {
            "source": filename,
            "file_path": pdf_path,
            "file_type": "pdf",
            "pages": pages,
            "page_range": f"p.{min(pages)}-{max(pages)}" if pages else "page inconnue"
        }
        
    except Exception as e:
        print(f"Erreur lors de l'extraction des métadonnées pour {filename}: {e}")
        metadata = {
            "source": filename,
            "file_path": pdf_path,
            "file_type": "pdf",
            "pages": [],
            "page_range": "page inconnue"
        }
    
    return metadata

def format_source_with_pages(metadata: Dict) -> str:
    """
    Formater l'information de source avec les pages
    
    Args:
        metadata: Métadonnées du document
        
    Returns:
        Chaîne formatée avec source et pages
    """
    source = metadata.get("source", "Source inconnue")
    pages = metadata.get("pages", [])
    
    if pages:
        if len(pages) == 1:
            return f"{source} (page {pages[0]})"
        else:
            pages_str = ", ".join(map(str, sorted(pages)))
            return f"{source} (pages {pages_str})"
    else:
        return f"{source} (page non déterminée)"
