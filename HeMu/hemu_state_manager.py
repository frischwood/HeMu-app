#!/usr/bin/env python3
"""
HeMu State Manager - Tracks processed data and avoids recomputation
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd

class HeMuStateManager:
    """Manages HeMu processing state to avoid unnecessary recomputations"""
    
    def __init__(self, domain="CH", state_file=None):
        self.domain = domain
        self.hemu_root = Path(__file__).parent
        self.state_file = state_file or self.hemu_root / f"state_{domain}.json"
        self.state = self._load_state()
        
    def _load_state(self):
        """Load processing state from file"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "domain_config": {},
            "static_data": {},
            "processed_dates": {},
            "last_update": None
        }
    
    def _save_state(self):
        """Save processing state to file"""
        self.state["last_update"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _compute_domain_hash(self, matcher_path, horayzon_path):
        """Compute hash of domain configuration"""
        domain_info = {
            "matcher_exists": os.path.exists(matcher_path),
            "horayzon_exists": os.path.exists(horayzon_path),
            "matcher_mtime": os.path.getmtime(matcher_path) if os.path.exists(matcher_path) else 0,
            "horayzon_mtime": os.path.getmtime(horayzon_path) if os.path.exists(horayzon_path) else 0
        }
        return hashlib.md5(str(domain_info).encode()).hexdigest()
    
    def is_static_data_valid(self, matcher_path, horayzon_path):
        """Check if static data (domain, topography) needs recomputation"""
        current_hash = self._compute_domain_hash(matcher_path, horayzon_path)
        stored_hash = self.state["domain_config"].get("hash")
        
        if stored_hash != current_hash:
            print(f"🔄 Domain configuration changed, static data needs update")
            self.state["domain_config"]["hash"] = current_hash
            return False
        
        # Check if static data files exist
        static_vars = ["SRTMGL3_DEM", "slope", "aspectCos", "aspectSin"]
        for var in static_vars:
            var_path = self.hemu_root / f"runs/{self.domain}/static/{var}/{var}.nc"
            if not var_path.exists():
                print(f"⚠️  Static data missing: {var}")
                return False
        
        print(f"✅ Static data is up-to-date for domain {self.domain}")
        return True
    
    def is_date_range_processed(self, start_date, end_date, required_vars=None):
        """Check if a date range has been fully processed"""
        if required_vars is None:
            required_vars = ["HRV", "SZA", "SAA"] + ["SRTMGL3_DEM", "slope", "aspectCos", "aspectSin"]
        
        date_key = f"{start_date.strftime('%Y%m%d%H%M')}-{end_date.strftime('%Y%m%d%H%M')}"
        
        if date_key not in self.state["processed_dates"]:
            return False
        
        processed_info = self.state["processed_dates"][date_key]
        
        # Check if all required variables exist
        for var in required_vars:
            var_path = self.hemu_root / f"runs/{self.domain}/{date_key}/{var}/{var}.nc"
            if not var_path.exists():
                print(f"⚠️  Missing data for {date_key}: {var}")
                return False
        
        print(f"✅ Date range {date_key} already processed")
        return True
    
    def mark_date_range_processed(self, start_date, end_date, variables):
        """Mark a date range as processed"""
        date_key = f"{start_date.strftime('%Y%m%d%H%M')}-{end_date.strftime('%Y%m%d%H%M')}"
        self.state["processed_dates"][date_key] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "variables": variables,
            "processed_at": datetime.now().isoformat()
        }
        self._save_state()
    
    def get_missing_date_ranges(self, start_date, end_date, chunk_days=7):
        """Get list of date ranges that need processing"""
        missing_ranges = []
        current_date = start_date
        
        while current_date < end_date:
            chunk_end = min(current_date + pd.Timedelta(days=chunk_days), end_date)
            
            if not self.is_date_range_processed(current_date, chunk_end):
                missing_ranges.append((current_date, chunk_end))
            
            current_date = chunk_end
        
        return missing_ranges
    
    def cleanup_old_data(self, keep_days=30):
        """Remove old processed data to save space"""
        cutoff_date = datetime.now() - pd.Timedelta(days=keep_days)
        
        to_remove = []
        for date_key, info in self.state["processed_dates"].items():
            processed_at = pd.to_datetime(info["processed_at"])
            if processed_at < cutoff_date:
                # Remove data directory
                data_dir = self.hemu_root / f"runs/{self.domain}/{date_key}"
                if data_dir.exists():
                    import shutil
                    shutil.rmtree(data_dir)
                    print(f"🗑️  Removed old data: {date_key}")
                to_remove.append(date_key)
        
        for key in to_remove:
            del self.state["processed_dates"][key]
        
        self._save_state()

if __name__ == "__main__":
    # Test the state manager
    state_mgr = HeMuStateManager("CH")
    print(f"State file: {state_mgr.state_file}")
    print(f"Current state: {state_mgr.state}")
