#!/usr/bin/env python3
"""
Knowledge Base Auto-Loader for YouTube Autopilot
מערכת טעינה אוטומטית של בסיס הידע למערכת ניהול YouTube

This system automatically loads the knowledge base every time you access the repository,
providing continuous context and memory for AI development sessions.
"""

import os
import sys
import json
import yaml
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class YouTubeKnowledgeLoader:
    """Auto-loader for the YouTube Autopilot knowledge base"""
    
    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        self.kb_path = self.repo_root / "knowledge_base" / ".agent_kb"
        self.cache_path = self.repo_root / ".knowledge_cache"
        self.status_file = self.cache_path / "loader_status.json"
        
        # Ensure cache directory exists
        self.cache_path.mkdir(exist_ok=True)
        
        self.knowledge_data = {
            "core_docs": {},
            "knowledge_cards": {},
            "manifest": {},
            "loaded_at": None,
            "version": "1.0.0",
            "project_type": "youtube_autopilot"
        }
    
    def setup_auto_loading(self) -> bool:
        """Set up automatic knowledge base loading for future sessions"""
        try:
            print("🎥 Setting up YouTube Autopilot Knowledge Base Auto-Loading...")
            
            # Create .bashrc hook for auto-loading
            bashrc_hook = f"""
# YouTube Autopilot - Knowledge Base Auto-Loader
if [ -f "{self.repo_root}/tools/knowledge_loader.py" ] && [ "$PWD" = "{self.repo_root}" ]; then
    echo "🎥 Loading YouTube Autopilot Knowledge Base..."
    python3 "{self.repo_root}/tools/knowledge_loader.py" --load --quiet
fi
"""
            
            # Add to .bashrc if not already present
            bashrc_path = Path.home() / ".bashrc"
            if bashrc_path.exists():
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                
                if "YouTube Autopilot - Knowledge Base Auto-Loader" not in content:
                    with open(bashrc_path, 'a') as f:
                        f.write(bashrc_hook)
                    print("✅ Added auto-loading hook to .bashrc")
                else:
                    print("✅ Auto-loading hook already exists in .bashrc")
            
            # Create project-specific activation script
            activation_script = self.repo_root / ".activate_knowledge.sh"
            with open(activation_script, 'w') as f:
                f.write(f"""#!/bin/bash
# YouTube Autopilot Knowledge Base Activation
echo "🎥 Activating YouTube Autopilot Knowledge Base..."
cd "{self.repo_root}"
python3 tools/knowledge_loader.py --load
echo "✅ Knowledge Base loaded and ready!"
""")
            
            activation_script.chmod(0o755)
            print(f"✅ Created activation script: {activation_script}")
            
            # Initial load
            self.load_knowledge_base()
            
            print("🎯 Setup complete! Knowledge base will auto-load when you access this repository.")
            print(f"💡 Manual activation: cd {self.repo_root} && python tools/knowledge_loader.py --load")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up auto-loading: {e}")
            return False
    
    def load_knowledge_base(self, quiet: bool = False) -> bool:
        """Load the complete knowledge base into memory"""
        try:
            if not quiet:
                print("🎥 Loading YouTube Autopilot Knowledge Base...")
            
            # Load manifest
            manifest_path = self.kb_path / "_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    self.knowledge_data["manifest"] = json.load(f)
                if not quiet:
                    print("✅ Loaded knowledge base manifest")
            
            # Load core documents
            core_docs_path = self.kb_path / "core_docs"
            if core_docs_path.exists():
                for doc_file in core_docs_path.glob("*.md"):
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.knowledge_data["core_docs"][doc_file.name] = {
                        "content": content,
                        "size": len(content),
                        "hash": hashlib.md5(content.encode()).hexdigest(),
                        "loaded_at": datetime.now().isoformat()
                    }
                if not quiet:
                    print(f"✅ Loaded {len(self.knowledge_data['core_docs'])} core documents")
            
            # Load knowledge cards
            cards_path = self.kb_path / "knowledge_cards"
            if cards_path.exists():
                for category_dir in cards_path.iterdir():
                    if category_dir.is_dir():
                        category_name = category_dir.name
                        self.knowledge_data["knowledge_cards"][category_name] = {}
                        
                        for card_file in category_dir.glob("*.yaml"):
                            with open(card_file, 'r', encoding='utf-8') as f:
                                content = yaml.safe_load(f)
                            self.knowledge_data["knowledge_cards"][category_name][card_file.stem] = {
                                "content": content,
                                "file": str(card_file),
                                "loaded_at": datetime.now().isoformat()
                            }
                
                total_cards = sum(len(cards) for cards in self.knowledge_data["knowledge_cards"].values())
                if not quiet:
                    print(f"✅ Loaded {total_cards} knowledge cards across {len(self.knowledge_data['knowledge_cards'])} categories")
            
            # Load project-specific data
            self._load_youtube_specific_data(quiet)
            
            # Update status
            self.knowledge_data["loaded_at"] = datetime.now().isoformat()
            self._save_status()
            
            if not quiet:
                print("🎯 YouTube Autopilot Knowledge Base loaded successfully!")
                self._print_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading knowledge base: {e}")
            return False
    
    def _load_youtube_specific_data(self, quiet: bool = False) -> None:
        """Load YouTube-specific project data"""
        try:
            # Load automation status
            automation_status_file = self.repo_root / "automation_status.json"
            if automation_status_file.exists():
                with open(automation_status_file, 'r') as f:
                    self.knowledge_data["automation_status"] = json.load(f)
                if not quiet:
                    print("✅ Loaded automation status")
            
            # Load automation schedule
            schedule_file = self.repo_root / "automation_schedule.json"
            if schedule_file.exists():
                with open(schedule_file, 'r') as f:
                    self.knowledge_data["automation_schedule"] = json.load(f)
                if not quiet:
                    print("✅ Loaded automation schedule")
            
            # Load maintenance reports
            maintenance_file = self.repo_root / "maintenance_report.md"
            if maintenance_file.exists():
                with open(maintenance_file, 'r', encoding='utf-8') as f:
                    self.knowledge_data["maintenance_report"] = f.read()
                if not quiet:
                    print("✅ Loaded maintenance report")
                    
        except Exception as e:
            if not quiet:
                print(f"⚠️ Warning: Could not load YouTube-specific data: {e}")
    
    def update_knowledge_base(self) -> bool:
        """Update knowledge base with latest changes"""
        try:
            print("🔄 Updating YouTube Autopilot Knowledge Base...")
            
            # Check for changes
            changes_detected = self._detect_changes()
            
            if changes_detected:
                print("📝 Changes detected, reloading knowledge base...")
                return self.load_knowledge_base()
            else:
                print("✅ Knowledge base is up to date")
                return True
                
        except Exception as e:
            print(f"❌ Error updating knowledge base: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current knowledge base status"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                return json.load(f)
        return {"status": "not_loaded"}
    
    def print_status(self) -> None:
        """Print current knowledge base status"""
        status = self.get_status()
        
        print("🎥 YouTube Autopilot Knowledge Base Status")
        print("=" * 50)
        
        if status.get("status") == "not_loaded":
            print("❌ Knowledge base not loaded")
            print("💡 Run: python tools/knowledge_loader.py --load")
            return
        
        print(f"✅ Status: {status.get('status', 'unknown')}")
        print(f"📅 Last loaded: {status.get('loaded_at', 'unknown')}")
        print(f"📚 Core documents: {status.get('core_docs_count', 0)}")
        print(f"🗂️ Knowledge cards: {status.get('knowledge_cards_count', 0)}")
        print(f"🏷️ Categories: {status.get('categories_count', 0)}")
        print(f"🎥 Project type: YouTube Autopilot")
        
        if status.get("categories"):
            print("\n📋 Knowledge Categories:")
            for category, count in status["categories"].items():
                print(f"   • {category}: {count} cards")
    
    def _detect_changes(self) -> bool:
        """Detect if knowledge base files have changed"""
        try:
            current_status = self.get_status()
            if not current_status.get("file_hashes"):
                return True
            
            # Check core documents
            core_docs_path = self.kb_path / "core_docs"
            if core_docs_path.exists():
                for doc_file in core_docs_path.glob("*.md"):
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    current_hash = hashlib.md5(content.encode()).hexdigest()
                    stored_hash = current_status["file_hashes"].get(str(doc_file))
                    
                    if current_hash != stored_hash:
                        return True
            
            # Check knowledge cards
            cards_path = self.kb_path / "knowledge_cards"
            if cards_path.exists():
                for card_file in cards_path.rglob("*.yaml"):
                    with open(card_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    current_hash = hashlib.md5(content.encode()).hexdigest()
                    stored_hash = current_status["file_hashes"].get(str(card_file))
                    
                    if current_hash != stored_hash:
                        return True
            
            # Check YouTube-specific files
            for file_path in ["automation_status.json", "automation_schedule.json", "maintenance_report.md"]:
                file_full_path = self.repo_root / file_path
                if file_full_path.exists():
                    with open(file_full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    current_hash = hashlib.md5(content.encode()).hexdigest()
                    stored_hash = current_status["file_hashes"].get(str(file_full_path))
                    
                    if current_hash != stored_hash:
                        return True
            
            return False
            
        except Exception:
            return True
    
    def _save_status(self) -> None:
        """Save current knowledge base status"""
        try:
            # Calculate file hashes
            file_hashes = {}
            
            # Core documents
            core_docs_path = self.kb_path / "core_docs"
            if core_docs_path.exists():
                for doc_file in core_docs_path.glob("*.md"):
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_hashes[str(doc_file)] = hashlib.md5(content.encode()).hexdigest()
            
            # Knowledge cards
            cards_path = self.kb_path / "knowledge_cards"
            if cards_path.exists():
                for card_file in cards_path.rglob("*.yaml"):
                    with open(card_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_hashes[str(card_file)] = hashlib.md5(content.encode()).hexdigest()
            
            # YouTube-specific files
            for file_path in ["automation_status.json", "automation_schedule.json", "maintenance_report.md"]:
                file_full_path = self.repo_root / file_path
                if file_full_path.exists():
                    with open(file_full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_hashes[str(file_full_path)] = hashlib.md5(content.encode()).hexdigest()
            
            # Prepare status data
            categories = {}
            for category, cards in self.knowledge_data["knowledge_cards"].items():
                categories[category] = len(cards)
            
            status_data = {
                "status": "loaded",
                "loaded_at": self.knowledge_data["loaded_at"],
                "version": self.knowledge_data["version"],
                "project_type": "youtube_autopilot",
                "core_docs_count": len(self.knowledge_data["core_docs"]),
                "knowledge_cards_count": sum(len(cards) for cards in self.knowledge_data["knowledge_cards"].values()),
                "categories_count": len(self.knowledge_data["knowledge_cards"]),
                "categories": categories,
                "file_hashes": file_hashes,
                "repo_root": str(self.repo_root),
                "kb_path": str(self.kb_path)
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Warning: Could not save status: {e}")
    
    def _print_summary(self) -> None:
        """Print knowledge base loading summary"""
        print("\n📊 YouTube Autopilot Knowledge Base Summary:")
        print(f"   📚 Core Documents: {len(self.knowledge_data['core_docs'])}")
        
        for doc_name, doc_data in self.knowledge_data["core_docs"].items():
            print(f"      • {doc_name} ({doc_data['size']} chars)")
        
        print(f"   🗂️ Knowledge Categories: {len(self.knowledge_data['knowledge_cards'])}")
        
        for category, cards in self.knowledge_data["knowledge_cards"].items():
            print(f"      • {category}: {len(cards)} cards")
            for card_name in cards.keys():
                print(f"        - {card_name}")
        
        # YouTube-specific data
        if "automation_status" in self.knowledge_data:
            print(f"   🤖 Automation Status: Loaded")
        if "automation_schedule" in self.knowledge_data:
            print(f"   📅 Automation Schedule: Loaded")
        if "maintenance_report" in self.knowledge_data:
            print(f"   🔧 Maintenance Report: Loaded")
        
        print(f"\n🎯 Total Knowledge Items: {len(self.knowledge_data['core_docs']) + sum(len(cards) for cards in self.knowledge_data['knowledge_cards'].values())}")

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="YouTube Autopilot Knowledge Base Auto-Loader")
    parser.add_argument("--setup", action="store_true", help="Set up automatic knowledge base loading")
    parser.add_argument("--load", action="store_true", help="Load knowledge base")
    parser.add_argument("--update", action="store_true", help="Update knowledge base")
    parser.add_argument("--status", action="store_true", help="Show knowledge base status")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (minimal output)")
    parser.add_argument("--repo-root", help="Repository root path (auto-detected if not provided)")
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = YouTubeKnowledgeLoader(args.repo_root)
    
    # Execute requested action
    if args.setup:
        success = loader.setup_auto_loading()
        sys.exit(0 if success else 1)
    elif args.load:
        success = loader.load_knowledge_base(quiet=args.quiet)
        sys.exit(0 if success else 1)
    elif args.update:
        success = loader.update_knowledge_base()
        sys.exit(0 if success else 1)
    elif args.status:
        loader.print_status()
        sys.exit(0)
    else:
        # Default: show status and offer to load
        loader.print_status()
        status = loader.get_status()
        
        if status.get("status") != "loaded":
            print("\n💡 To load the knowledge base, run:")
            print("   python tools/knowledge_loader.py --load")
            print("\n💡 To set up auto-loading, run:")
            print("   python tools/knowledge_loader.py --setup")

if __name__ == "__main__":
    main()
