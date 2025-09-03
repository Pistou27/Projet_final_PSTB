"""
Interface en ligne de commande pour le pipeline RAG
"""

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .pipeline import RAGPipeline
from .utils import Logger

class RAGCLI:
    """Interface CLI pour le pipeline RAG"""
    
    def __init__(self, collection_name: str = None):
        """Initialise le CLI avec un pipeline RAG"""
        self.pipeline = RAGPipeline(collection_name=collection_name)
        Logger.info(f"🚀 CLI RAG démarré")
    
    def ingest_command(self, doc_path: str, doc_id: str = None):
        """Commande d'ingestion d'un document"""
        doc_path = Path(doc_path)
        
        if not doc_path.exists():
            Logger.error(f"❌ Fichier non trouvé: {doc_path}")
            return
        
        if not doc_id:
            doc_id = doc_path.stem
        
        Logger.info(f"📥 Ingestion: {doc_path} -> {doc_id}")
        
        stats = self.pipeline.ingest_document(doc_path, doc_id)
        
        if stats.success:
            Logger.success(f"✅ Ingestion réussie:")
            Logger.info(f"   - Document: {stats.doc_id}")
            Logger.info(f"   - Chunks: {stats.chunks_created}")
            Logger.info(f"   - Pages: {stats.pages_processed}")
        else:
            Logger.error(f"❌ Ingestion échouée: {stats.error}")
    
    def search_command(self, query: str, doc_ids: Optional[List[str]] = None, 
                      limit: int = 5, no_rerank: bool = False):
        """Commande de recherche"""
        Logger.info(f"🔍 Recherche: '{query}'")
        
        response = self.pipeline.search(
            query=query,
            doc_ids=doc_ids,
            limit=limit,
            use_reranking=not no_rerank
        )
        
        # Afficher la réponse
        print(f"\n{'='*60}")
        print(f"QUESTION: {query}")
        print(f"{'='*60}")
        
        if not response.success:
            print(f"❌ ERREUR: {response.error_message}")
            return
        
        print(f"\n📝 RÉPONSE:")
        print(f"{response.answer}")
        
        if response.citations:
            print(f"\n📚 CITATIONS:")
            for i, citation in enumerate(response.citations, 1):
                if isinstance(citation, dict):
                    print(f"  {i}. {citation.get('doc_id', 'N/A')} (page {citation.get('page', 'N/A')})")
                else:
                    print(f"  {i}. {citation}")
        
        if response.claims:
            print(f"\n🎯 AFFIRMATIONS DÉTAILLÉES:")
            for i, claim in enumerate(response.claims, 1):
                if isinstance(claim, dict):
                    print(f"  {i}. {claim.get('text', str(claim))}")
                    if claim.get('citations'):
                        for j, citation in enumerate(claim['citations'], 1):
                            if isinstance(citation, dict):
                                print(f"      → {citation.get('doc_id', 'N/A')} (page {citation.get('page', 'N/A')})")
                else:
                    print(f"  {i}. {claim}")
        
        print(f"\n📊 MÉTADONNÉES:")
        print(f"  - Confiance: {response.confidence:.2f}")
        print(f"  - Temps: {response.processing_time:.2f}s")
        
        print(f"{'='*60}\n")
    
    def list_command(self):
        """Liste tous les documents de la collection"""
        Logger.info("📋 Liste des documents")
        
        try:
            documents = self.pipeline.list_documents()
            
            if not documents:
                Logger.info("Aucun document dans la collection")
                return
            
            print(f"\n📚 DOCUMENTS DANS LA COLLECTION:")
            print(f"{'='*60}")
            
            for doc in documents:
                print(f"📄 {doc.doc_id}")
                print(f"   - Chunks: {doc.chunks_count}")
                print(f"   - Pages: {doc.pages_count} ({doc.pages_range})")
                print(f"   - Créé: {doc.created_at}")
                print()
            
            print(f"Total: {len(documents)} documents")
            print(f"{'='*60}\n")
            
        except Exception as e:
            Logger.error(f"❌ Erreur liste documents: {e}")
    
    def info_command(self):
        """Affiche les informations de la collection"""
        Logger.info("ℹ️  Informations de la collection")
        
        try:
            info = self.pipeline.get_collection_info()
            health = self.pipeline.health_check()
            
            print(f"\n🔧 INFORMATIONS SYSTÈME:")
            print(f"{'='*60}")
            
            print(f"📊 Collection Qdrant:")
            print(f"   - Nom: {info.get('collection_name', 'N/A')}")
            print(f"   - Points: {info.get('points_count', 0)}")
            print(f"   - Statut: {info.get('status', 'N/A')}")
            
            print(f"\n🏥 Santé des composants:")
            for component, status in health.items():
                icon = "✅" if status else "❌"
                print(f"   {icon} {component.replace('_', ' ').title()}")
            
            print(f"{'='*60}\n")
            
        except Exception as e:
            Logger.error(f"❌ Erreur informations: {e}")
    
    def delete_command(self, doc_id: str):
        """Supprime un document de la collection"""
        Logger.info(f"🗑️  Suppression: {doc_id}")
        
        success = self.pipeline.delete_document(doc_id)
        
        if success:
            Logger.success(f"✅ Document {doc_id} supprimé")
        else:
            Logger.error(f"❌ Échec suppression {doc_id}")
    
    def clear_command(self, confirm: bool = False):
        """Vide complètement la collection"""
        if not confirm:
            Logger.warning("⚠️  Cette action va supprimer TOUS les documents!")
            response = input("Confirmer? (oui/non): ").lower()
            if response not in ['oui', 'o', 'yes', 'y']:
                Logger.info("Opération annulée")
                return
        
        Logger.info("🧹 Vidage de la collection...")
        
        success = self.pipeline.clear_collection()
        
        if success:
            Logger.success("✅ Collection vidée")
        else:
            Logger.error("❌ Échec vidage collection")

