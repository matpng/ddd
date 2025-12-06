#!/usr/bin/env python3
"""
Discovery Manager
Handles storage, retrieval, and indexing of autonomous discoveries.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import shutil

logger = logging.getLogger(__name__)


class DiscoveryManager:
    """Manages autonomous discovery storage and retrieval."""
    
    def __init__(self, base_dir: str = 'autonomous_discoveries'):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        self.index_file = self.base_dir / 'index.json'
        self.latest_file = self.base_dir / 'latest.json'
        
        # Initialize index if it doesn't exist
        if not self.index_file.exists():
            self._save_json(self.index_file, {
                'total_discoveries': 0,
                'discoveries': [],
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            })
    
    def save_discovery(self, discovery_data: Dict[str, Any], discovery_type: str) -> str:
        """
        Save a discovery and update indexes.
        
        Args:
            discovery_data: Discovery results from autonomous daemon
            discovery_type: Type of discovery (angle_sweep, multi_axis, etc.)
        
        Returns:
            Discovery ID
        """
        try:
            # Create date-based directory
            today = datetime.utcnow().strftime('%Y-%m-%d')
            date_dir = self.base_dir / today
            date_dir.mkdir(exist_ok=True)
            
            # Generate unique ID
            timestamp = datetime.utcnow().strftime('%H%M%S')
            discovery_id = f"{discovery_type}_{timestamp}"
            
            # Add metadata
            discovery_record = {
                'id': discovery_id,
                'type': discovery_type,
                'timestamp': datetime.utcnow().isoformat(),
                'date': today,
                'data': discovery_data
            }
            
            # Save JSON file
            json_file = date_dir / f"{discovery_id}.json"
            self._save_json(json_file, discovery_record)
            
            # Update index
            self._update_index(discovery_record)
            
            # Update latest
            self._save_json(self.latest_file, discovery_record)
            
            logger.info(f"Saved discovery: {discovery_id}")
            return discovery_id
            
        except Exception as e:
            logger.error(f"Error saving discovery: {e}", exc_info=True)
            raise
    
    def get_latest(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get latest N discoveries."""
        try:
            index = self._load_json(self.index_file)
            discoveries = index.get('discoveries', [])
            # Sort by timestamp descending
            discoveries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return discoveries[:count]
        except Exception as e:
            logger.error(f"Error getting latest discoveries: {e}")
            return []
    
    def get_all(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get all discoveries with pagination."""
        try:
            index = self._load_json(self.index_file)
            discoveries = index.get('discoveries', [])
            discoveries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            total = len(discoveries)
            paginated = discoveries[offset:offset + limit]
            
            return {
                'total': total,
                'limit': limit,
                'offset': offset,
                'discoveries': paginated
            }
        except Exception as e:
            logger.error(f"Error getting all discoveries: {e}")
            return {'total': 0, 'discoveries': []}
    
    def get_by_id(self, discovery_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific discovery by ID."""
        try:
            # Search in index first
            index = self._load_json(self.index_file)
            for record in index.get('discoveries', []):
                if record.get('id') == discovery_id:
                    # Load full data from file
                    date = record.get('date')
                    file_path = self.base_dir / date / f"{discovery_id}.json"
                    if file_path.exists():
                        return self._load_json(file_path)
                    return record
            return None
        except Exception as e:
            logger.error(f"Error getting discovery {discovery_id}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        try:
            index = self._load_json(self.index_file)
            discoveries = index.get('discoveries', [])
            
            # Count by type
            type_counts = {}
            for disc in discoveries:
                disc_type = disc.get('type', 'unknown')
                type_counts[disc_type] = type_counts.get(disc_type, 0) + 1
            
            # Count by date
            date_counts = {}
            for disc in discoveries:
                date = disc.get('date', 'unknown')
                date_counts[date] = date_counts.get(date, 0) + 1
            
            # Get latest
            latest = None
            if discoveries:
                sorted_discoveries = sorted(discoveries, key=lambda x: x.get('timestamp', ''), reverse=True)
                latest = sorted_discoveries[0] if sorted_discoveries else None
            
            return {
                'total_discoveries': index.get('total_discoveries', 0),
                'discoveries_by_type': type_counts,
                'discoveries_by_date': date_counts,
                'latest_discovery': latest,
                'last_updated': index.get('last_updated'),
                'created_at': index.get('created_at')
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'total_discoveries': 0}
    
    def search(self, query: str = '', discovery_type: str = '', date: str = '') -> List[Dict[str, Any]]:
        """Search discoveries by various criteria."""
        try:
            index = self._load_json(self.index_file)
            discoveries = index.get('discoveries', [])
            results = discoveries
            
            # Filter by type
            if discovery_type:
                results = [d for d in results if d.get('type') == discovery_type]
            
            # Filter by date
            if date:
                results = [d for d in results if d.get('date') == date]
            
            # Filter by query (search in ID and type)
            if query:
                query_lower = query.lower()
                results = [d for d in results if 
                          query_lower in d.get('id', '').lower() or 
                          query_lower in d.get('type', '').lower()]
            
            # Sort by timestamp descending
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return results
        except Exception as e:
            logger.error(f"Error searching discoveries: {e}")
            return []
    
    def _update_index(self, discovery_record: Dict[str, Any]):
        """Update the main index with new discovery."""
        try:
            index = self._load_json(self.index_file)
            
            # Add summary to index (not full data)
            summary = {
                'id': discovery_record['id'],
                'type': discovery_record['type'],
                'timestamp': discovery_record['timestamp'],
                'date': discovery_record['date'],
                'summary': discovery_record['data'].get('summary', {})
            }
            
            discoveries = index.get('discoveries', [])
            discoveries.append(summary)
            
            index['discoveries'] = discoveries
            index['total_discoveries'] = len(discoveries)
            index['last_updated'] = datetime.utcnow().isoformat()
            
            self._save_json(self.index_file, index)
            
        except Exception as e:
            logger.error(f"Error updating index: {e}", exc_info=True)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON from file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """Save data as JSON."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            raise
    
    def cleanup_old_discoveries(self, days: int = 30):
        """Remove discoveries older than specified days."""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            for date_dir in self.base_dir.iterdir():
                if date_dir.is_dir() and date_dir.name < cutoff_date:
                    logger.info(f"Removing old discoveries from {date_dir.name}")
                    shutil.rmtree(date_dir)
            
            # Rebuild index after cleanup
            self._rebuild_index()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _rebuild_index(self):
        """Rebuild index from all discovery files."""
        try:
            discoveries = []
            
            for date_dir in sorted(self.base_dir.iterdir()):
                if not date_dir.is_dir():
                    continue
                
                for json_file in date_dir.glob('*.json'):
                    try:
                        data = self._load_json(json_file)
                        summary = {
                            'id': data['id'],
                            'type': data['type'],
                            'timestamp': data['timestamp'],
                            'date': data['date'],
                            'summary': data['data'].get('summary', {})
                        }
                        discoveries.append(summary)
                    except Exception as e:
                        logger.error(f"Error processing {json_file}: {e}")
            
            index = {
                'total_discoveries': len(discoveries),
                'discoveries': discoveries,
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            self._save_json(self.index_file, index)
            logger.info(f"Rebuilt index with {len(discoveries)} discoveries")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
