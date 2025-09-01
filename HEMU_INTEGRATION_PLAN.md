# HeMu Integration Implementation Roadmap

## 🎯 **Objective**
Integrate HeMu satellite data processing with the existing app to automatically:
1. Download new satellite data from EUMDAC
2. Process it for solar irradiance inference  
3. Generate COG files for visualization
4. Avoid recomputing static data (domain, topography)

## 📋 **Implementation Phases**

### **Phase 1: Prerequisites Setup** ⏱️ 2-3 days
- [ ] **Install HORAYZON dependency**
  - Manual installation of HORAYZON package
  - Prepare horizon data for Switzerland domain
  - Test basic functionality

- [ ] **Create Switzerland domain configuration**
  ```bash
  cd /Users/frischho/Documents/dev/heliomont_dml/app/HeMu
  python create_switzerland_domain.py
  ```

- [ ] **Setup required config files**
  - Create `configs/TSViT.yaml` (model configuration)
  - Create `data/Helio/stats/stats_NC_2015_2020_sza80.csv` (normalization stats)
  - Setup model checkpoints

### **Phase 2: Smart Processing Logic** ⏱️ 1-2 days  
- [x] **State Management System**
  - `hemu_state_manager.py` - tracks processed data
  - Avoids recomputation of static data
  - Manages date ranges and cleanup

- [x] **Smart HeMu Processor**
  - `smart_hemu_processor.py` - main automation logic
  - Intelligent caching and dependency checking
  - Integration with existing app data flow

### **Phase 3: Docker Integration** ⏱️ 1 day
- [x] **HeMu Docker Container**
  - `Dockerfile.hemu` - HeMu-specific container
  - `requirements-hemu.txt` - ML and satellite processing deps
  - `docker-compose-with-hemu.yml` - updated orchestration

- [ ] **Container Testing**
  - Build and test HeMu container
  - Verify GPU access (if available)
  - Test data sharing between containers

### **Phase 4: Data Flow Integration** ⏱️ 1-2 days
- [ ] **HeMu Output → App COGs**
  - Convert HeMu predictions to COG format
  - Integrate with existing ingest pipeline
  - Update database records

- [ ] **API Integration**
  - Update backend to serve HeMu predictions
  - Modify frontend for new data types
  - Add processing status endpoints

### **Phase 5: Testing & Optimization** ⏱️ 2-3 days
- [ ] **End-to-End Testing**
  - Test complete pipeline from satellite download to visualization
  - Validate data quality and timing
  - Performance optimization

- [ ] **Error Handling & Monitoring**
  - Robust error handling for EUMDAC API failures
  - Monitoring and alerting for processing failures
  - Graceful degradation strategies

## 🔧 **Key Technical Considerations**

### **Static Data Optimization**
- ✅ Static data (topography, domain) computed once and cached
- ✅ Hash-based change detection for domain updates
- ✅ Separate static data processing from dynamic satellite data

### **Processing Schedule**
- **HeMu Processor**: Runs hourly, processes last 24 hours of satellite data
- **Original Ingest**: Continues running every 5 minutes for existing NetCDF files
- **Smart Scheduling**: Avoids duplicate processing through state management

### **Data Flow Architecture**
```
EUMDAC API → HeMu Processor → Solar Irradiance Predictions → COG Conversion → App Visualization
     ↓              ↓                      ↓                      ↓              ↓
Satellite Data → Processing Cache → NetCDF Outputs → TiTiler → Frontend Maps
```

### **Resource Management**
- **Memory**: Large satellite files processed in chunks
- **Storage**: Old processed data automatically cleaned up
- **GPU**: Optional GPU acceleration for ML inference
- **Network**: Efficient satellite data downloads

## 🚀 **Deployment Steps**

### **Step 1: Prepare Dependencies**
```bash
# Setup infrastructure
cd /Users/frischho/Documents/dev/heliomont_dml/app/HeMu
chmod +x setup_infrastructure.sh
./setup_infrastructure.sh

# Create Switzerland domain
python create_switzerland_domain.py
```

### **Step 2: Configure EUMDAC Credentials**
```bash
# Update .env file with EUMDAC API credentials
cp docker/.env.template.hemu docker/.env.hemu
# Edit .env.hemu with your EUMDAC API key/secret
```

### **Step 3: Build and Test**
```bash
# Build HeMu container
cd docker
docker build -f ../HeMu/Dockerfile.hemu -t hemu-processor ../HeMu/

# Test basic functionality
docker run --rm -it hemu-processor python -c "import HeMu; print('HeMu import successful')"
```

### **Step 4: Deploy with Docker Compose**
```bash
# Start with HeMu integration
docker-compose -f docker-compose-with-hemu.yml up -d

# Monitor logs
docker-compose -f docker-compose-with-hemu.yml logs -f hemu-processor
```

## 📊 **Expected Outcomes**

### **Automated Workflow**
1. **Every Hour**: HeMu processor checks for new satellite data
2. **Smart Processing**: Only processes new/missing data
3. **COG Generation**: Converts predictions to app-compatible format
4. **Visualization**: New solar irradiance maps appear in frontend
5. **Cleanup**: Old data automatically removed to save space

### **Performance Targets**
- **Processing Latency**: < 30 minutes from satellite availability
- **Data Freshness**: Hourly updates during daylight hours
- **Storage Efficiency**: 7-day rolling window of processed data
- **Reliability**: 95%+ uptime with graceful error handling

### **User Experience**
- **Real-time Data**: Fresh solar irradiance predictions
- **Historical Continuity**: Seamless integration with existing data
- **Performance**: No impact on existing app performance
- **Monitoring**: Processing status visible through API

## ⚠️ **Risk Mitigation**

### **Technical Risks**
- **HORAYZON Dependency**: Manual installation required
- **EUMDAC API Limits**: Rate limiting and quotas
- **Processing Resources**: GPU availability for inference
- **Data Quality**: Satellite data gaps and quality issues

### **Mitigation Strategies**
- **Fallback Processing**: CPU-only inference if GPU unavailable
- **Error Recovery**: Retry logic for API failures
- **Data Validation**: Quality checks on processed outputs
- **Monitoring**: Comprehensive logging and alerting

## 🎉 **Success Criteria**

- [ ] **Functional**: HeMu processor automatically downloads and processes satellite data
- [ ] **Efficient**: Static data cached and not recomputed unnecessarily  
- [ ] **Integrated**: HeMu outputs seamlessly appear in existing app interface
- [ ] **Reliable**: System handles failures gracefully and recovers automatically
- [ ] **Maintainable**: Clear logging, monitoring, and debugging capabilities
