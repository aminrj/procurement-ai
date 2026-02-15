"""
CLI utility for managing the procurement knowledge base

Provides commands to:
- Add example documents
- Import/export knowledge base
- Search and view contents
- Get statistics
"""

import asyncio
import argparse
import json
from pathlib import Path
import sys
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from procurement_ai.rag import KnowledgeBase


DEFAULT_KB_PATH = "./data/knowledge_base"


async def add_example(kb: KnowledgeBase, args):
    """Add a single example to knowledge base"""
    metadata = {}
    if args.year:
        metadata['year'] = args.year
    if args.success_rate:
        metadata['success_rate'] = args.success_rate
    
    doc_id = await kb.add_example(
        content=args.content,
        category=args.category,
        title=args.title,
        metadata=metadata if metadata else None
    )
    
    print(f"✅ Added example: {doc_id}")
    print(f"   Title: {args.title}")
    print(f"   Category: {args.category}")
    print(f"   Content: {len(args.content)} characters")


async def import_from_file(kb: KnowledgeBase, args):
    """Import knowledge base from JSON file"""
    count = await kb.import_from_json(args.file)
    print(f"✅ Imported {count} documents from {args.file}")


async def export_to_file(kb: KnowledgeBase, args):
    """Export knowledge base to JSON file"""
    await kb.export_to_json(args.file)
    print(f"✅ Exported knowledge base to {args.file}")


async def show_stats(kb: KnowledgeBase, args):
    """Show knowledge base statistics"""
    stats = kb.get_statistics()
    
    print(f"\n📊 Knowledge Base Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    
    if stats['total_documents'] > 0:
        print(f"\n   Categories:")
        for cat, count in stats['categories'].items():
            print(f"      - {cat}: {count}")


async def search_kb(kb: KnowledgeBase, args):
    """Search knowledge base"""
    results = await kb.search(
        query=args.query,
        k=args.limit,
        min_similarity=args.min_similarity,
        category=args.category if hasattr(args, 'category') and args.category else None
    )
    
    print(f"\n🔍 Search: '{args.query}'")
    print(f"   Found {len(results)} matches\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.metadata.get('title', 'Untitled')} (similarity: {result.similarity:.3f})")
        print(f"   Category: {result.metadata.get('category', 'unknown')}")
        if args.show_content:
            print(f"   Content preview: {result.content[:150]}...")
        print()


async def list_documents(kb: KnowledgeBase, args):
    """List all documents in knowledge base"""
    all_docs = kb.vector_store.get_all_documents()
    
    if not all_docs['ids']:
        print("📦 Knowledge base is empty")
        return
    
    print(f"\n📄 Documents in knowledge base ({len(all_docs['ids'])} total):\n")
    
    for i, (doc_id, metadata) in enumerate(zip(all_docs['ids'], all_docs['metadatas']), 1):
        title = metadata.get  ('title', 'Untitled')
        category = metadata.get('category', 'unknown')
        print(f"{i}. [{category}] {title}")
        if args.verbose:
            print(f"   ID: {doc_id}")
            for key, value in metadata.items():
                if key not in ['title', 'category']:
                    print(f"   {key}: {value}")
        print()


async def main():
    parser = argparse.ArgumentParser(
        description="Manage procurement AI knowledge base"
    )
    
    parser.add_argument(
        '--kb-path',
        default=DEFAULT_KB_PATH,
        help=f"Path to knowledge base (default: {DEFAULT_KB_PATH})"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add example command
    add_parser = subparsers.add_parser('add', help='Add an example document')
    add_parser.add_argument('--content', required=True, help='Document content (or @filename to read from file)')
    add_parser.add_argument('--category', required=True, help='Category (e.g., cybersecurity, ai, software)')
    add_parser.add_argument('--title', required=True, help='Document title')
    add_parser.add_argument('--year', type=int, help='Year')
    add_parser.add_argument('--success-rate', type=float, help='Success rate (0.0-1.0)')
    add_parser.set_defaults(func=add_example)
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import from JSON file')
    import_parser.add_argument('file', help='JSON file path')
    import_parser.set_defaults(func=import_from_file)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export to JSON file')
    export_parser.add_argument('file', help='JSON file path')
    export_parser.set_defaults(func=export_to_file)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=show_stats)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search knowledge base')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', '-n', type=int, default=5, help='Number of results (default: 5)')
    search_parser.add_argument('--min-similarity', '-s', type=float, default=0.5, help='Min similarity (default: 0.5)')
    search_parser.add_argument('--category', '-c', help='Filter by category')
    search_parser.add_argument('--show-content', action='store_true', help='Show content preview')
    search_parser.set_defaults(func=search_kb)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all documents')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed info')
    list_parser.set_defaults(func=list_documents)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize knowledge base
    kb = KnowledgeBase(persist_directory=args.kb_path)
    
    # Handle file reading for add command
    if args.command == 'add' and args.content.startswith('@'):
        filepath = args.content[1:]
        with open(filepath, 'r') as f:
            args.content = f.read()
    
    # Run command
    await args.func(kb, args)


if __name__ == '__main__':
    asyncio.run(main())
