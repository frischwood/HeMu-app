let map = new maplibregl.Map({
    container: 'map',
    style: {
        version: 8,
        sources: {
            osm: {
                type: 'raster',
                tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'],
                tileSize: 256,
            }
        },
        layers: [
            { 
                id: 'osm', 
                type: 'raster', 
                source: 'osm',
                paint: {
                    'raster-opacity': 1
                }
            }
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
    console.log('🚀 Starting layer update with index:', index);
    
    if (!dates.length || index >= dates.length) {
        console.warn('⚠️ No dates available or invalid index');
        return;
    }
    
    const date = dates[index];
    const variable = document.getElementById("data-layer").value;
    const tiffName = `${variable}_${date}.tif`;
    // Use direct path without file:// protocol
    const tiffPath = `/opt/cogs/${tiffName}`;
    
    console.log('📂 Loading file:', tiffPath);
    
    fetch(`http://localhost:8001/cog/info?url=${encodeURIComponent(tiffPath)}`) // 
        .then(response => {
            console.log('📡 TiTiler response:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(info => {
            console.log('ℹ️ File info:', info);
            
            // Remove existing layer and source
            if (map.getLayer('data-layer')) {
                console.log('🗑️ Removing existing layer');
                map.removeLayer('data-layer');
            }
            if (map.getSource('dataLayer')) {
                console.log('🗑️ Removing existing source');
                map.removeSource('dataLayer');
            }

            // Construct tile URL with direct path
            const tileUrl = `http://localhost:8001/cog/tiles/{z}/{x}/{y}.png?url=${encodeURIComponent(tiffPath)}`; //{encodeURIComponent(tiffPath)}
            console.log('🔗 New tile URL:', tileUrl);

            // Add new source
            map.addSource('dataLayer', {
                type: 'raster',
                tiles: [tileUrl],
                tileSize: 256,
                bounds: info.bounds
            });

            // Add new layer with maximum opacity
            map.addLayer({
                id: 'data-layer',
                type: 'raster',
                source: 'dataLayer',
                layout: {
                    visibility: 'visible'
                },
                paint: {
                    'raster-opacity': 1,
                    'raster-resampling': 'nearest'
                }
            }); // Add above the basemap

            console.log('✅ Layer added with bounds:', info.bounds);
            
            // Zoom to layer
            map.fitBounds([
                [info.bounds[0], info.bounds[1]],
                [info.bounds[2], info.bounds[3]]
            ], {
                padding: 20,
                duration: 1000
            });
        })
        .catch(error => {
            console.error('❌ Error:', error);
            document.getElementById("error").textContent = error.message;
        });
}

document.getElementById("date-slider").addEventListener("input", (e) => {
    // updateLayerByTime(parseInt(e.target.value));
    const index = parseInt(e.target.value);
    console.log('🎚️ Slider changed:', { index, date: dates[index] });
    document.getElementById("current-date").textContent = dates[index];
    updateLayerByTime(index);
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

// Add event listener for map load
map.on('load', () => {
    console.log('🗺️ Map loaded');
});

// Move toggle functions here from inline scripts
window.toggleLayer = function() {
    if (map.getLayer('data-layer')) {
        const visibility = map.getLayoutProperty('data-layer', 'visibility');
        const newVisibility = visibility === 'visible' ? 'none' : 'visible';
        map.setLayoutProperty('data-layer', 'visibility', newVisibility);
        console.log('👁️ Layer visibility set to:', newVisibility);
    }
};

window.zoomToLayer = function() {
    if (map.getSource('dataLayer')) {
        const bounds = map.getSource('dataLayer').bounds;
        if (bounds) {
            map.fitBounds(bounds, {
                padding: 20,
                duration: 1000
            });
        }
    }
};