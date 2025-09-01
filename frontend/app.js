// Global state
let map;
let dates = [];
let scalingParams = {};
let currentIndex = 0;
let animationId = null;
let isPlaying = false;

// Initialize map
function initializeMap() {
    map = new maplibregl.Map({
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

    map.on('load', () => {
        console.log('🗺️ Map loaded');
        hideLoading();
    });

    return map;
}

// Sidebar functionality
function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        
        // Update toggle icon - when sidebar is open, show right arrow (to close)
        // when sidebar is closed, show left arrow (to open)
        const icon = sidebarToggle.querySelector('i');
        if (sidebar.classList.contains('collapsed')) {
            icon.className = 'fas fa-chevron-left'; // Open sidebar (arrow points toward sidebar)
        } else {
            icon.className = 'fas fa-chevron-right'; // Close sidebar (arrow points away from sidebar)
        }
    });
}

// Loading state management
function showLoading() {
    const loading = document.getElementById('loading-indicator');
    if (loading) loading.classList.add('show');
}

function hideLoading() {
    const loading = document.getElementById('loading-indicator');
    if (loading) loading.classList.remove('show');
}

// Notification system
function showNotification(message, type = 'info') {
    const notifications = document.getElementById('notifications');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    notifications.appendChild(notification);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 4000);
}

// Data loading
function loadTimestamps() {
    showLoading();
    
    fetch('/api/timestamps')
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            if (data.length === 0) {
                document.getElementById("range-info").textContent = "No data available.";
                showNotification("No data available", "error");
                return;
            }
            
            // Store dates and scaling parameters
            dates = data.map(item => item.datetime);
            data.forEach(item => {
                scalingParams[item.datetime] = {
                    vmin: item.vmin,
                    vmax: item.vmax
                };
            });

            setupTimeControls();
            updateLayerByTime(0);
            showNotification(`Loaded ${dates.length} timestamps`, "success");
        })
        .catch(error => {
            console.error('❌ Error loading timestamps:', error);
            document.getElementById("range-info").textContent = "Error loading data.";
            document.getElementById("error").textContent = error.message;
            showNotification(`Error: ${error.message}`, "error");
        })
        .finally(() => {
            hideLoading();
        });
}

// Time controls setup
function setupTimeControls() {
    const slider = document.getElementById("date-slider");
    const rangeInfo = document.getElementById("range-info");
    const sliderStart = document.getElementById("slider-start");
    const sliderEnd = document.getElementById("slider-end");
    
    slider.max = dates.length - 1;
    slider.value = 0;
    currentIndex = 0;
    
    // Update display
    rangeInfo.textContent = `${dates.length} timestamps available`;
    sliderStart.textContent = new Date(dates[0]).toLocaleDateString();
    sliderEnd.textContent = new Date(dates[dates.length - 1]).toLocaleDateString();
    
    updateCurrentTimeDisplay(0);
}

// Update current time display
function updateCurrentTimeDisplay(index) {
    const currentDate = document.getElementById("current-date");
    if (dates[index]) {
        const date = new Date(dates[index]);
        currentDate.textContent = date.toLocaleString();
    }
}

