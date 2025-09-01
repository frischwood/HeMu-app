#!/usr/bin/env python3
"""
Smart HeMu Processor - Automated satellite data processing with caching
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Add HeMu scripts to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from hemu_state_manager import HeMuStateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SmartHeMuProcessor:
    """Automated HeMu processing with intelligent caching"""
    
    def __init__(self, domain="CH", lookback_hours=24):
        self.domain = domain
        self.lookback_hours = lookback_hours
        self.hemu_root = Path(__file__).parent
        self.state_manager = HeMuStateManager(domain)
        
        # Default configuration for Switzerland
        self.config = self._get_default_config()
        
    def _get_default_config(self):
        """Get default configuration for Switzerland"""
        return {
            "simuDomain": self.domain,
            "satGen": "MSG",  # Meteosat Second Generation
            "szaFilterVal": 80,  # Daylight filtering
            "eumdacApiCreds": {
                "key": "rBk6COGAX5IdVxWrBV7kYlVT3Jga",
                "secret": "DNv7TjL1WRpd2y8g8XVZ82ImJJ8a"
            },
            "inferConfigPath": "configs/TSViT.yaml",
            "statsPath": "data/Helio/stats/stats_NC_2015_2020_sza80.csv",
            "batchSize": 1,
            "local_device_ids": 0,  # GPU if available
            "root": "runs"
        }
    
    def check_dependencies(self):
        """Check if all required dependencies are available"""
        missing_deps = []
        
        # Check domain matcher
        matcher_path = self.hemu_root / f"data/static/domainMatcher/{self.domain}"
        if not matcher_path.exists() or not any(matcher_path.glob("*.nc")):
            missing_deps.append(f"Domain matcher for {self.domain}")
        
        # Check HORAYZON data
        horayzon_path = self.hemu_root / f"data/static/horayzon/{self.domain}"
        if not horayzon_path.exists() or not any(horayzon_path.glob("*.nc")):
            missing_deps.append(f"HORAYZON data for {self.domain}")
        
        # Check model config
        config_path = self.hemu_root / self.config["inferConfigPath"]
        if not config_path.exists():
            missing_deps.append("Model configuration (TSViT.yaml)")
        
        # Check statistics file
        stats_path = self.hemu_root / self.config["statsPath"]
        if not stats_path.exists():
            missing_deps.append("Normalization statistics file")
        
        if missing_deps:
            logger.error(f"Missing dependencies: {missing_deps}")
            return False
        
        logger.info("✅ All dependencies available")
        return True
    
    def get_processing_dates(self):
        """Get date range for processing (recent satellite data)"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=self.lookback_hours)
        
        # Round to nearest hour
        start_date = start_date.replace(minute=0, second=0, microsecond=0)
        end_date = end_date.replace(minute=0, second=0, microsecond=0)
        
        return start_date, end_date
    
    def setup_static_data(self):
        """Setup static data (topography, domain) if needed"""
        matcher_path = self.hemu_root / f"data/static/domainMatcher/{self.domain}"
        horayzon_path = self.hemu_root / f"data/static/horayzon/{self.domain}"
        
        if not self.state_manager.is_static_data_valid(str(matcher_path), str(horayzon_path)):
            logger.info("🔄 Setting up static data...")
            
            try:
                # Import HeMu components
                from HeMu import topoData
                
                # Create temporary simulation directory for static data
                static_dir = self.hemu_root / f"runs/{self.domain}/static"
                static_dir.mkdir(parents=True, exist_ok=True)
                
                # Process topographic data
                topo_processor = topoData(str(static_dir), str(horayzon_path))
                topo_processor.compute()
                
                logger.info("✅ Static data setup complete")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to setup static data: {e}")
                return False
        
        return True
    
    def process_satellite_data(self, start_date, end_date):
        """Process satellite data for given date range"""
        logger.info(f"🛰️  Processing satellite data: {start_date} to {end_date}")
        
        try:
            # Import HeMu model
            from HeMu import Model
            
            # Update config with dates
            config = self.config.copy()
            config["start"] = start_date
            config["end"] = end_date
            
            # Initialize HeMu model
            emulator = Model(config)
            
            # Process data (satellite + solar angles + topography)
            data_start_time = time.time()
            emulator.getInputData()
            logger.info(f"⏱️  Data preprocessing: {time.time() - data_start_time:.1f}s")
            
            # Run inference
            infer_start_time = time.time()
            emulator.infer()
            logger.info(f"⏱️  Inference: {time.time() - infer_start_time:.1f}s")
            
            # Mark as processed
            processed_vars = ["HRV", "SZA", "SAA", "SRTMGL3_DEM", "slope", "aspectCos", "aspectSin"]
            self.state_manager.mark_date_range_processed(start_date, end_date, processed_vars)
            
            logger.info("✅ Satellite data processing complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Satellite data processing failed: {e}")
            return False
    
    def convert_to_app_format(self, start_date, end_date):
        """Convert HeMu output to app-compatible COG format"""
        logger.info("🔄 Converting HeMu output to COG format...")
        
        try:
            # Import conversion utilities from main app
            sys.path.append(str(Path(__file__).parent.parent / "app"))
            from convert import convert_netcdf_to_cog
            
            # Find HeMu output files
            date_key = f"{start_date.strftime('%Y%m%d%H%M')}-{end_date.strftime('%Y%m%d%H%M')}"
            hemu_output_dir = self.hemu_root / f"runs/{self.domain}/{date_key}"
            
            # Look for solar irradiance predictions (adjust variable name as needed)
            prediction_files = list(hemu_output_dir.glob("**/predictions_*.nc"))
            
            if not prediction_files:
                logger.warning("No HeMu prediction files found")
                return False
            
            # Convert predictions to COG format
            app_cogs_dir = Path(__file__).parent.parent / "data/cogs"
            app_cogs_dir.mkdir(exist_ok=True)
            
            converted_count = 0
            for pred_file in prediction_files:
                try:
                    # Extract timestamp from filename
                    # (This will need adjustment based on actual HeMu output format)
                    timestamp_str = pred_file.stem.split('_')[-1]  # Adjust as needed
                    
                    # Convert to COG
                    cog_path, timestamp, vmin, vmax = convert_netcdf_to_cog(
                        str(pred_file), 
                        variable_name="solar_irradiance"  # Adjust variable name
                    )
                    
                    logger.info(f"✅ Converted: {pred_file.name} -> {cog_path}")
                    converted_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to convert {pred_file}: {e}")
            
            logger.info(f"✅ Converted {converted_count} files to COG format")
            return converted_count > 0
            
        except Exception as e:
            logger.error(f"❌ COG conversion failed: {e}")
            return False
    
    def cleanup_old_data(self):
        """Clean up old processed data"""
        logger.info("🗑️  Cleaning up old data...")
        self.state_manager.cleanup_old_data(keep_days=7)  # Keep 1 week
    
    def run(self):
        """Main processing routine"""
        logger.info(f"🚀 Starting HeMu automated processing for {self.domain}")
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ Dependencies missing, cannot proceed")
            return False
        
        # Setup static data if needed
        if not self.setup_static_data():
            logger.error("❌ Static data setup failed")
            return False
        
        # Get processing dates
        start_date, end_date = self.get_processing_dates()
        logger.info(f"📅 Processing period: {start_date} to {end_date}")
        
        # Check if already processed
        if self.state_manager.is_date_range_processed(start_date, end_date):
            logger.info("✅ Data already processed, skipping")
            return True
        
        # Process satellite data
        if not self.process_satellite_data(start_date, end_date):
            return False
        
        # Convert to app format
        if not self.convert_to_app_format(start_date, end_date):
            logger.warning("⚠️  COG conversion failed, but processing succeeded")
        
        # Cleanup old data
        self.cleanup_old_data()
        
        logger.info("🎉 HeMu processing complete!")
        return True

def main():
    """Main entry point"""
    processor = SmartHeMuProcessor(domain="CH", lookback_hours=24)
    success = processor.run()
    
    if success:
        logger.info("✅ HeMu automated processing completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ HeMu automated processing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
