let map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        osm: {
          type: 'raster',
          tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
        },
        dataLayer: {
          type: 'raster',
          tiles: [],  // initially empty
          tileSize: 256,
          minzoom: 0,
          maxzoom: 14
        }
      },
      layers: [
        { id: 'osm', type: 'raster', source: 'osm' },
        { id: 'data-layer', type: 'raster', source: 'dataLayer' }
      ]
    },
    center: [8.2, 46.8],
    zoom: 6
  });
  
  let dates = [];
  fetch('http://localhost:8000/timestamps')
    .then(res => res.json())
    .then(ts => {
      const rangeInfo = document.getElementById("range-info");
      if (ts.length === 0) {
        rangeInfo.textContent = "No data available.";
        return;
      }
      dates = ts;
      const slider = document.getElementById("date-slider");
      slider.max = dates.length - 1;
      slider.value = 0;
      document.getElementById("current-date").textContent = dates[0];
      rangeInfo.textContent = `Available range: ${dates[0]} to ${dates[dates.length - 1]}`;
      updateLayerByTime(0);
    });
  
    function updateLayerByTime(index) {
      console.log('🚀 updateLayerByTime called with index:', index);
      
      if (!dates.length || index >= dates.length) {
          console.warn('⚠️ No dates available or invalid index');
          return;
      }
      
      const date = dates[index];
      console.log('📅 Current date:', date);
      
      document.getElementById("current-date").textContent = date;
      const variable = document.getElementById("data-layer").value;
      const tiffName = `${variable}_${date}.tif`;
      const tiffPath = `file:///opt/cogs/${tiffName}`;
      
      console.log('🔍 Looking for file:', tiffName);
      console.log('📁 Full path:', tiffPath);
      
      // Update debug message
      document.getElementById("debug").textContent = `Looking for file: ${tiffName}`;
      
      // First check if the file exists and get its metadata
      const infoUrl = `http://localhost:8001/cog/info?url=${encodeURIComponent(tiffPath)}`;
      console.log('🌐 Fetching metadata from:', infoUrl);
      
      fetch(infoUrl)
          .then(response => {
              console.log('📥 Response status:', response.status);
              if (!response.ok) {
                  return response.json().then(error => {
                      const errorMessage = `Server error: ${JSON.stringify(error)}`;
                      console.error('❌ Error:', errorMessage);
                      document.getElementById("error").textContent = errorMessage;
                      throw new Error('Server response not ok');
                  });
              }
              return response.json();
          })
          .then(info => {
              console.log('ℹ️ File metadata:', info);
              document.getElementById("error").textContent = '';
              
              const newUrl = `http://localhost:8001/cog/tiles/{z}/{x}/{y}.png?url=${encodeURIComponent(tiffPath)}`;
              console.log('🗺️ Creating tile URL:', newUrl);
  
              // Remove existing layer and source if they exist
              if (map.getLayer('data-layer')) {
                  console.log('🗑️ Removing existing layer');
                  map.removeLayer('data-layer');
              }
              if (map.getSource('dataLayer')) {
                  console.log('🗑️ Removing existing source');
                  map.removeSource('dataLayer');
              }
  
              console.log('➕ Adding new source and layer');
              map.addSource('dataLayer', {
                  type: 'raster',
                  tiles: [newUrl],
                  tileSize: 256,
                  minzoom: 0,
                  maxzoom: 22,
                  bounds: info.bounds
              });
  
              map.addLayer({
                  id: 'data-layer',
                  type: 'raster',
                  source: 'dataLayer',
                  paint: {
                      'raster-opacity': 0.8,
                      'raster-resampling': 'linear'
                  }
              });
  
              console.log('✅ Layer added successfully');
          })
          .catch(error => {
              const errorMessage = `Error loading layer: ${error.message}`;
              console.error('❌ Error:', error);
              document.getElementById("error").textContent = errorMessage;
          });
  }

// function updateLayerByTime(index) {
//     if (!dates.length || index >= dates.length) return;
//     const date = dates[index];
//     document.getElementById("current-date").textContent = date;
//     const variable = document.getElementById("data-layer").value;
//     const tiffName = `${variable}_${date}.tif`;
    
//     // Update debug message
//     document.getElementById("debug").textContent = `Looking for file: ${tiffName}`;
    
//     fetch(`http://localhost:8001/cog/info?url=file:///opt/cogs/${tiffName}`)
//         .then(response => {
//             if (!response.ok) {
//                 document.getElementById("error").textContent = `File not found: ${tiffName}`;
//                 console.error('File not found:', tiffName);
//                 console.error('Full path:', `/opt/cogs/${tiffName}`);
//                 return;
//             }
//             document.getElementById("error").textContent = ''; // Clear error on success
            
//             const newUrl = `http://localhost:8001/cog/tiles/{z}/{x}/{y}.png?url=file:///opt/cogs/${tiffName}`;
//             console.log('Loading tile URL:', newUrl);

//             map.removeLayer('data-layer');
//             map.removeSource('dataLayer');

//             map.addSource('dataLayer', {
//                 type: 'raster',
//                 tiles: [newUrl],
//                 tileSize: 256,
//                 minzoom: 0,
//                 maxzoom: 14,
//             });

//             map.addLayer({
//                 id: 'data-layer',
//                 type: 'raster',
//                 source: 'dataLayer'
//             });
//         })
//         .catch(error => {
//             document.getElementById("error").textContent = `Error: ${error.message}`;
//             console.error('Error checking file:', error);
//         });
// }
  
  document.getElementById("date-slider").addEventListener("input", (e) => {
    updateLayerByTime(parseInt(e.target.value));
  });
  
  document.getElementById("basemap-select").addEventListener("change", (e) => {
    const type = e.target.value;
    let tileURL = '';
    if (type === 'osm') {
      tileURL = 'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png';
    } else if (type === 'google') {
      tileURL = 'http://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}';
    } else if (type === 'adminCH') {
        tileURL = 'https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg';
      }
    map.getSource('osm').tiles = [tileURL];
    map.style.sourceCaches['osm'].clearTiles();
    map.style.sourceCaches['osm'].update(map.transform);
    map.triggerRepaint();
  });

  document.getElementById("basemap-opacity").addEventListener("input", (e) => {
    const opacity = parseInt(e.target.value) / 100;
    map.setPaintProperty('osm', 'raster-opacity', opacity);
    document.getElementById("basemap-opacity-value").textContent = `${e.target.value}%`;
  });

  document.getElementById("data-opacity").addEventListener("input", (e) => {
    const opacity = parseInt(e.target.value) / 100;
    if (map.getLayer('data-layer')) {
        map.setPaintProperty('data-layer', 'raster-opacity', opacity);
    }
    document.getElementById("data-opacity-value").textContent = `${e.target.value}%`;
});