// Layer update function
function updateLayerByTime(index) {
    if (!dates.length || index >= dates.length || index < 0) {
        console.warn('⚠️ Invalid index or no dates available');
        return;
    }
    
    currentIndex = index;
    const date = dates[index];
    const scaling = scalingParams[date];
    const variable = document.getElementById("data-layer").value;
    const colormap = document.getElementById("colormap-select").value;
    const tiffName = `${variable}_${date}.tif`;
    const tiffPath = `/opt/cogs/${tiffName}`;
    
    console.log(`🎯 Loading: ${tiffName} with scaling:`, scaling);
    
    fetch(`/cog/info?url=${encodeURIComponent(tiffPath)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`File not found: ${tiffName}`);
            }
            return response.json();
        })
        .then(info => {
            // Remove existing layer
            if (map.getLayer('data-layer')) {
                map.removeLayer('data-layer');
            }
            if (map.getSource('dataLayer')) {
                map.removeSource('dataLayer');
            }

            // Construct tile URL with scaling
            const tileUrl = `/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png?url=${encodeURIComponent(tiffPath)}&rescale=${scaling.vmin},${scaling.vmax}&colormap_name=${colormap}`;

            // Add new source
            map.addSource('dataLayer', {
                type: 'raster',
                tiles: [tileUrl],
                tileSize: 256,
                bounds: info.bounds
            });

            // Add new layer
            const dataOpacity = parseInt(document.getElementById("data-opacity").value) / 100;
            map.addLayer({
                id: 'data-layer',
                type: 'raster',
                source: 'dataLayer',
                layout: {
                    visibility: 'visible'
                },
                paint: {
                    'raster-opacity': dataOpacity,
                    'raster-resampling': 'nearest'
                }
            });

            // Update data info display
            updateDataInfo(scaling);
            updateColorLegend(scaling, colormap);
            
            console.log('✅ Layer updated successfully');
        })
        .catch(error => {
            console.error('❌ Error updating layer:', error);
            document.getElementById("error").textContent = error.message;
            showNotification(`Error: ${error.message}`, "error");
        });
}

// Update data info panel
function updateDataInfo(scaling) {
    document.getElementById("current-vmin").textContent = scaling.vmin.toFixed(1);
    document.getElementById("current-vmax").textContent = scaling.vmax.toFixed(1);
}

// Update color legend
function updateColorLegend(scaling, colormap) {
    const legendMin = document.getElementById("legend-min");
    const legendMax = document.getElementById("legend-max");
    const legendBar = document.querySelector(".legend-bar");
    
    legendMin.textContent = scaling.vmin.toFixed(0);
    legendMax.textContent = scaling.vmax.toFixed(0);
    
    // Update legend bar gradient based on colormap
    const colormapGradients = {
        'magma': 'linear-gradient(to right, #000004, #320a5e, #781b6c, #bb3654, #ec6824, #fbb41a, #fcffa4)',
        'viridis': 'linear-gradient(to right, #440154, #31688e, #35b779, #fde725)',
        'plasma': 'linear-gradient(to right, #0d0887, #7e03a8, #cc4778, #f89441, #f0f921)',
        'turbo': 'linear-gradient(to right, #23171b, #271a28, #2d1e3e, #34285a, #3e3574, #4c448a, #5c549d, #6d65ad, #7f76ba, #9287c4, #a598cc, #b9a9d1, #cdbad4, #e1ccd4, #f4ddd1, #ffeecb)',
        'hot': 'linear-gradient(to right, #000000, #ff0000, #ffff00, #ffffff)',
        'cool': 'linear-gradient(to right, #00ffff, #ff00ff)'
    };
    
    legendBar.style.background = colormapGradients[colormap] || colormapGradients['magma'];
}

// Animation controls
function startAnimation() {
    if (isPlaying || dates.length === 0) return;
    
    isPlaying = true;
    document.getElementById("play-btn").style.display = "none";
    document.getElementById("pause-btn").style.display = "flex";
    
    function animate() {
        if (!isPlaying) return;
        
        currentIndex = (currentIndex + 1) % dates.length;
        document.getElementById("date-slider").value = currentIndex;
        updateCurrentTimeDisplay(currentIndex);
        updateLayerByTime(currentIndex);
        
        animationId = setTimeout(animate, 500); // 2 FPS
    }
    
    animate();
}

function pauseAnimation() {
    isPlaying = false;
    if (animationId) {
        clearTimeout(animationId);
        animationId = null;
    }
    
    document.getElementById("play-btn").style.display = "flex";
    document.getElementById("pause-btn").style.display = "none";
}

function resetAnimation() {
    pauseAnimation();
    currentIndex = 0;
    document.getElementById("date-slider").value = 0;
    updateCurrentTimeDisplay(0);
    updateLayerByTime(0);
}

// Basemap management
function updateBasemap(type) {
    const basemapSources = {
        'osm': 'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'satellite': 'http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        'terrain': 'http://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        'dark': 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
    };
    
    const tileURL = basemapSources[type] || basemapSources['osm'];
    map.getSource('osm').tiles = [tileURL];
    map.style.sourceCaches['osm'].clearTiles();
    map.style.sourceCaches['osm'].update(map.transform);
    map.triggerRepaint();
}

// Event listeners setup
function setupEventListeners() {
    // Sidebar
    initializeSidebar();
    
    // Time slider
    document.getElementById("date-slider").addEventListener("input", (e) => {
        const index = parseInt(e.target.value);
        currentIndex = index;
        updateCurrentTimeDisplay(index);
        updateLayerByTime(index);
    });
    
    // Playback controls
    document.getElementById("play-btn").addEventListener("click", startAnimation);
    document.getElementById("pause-btn").addEventListener("click", pauseAnimation);
    document.getElementById("reset-btn").addEventListener("click", resetAnimation);
    
    // Basemap controls
    document.getElementById("basemap-select").addEventListener("change", (e) => {
        updateBasemap(e.target.value);
    });
    
    document.getElementById("basemap-opacity").addEventListener("input", (e) => {
        const opacity = parseInt(e.target.value) / 100;
        map.setPaintProperty('osm', 'raster-opacity', opacity);
        document.getElementById("basemap-opacity-value").textContent = `${e.target.value}%`;
    });
    
    // Data layer controls
    document.getElementById("data-opacity").addEventListener("input", (e) => {
        const opacity = parseInt(e.target.value) / 100;
        if (map.getLayer('data-layer')) {
            map.setPaintProperty('data-layer', 'raster-opacity', opacity);
        }
        document.getElementById("data-opacity-value").textContent = `${e.target.value}%`;
    });
    
    document.getElementById("colormap-select").addEventListener("change", () => {
        updateLayerByTime(currentIndex);
    });
    
    // Map controls
    document.getElementById("fullscreen-btn").addEventListener("click", () => {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            document.documentElement.requestFullscreen();
        }
    });
    
    document.getElementById("home-btn").addEventListener("click", () => {
        map.setCenter([8.2, 46.8]);
        map.setZoom(6);
    });
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Heliomont DML application');
    
    // Initialize components
    initializeMap();
    setupEventListeners();
    
    // Load initial data
    loadTimestamps();
    
    console.log('✅ Application initialized');
});

// Global functions for compatibility
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