def main():
    """Point d'entrée principal du CLI"""
    parser = argparse.ArgumentParser(
        description="RAG Pipeline CLI - Recherche intelligente dans vos documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Ingérer un document
  python -m rag_qdrant.cli ingest data/splendor.pdf --doc-id splendor

  # Rechercher dans tous les documents
  python -m rag_qdrant.cli search "Comment jouer à Splendor?"

  # Rechercher dans des documents spécifiques
  python -m rag_qdrant.cli search "Règles de terraformation" --docs terraforming-mars

  # Lister les documents
  python -m rag_qdrant.cli list

  # Informations système
  python -m rag_qdrant.cli info

  # Supprimer un document
  python -m rag_qdrant.cli delete splendor

  # Vider la collection
  python -m rag_qdrant.cli clear
        """
    )
    
    parser.add_argument(
        "--collection",
        default=None,
        help="Nom de la collection Qdrant (défaut: config)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")
    
    # Commande ingest
    ingest_parser = subparsers.add_parser("ingest", help="Ingérer un document PDF")
    ingest_parser.add_argument("doc_path", help="Chemin vers le document PDF")
    ingest_parser.add_argument("--doc-id", help="ID du document (défaut: nom du fichier)")
    
    # Commande search
    search_parser = subparsers.add_parser("search", help="Rechercher dans les documents")
    search_parser.add_argument("query", help="Question à poser")
    search_parser.add_argument("--docs", nargs="*", help="IDs des documents à filtrer")
    search_parser.add_argument("--limit", type=int, default=5, help="Nombre de résultats max")
    search_parser.add_argument("--no-rerank", action="store_true", help="Désactiver le reranking")
    
    # Commande list
    subparsers.add_parser("list", help="Lister tous les documents")
    
    # Commande info
    subparsers.add_parser("info", help="Informations système")
    
    # Commande delete
    delete_parser = subparsers.add_parser("delete", help="Supprimer un document")
    delete_parser.add_argument("doc_id", help="ID du document à supprimer")
    
    # Commande clear
    clear_parser = subparsers.add_parser("clear", help="Vider la collection")
    clear_parser.add_argument("--yes", action="store_true", help="Confirmer automatiquement")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialiser le CLI
    cli = RAGCLI(collection_name=args.collection)
    
    # Exécuter la commande
    try:
        if args.command == "ingest":
            cli.ingest_command(args.doc_path, args.doc_id)
        
        elif args.command == "search":
            cli.search_command(args.query, args.docs, args.limit, args.no_rerank)
        
        elif args.command == "list":
            cli.list_command()
        
        elif args.command == "info":
            cli.info_command()
        
        elif args.command == "delete":
            cli.delete_command(args.doc_id)
        
        elif args.command == "clear":
            cli.clear_command(args.yes)
        
    except KeyboardInterrupt:
        Logger.info("\n👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        Logger.error(f"❌ Erreur CLI: {e}")

if __name__ == "__main__":
    main()
