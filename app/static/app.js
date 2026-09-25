/**
 * Raksha AI - Frontend Client Application
 * Version: 3.5.0 (Dual-Theme: Dark Obsidian 🌙 & Clean Light ☀️)
 * 
 * Dedicated Modules:
 * 1. State Traffic Police Headquarters Portal (Accidents, Traffic Gridlocks, Road Diversions)
 * 2. PWD Admin Portal (Civil Highways, Potholes & Pedestrian Crosswalks)
 * 3. Bus Driver MADT In-Cabin Tactical Radar HUD (Speedometer, Proximity Alerts, Audio)
 * 4. Bus Edge AI Perception Simulator & AES-256 Cryptographic Pipeline
 * 5. Geofencing Proximity Collision Engine & Supabase Cloud Sync
 */

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // 1. STATE MANAGEMENT & CONFIGURATION
  // -------------------------------------------------------------------------
  const state = {
    currentTab: 'police-hq',
    theme: 'light',
    policeIncidents: [],
    pwdIncidents: [],
    activeGeofences: [],
    filterPolice: 'ALL',
    filterPwd: 'ALL',

    // Bus Telemetry & Route Simulation State
    bus: {
      id: 'BUS-104',
      lat: 13.0850,
      lng: 80.2760,
      speedKmh: 42.0,
      heading: 215.0,
      routeName: 'Route 19B : Chennai Central ➔ IT Highway Express',
      isDriving: false,
      currentWaypointIdx: 0,
      driveInterval: null
    },

    // Audio & Voice Alarms
    audioEnabled: true,
    lastSpokenAlertId: null,
    audioContext: null,

    // AES-256 Cryptographic Key
    aesMasterKeyHex: 'e4d9b2a7f8301c65b9d318e24f0c9a5b7134d6e802f1a5c39b7d8e204a1f6c8b'
  };

  // Metropolitan Transit Route Waypoints
  const ROUTE_WAYPOINTS = [
    { lat: 13.0850, lng: 80.2760, name: 'Central Station Terminal' },
    { lat: 13.0838, lng: 80.2745, name: 'EVR Periyar Salai (Near Vehicle Collision)' },
    { lat: 13.0805, lng: 80.2690, name: 'Gandhi Irwin Bridge (Near Severe Pothole)' },
    { lat: 13.0760, lng: 80.2610, name: 'Poonamallee High Rd (Near Traffic Jam)' },
    { lat: 13.0690, lng: 80.2550, name: 'Pantheon Road (Near Pothole Cluster)' },
    { lat: 13.0645, lng: 80.2480, name: 'Gemini Flyover (Near Signal Malfunction)' },
    { lat: 13.0580, lng: 80.2505, name: 'Sterling Road (Near Faded Zebra Crossing)' },
    { lat: 13.0512, lng: 80.2520, name: 'Cathedral Road (Near Illegal Parking)' },
    { lat: 13.0450, lng: 80.2410, name: 'Mount Road (Near Displaced Manhole)' },
    { lat: 13.0400, lng: 80.2330, name: 'T. Nagar Transit Hub Terminal' }
  ];

  // Map Layer Tile Providers (Real OpenStreetMap, Satellite, Mapbox, Carto)
  const MAP_PROVIDERS = {
    osm: {
      name: 'OpenStreetMap (Real Streets)',
      url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      attrib: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
      maxZoom: 19,
      needsKey: false
    },
    satellite: {
      name: 'ESRI World Imagery (Real Satellite HD)',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attrib: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, GIS Community',
      maxZoom: 19,
      needsKey: false
    },
    mapbox_streets: {
      name: 'Mapbox Streets Pro',
      urlTemplate: 'https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{z}/{x}/{y}?access_token={key}',
      attrib: '&copy; <a href="https://www.mapbox.com/" target="_blank">Mapbox</a> &copy; OpenStreetMap',
      maxZoom: 20,
      needsKey: true
    },
    mapbox_satellite: {
      name: 'Mapbox Satellite Hybrid',
      urlTemplate: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token={key}',
      attrib: '&copy; <a href="https://www.mapbox.com/" target="_blank">Mapbox</a>',
      maxZoom: 20,
      needsKey: true
    },
    mapbox_dark: {
      name: 'Mapbox Navigation Night',
      urlTemplate: 'https://api.mapbox.com/styles/v1/mapbox/navigation-night-v1/tiles/{z}/{x}/{y}?access_token={key}',
      attrib: '&copy; <a href="https://www.mapbox.com/" target="_blank">Mapbox</a>',
      maxZoom: 20,
      needsKey: true
    },
    carto_dark: {
      name: 'CartoDB Dark Obsidian',
      url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      attrib: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap contributors',
      maxZoom: 19,
      needsKey: false
    },
    carto_light: {
      name: 'CartoDB Light Minimal',
      url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      attrib: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap contributors',
      maxZoom: 19,
      needsKey: false
    }
  };

  const TILE_DARK = MAP_PROVIDERS.carto_dark.url;
  const TILE_LIGHT = MAP_PROVIDERS.carto_light.url;
  const TILE_ATTRIB = MAP_PROVIDERS.carto_dark.attrib;

  // Leaflet Maps and Marker Layers
  let policeMap = null, policeTileLayer = null, policeGeofenceLayers = [], policeBusMarker = null;
  let pwdMap = null, pwdTileLayer = null, pwdGeofenceLayers = [], pwdBusMarker = null;
  let driverMap = null, driverTileLayer = null, driverGeofenceLayers = [], driverBusMarker = null, driverScanCircle = null;

  // Haversine Distance Formula (Meters)
  function calculateDistanceMeters(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const phi1 = (lat1 * Math.PI) / 180;
    const phi2 = (lat2 * Math.PI) / 180;
    const dPhi = ((lat2 - lat1) * Math.PI) / 180;
    const dLambda = ((lon2 - lon1) * Math.PI) / 180;

    const a =
      Math.sin(dPhi / 2) * Math.sin(dPhi / 2) +
      Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) * Math.sin(dLambda / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  // -------------------------------------------------------------------------
  // 2. INITIALIZATION
  // -------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initNavigationTabs();
    initLeafletMaps();
    initEdgePerceptionLab();
    initDriverCockpitControls();
    initModals();
    fetchAllData();

    // Realtime Polling Loop
    setInterval(() => {
      fetchIncidentsAndGeofences();
      updateDriverProximityHUD();
    }, 2500);
  });

  // -------------------------------------------------------------------------
  // 3. THEME TOGGLE (DARK OBSIDIAN / LIGHT PURE WHITE)
  // -------------------------------------------------------------------------
  function initThemeToggle() {
    const btnToggle = document.getElementById('btnThemeToggle');
    const themeText = document.getElementById('themeText');

    // Check localStorage or default
    const savedTheme = localStorage.getItem('roadvision_theme') || 'light';
    applyTheme(savedTheme);

    btnToggle?.addEventListener('click', () => {
      const newTheme = state.theme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      showToast(newTheme === 'light' ? '☀️ Switched to Light Mode' : '🌙 Switched to Dark Obsidian Mode', 'police');
    });

    function applyTheme(theme) {
      state.theme = theme;
      localStorage.setItem('roadvision_theme', theme);

      if (theme === 'light') {
        document.body.classList.remove('theme-dark');
        document.body.classList.add('theme-light');
        if (themeText) themeText.textContent = 'Light Mode';
      } else {
        document.body.classList.remove('theme-light');
        document.body.classList.add('theme-dark');
        if (themeText) themeText.textContent = 'Dark Mode';
      }

      updateMapTileLayers(theme);
    }
  }

  function getTileUrlAndAttrib(providerKey) {
    const key = providerKey || state.mapProvider || 'osm';
    const provider = MAP_PROVIDERS[key] || MAP_PROVIDERS.osm;
    let url = provider.url;
    const mapboxKey = (localStorage.getItem('roadvision_mapbox_key') || '').trim();
    if (provider.needsKey) {
      if (!mapboxKey) {
        return null;
      }
      url = provider.urlTemplate.replace('{key}', encodeURIComponent(mapboxKey));
    }
    return {
      key,
      url,
      attrib: provider.attrib,
      maxZoom: provider.maxZoom || 19,
      provider
    };
  }

  function setAllMapTileLayers(providerKey, quiet = false) {
    const info = getTileUrlAndAttrib(providerKey);
    if (!info) {
      showToast('⚠️ Mapbox layer requires an API Key. Please add your Mapbox token.', 'pwd');
      openMapConfigModal();
      return;
    }

    state.mapProvider = info.key;
    localStorage.setItem('roadvision_map_provider', info.key);

    // Sync all dropdowns in UI
    document.querySelectorAll('.map-provider-select, #modalMapProviderSelect').forEach(el => {
      el.value = info.key;
    });

    const updateLayer = (map, currentLayer) => {
      if (!map) return currentLayer;
      try {
        if (currentLayer) map.removeLayer(currentLayer);
        const newLayer = L.tileLayer(info.url, {
          attribution: info.attrib,
          maxZoom: info.maxZoom
        }).addTo(map);
        newLayer.bringToBack();
        return newLayer;
      } catch (err) {
        console.warn('Map layer update error:', err);
        return currentLayer;
      }
    };

    policeTileLayer = updateLayer(policeMap, policeTileLayer);
    pwdTileLayer = updateLayer(pwdMap, pwdTileLayer);
    driverTileLayer = updateLayer(driverMap, driverTileLayer);

    if (!quiet) {
      showToast(`🗺️ Map layer: ${info.provider.name}`, 'police');
    }
  }

  function updateMapTileLayers(theme) {
    if (['carto_dark', 'carto_light'].includes(state.mapProvider)) {
      const nextCarto = theme === 'light' ? 'carto_light' : 'carto_dark';
      setAllMapTileLayers(nextCarto, true);
    }
  }

  // -------------------------------------------------------------------------
  // 4. NAVIGATION & TAB SWITCHING
  // -------------------------------------------------------------------------
  function initNavigationTabs() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const portalViews = document.querySelectorAll('.portal-view');

    navButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        if (!tab) return;

        navButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        portalViews.forEach(view => view.classList.remove('active'));
        const activeView = document.getElementById(getTabElementId(tab));
        if (activeView) activeView.classList.add('active');

        state.currentTab = tab;

        // Invalidate map sizes
        setTimeout(() => {
          if (tab === 'police-hq' && policeMap) policeMap.invalidateSize();
          if (tab === 'pwd-admin' && pwdMap) pwdMap.invalidateSize();
          if (tab === 'driver-madt' && driverMap) driverMap.invalidateSize();
        }, 150);
      });
    });

    const pathname = window.location.pathname;
    if (pathname.includes('pwd-admin')) document.getElementById('btnTabPwdAdmin')?.click();
    else if (pathname.includes('driver-madt')) document.getElementById('btnTabDriverMadt')?.click();
    else if (pathname.includes('bus-edge')) document.getElementById('btnTabBusEdge')?.click();
    else if (pathname.includes('cloud-deploy')) document.getElementById('btnTabCloudDeploy')?.click();
  }

  function getTabElementId(tab) {
    switch (tab) {
      case 'police-hq': return 'viewPoliceHq';
      case 'pwd-admin': return 'viewPwdAdmin';
      case 'driver-madt': return 'viewDriverMadt';
      case 'bus-edge': return 'viewBusEdge';
      case 'cloud-deploy': return 'viewCloudDeploy';
      default: return 'viewPoliceHq';
    }
  }

  // -------------------------------------------------------------------------
  // 5. MAPS INITIALIZATION (LEAFLET.JS)
  // -------------------------------------------------------------------------
  function initLeafletMaps() {
    const defaultCenter = [13.0720, 80.2580]; // Chennai Transit Corridor
    const defaultZoom = 13;

    // Load initial map provider (defaulting to Real OpenStreetMap 'osm' for rich real street views)
    const initialProviderKey = localStorage.getItem('roadvision_map_provider') || 'osm';
    state.mapProvider = initialProviderKey;
    const tileInfo = getTileUrlAndAttrib(initialProviderKey) || getTileUrlAndAttrib('osm');

    // 1. Police HQ Map
    if (document.getElementById('policeMap')) {
      policeMap = L.map('policeMap', { zoomControl: true }).setView(defaultCenter, defaultZoom);
      policeTileLayer = L.tileLayer(tileInfo.url, { attribution: tileInfo.attrib, maxZoom: tileInfo.maxZoom }).addTo(policeMap);
      drawRoutePolyline(policeMap, '#ef4444');
    }

    // 2. PWD Admin Map
    if (document.getElementById('pwdMap')) {
      pwdMap = L.map('pwdMap', { zoomControl: true }).setView(defaultCenter, defaultZoom);
      pwdTileLayer = L.tileLayer(tileInfo.url, { attribution: tileInfo.attrib, maxZoom: tileInfo.maxZoom }).addTo(pwdMap);
      drawRoutePolyline(pwdMap, '#00f3ff');
    }

    // 3. Driver MADT Radar Map
    if (document.getElementById('driverMap')) {
      driverMap = L.map('driverMap', { zoomControl: false }).setView([state.bus.lat, state.bus.lng], 14);
      driverTileLayer = L.tileLayer(tileInfo.url, { attribution: tileInfo.attrib, maxZoom: tileInfo.maxZoom }).addTo(driverMap);
      drawRoutePolyline(driverMap, '#10b981');

      driverScanCircle = L.circle([state.bus.lat, state.bus.lng], {
        radius: 250,
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.1,
        weight: 1,
        dashArray: '4, 4'
      }).addTo(driverMap);
    }

    // Hook up all map provider selectors across all tabs
    document.querySelectorAll('.map-provider-select').forEach(sel => {
      sel.value = tileInfo.key;
      sel.addEventListener('change', (e) => {
        setAllMapTileLayers(e.target.value);
      });
    });

    // Hook up all "🔑 Key" buttons and Header "Real Map / Key" button
    document.querySelectorAll('.btn-open-map-key, #btnHeaderMapConfig').forEach(btn => {
      btn.addEventListener('click', openMapConfigModal);
    });

    // Map Controls
    document.getElementById('btnPolRecenter')?.addEventListener('click', () => policeMap?.setView(defaultCenter, 13));
    document.getElementById('btnPolRefreshMap')?.addEventListener('click', fetchAllData);
    document.getElementById('btnPwdRecenter')?.addEventListener('click', () => pwdMap?.setView(defaultCenter, 13));
    document.getElementById('btnPwdRefreshMap')?.addEventListener('click', fetchAllData);
  }

  function drawRoutePolyline(mapInstance, strokeColor) {
    const latlngs = ROUTE_WAYPOINTS.map(w => [w.lat, w.lng]);
    L.polyline(latlngs, {
      color: strokeColor,
      weight: 3,
      opacity: 0.55,
      dashArray: '6, 6'
    }).addTo(mapInstance);
  }

  function createCustomIcon(emoji, bgClass) {
    return L.divIcon({
      className: 'custom-leaflet-marker',
      html: `<div class="marker-bubble ${bgClass}"><span>${emoji}</span></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });
  }

  const busIcon = L.divIcon({
    className: 'custom-bus-marker',
    html: `<div class="bus-marker-bubble"><span>🚌</span></div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18]
  });

  // -------------------------------------------------------------------------
  // 6. DATA FETCHING & SYNCHRONIZATION
  // -------------------------------------------------------------------------
  async function fetchAllData() {
    await fetchIncidentsAndGeofences();
    await fetchKpis();
  }

  async function fetchIncidentsAndGeofences() {
    try {
      // 1. Fetch Police HQ incidents
      const resPol = await fetch('/api/police-hq/incidents');
      if (resPol.ok) {
        const data = await resPol.json();
        state.policeIncidents = data.incidents || [];
        renderPoliceQueue();
      }

      // 2. Fetch PWD incidents
      const resPwd = await fetch('/api/pwd/incidents');
      if (resPwd.ok) {
        const data = await resPwd.json();
        state.pwdIncidents = data.incidents || [];
        renderPwdQueue();
      }

      // 3. Fetch active geofences
      const resGeo = await fetch('/api/geofences/active');
      if (resGeo.ok) {
        const data = await resGeo.json();
        state.activeGeofences = data.geofences || [];
        const geofenceCountEl = document.getElementById('activeGeofenceCount');
        if (geofenceCountEl) geofenceCountEl.textContent = data.total_active || 0;
      }

      // Update Map Layers
      updateMapGeofenceLayers();
    } catch (err) {
      console.warn('API Sync notice:', err);
    }
  }

  async function fetchKpis() {
    try {
      const res = await fetch('/api/kpi-summary');
      if (res.ok) {
        const kpi = await res.json();
        if (kpi.police) {
          document.getElementById('polKpiTotal').textContent = kpi.police.total || 0;
          document.getElementById('polKpiActive').textContent = kpi.police.active || 0;
          document.getElementById('polKpiAck').textContent = kpi.police.acknowledged || 0;
          document.getElementById('polKpiRepaired').textContent = kpi.police.repaired || 0;
        }
        if (kpi.pwd) {
          document.getElementById('pwdKpiTotal').textContent = kpi.pwd.total || 0;
          document.getElementById('pwdKpiActive').textContent = kpi.pwd.active || 0;
          document.getElementById('pwdKpiAck').textContent = kpi.pwd.acknowledged || 0;
          document.getElementById('pwdKpiRepaired').textContent = kpi.pwd.repaired || 0;
        }
      }
    } catch (e) {
      console.warn('KPI error:', e);
    }
  }

  // -------------------------------------------------------------------------
  // 7. GEOFENCE MAP RENDERING
  // -------------------------------------------------------------------------
  function updateMapGeofenceLayers() {
    // 1. Police Map (only non-cleared accident/traffic incidents)
    if (policeMap) {
      policeGeofenceLayers.forEach(l => policeMap.removeLayer(l));
      policeGeofenceLayers = [];

      state.policeIncidents.forEach(inc => {
        if (['REPAIRED', 'CLEARED'].includes(inc.status)) return;

        const circleColor = inc.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b';
        const circle = L.circle([inc.lat, inc.lng], {
          radius: inc.geofence_radius || 170,
          color: circleColor,
          fillColor: circleColor,
          fillOpacity: 0.2,
          weight: 2,
          dashArray: '5, 5'
        }).addTo(policeMap);

        const emoji = getHazardEmoji(inc.hazard_type);
        const marker = L.marker([inc.lat, inc.lng], {
          icon: createCustomIcon(emoji, 'marker-police')
        }).addTo(policeMap);

        marker.on('click', () => openIncidentModal(inc));
        circle.on('click', () => openIncidentModal(inc));

        policeGeofenceLayers.push(circle, marker);
      });

      if (!policeBusMarker) {
        policeBusMarker = L.marker([state.bus.lat, state.bus.lng], { icon: busIcon }).addTo(policeMap);
      } else {
        policeBusMarker.setLatLng([state.bus.lat, state.bus.lng]);
      }
    }

    // 2. PWD Map (only non-repaired road defects)
    if (pwdMap) {
      pwdGeofenceLayers.forEach(l => pwdMap.removeLayer(l));
      pwdGeofenceLayers = [];

      state.pwdIncidents.forEach(inc => {
        if (['REPAIRED', 'CLEARED'].includes(inc.status)) return;

        const circleColor = inc.severity === 'CRITICAL' ? '#ef4444' : '#00f3ff';
        const circle = L.circle([inc.lat, inc.lng], {
          radius: inc.geofence_radius || 140,
          color: circleColor,
          fillColor: circleColor,
          fillOpacity: 0.2,
          weight: 2,
          dashArray: '5, 5'
        }).addTo(pwdMap);

        const emoji = getHazardEmoji(inc.hazard_type);
        const marker = L.marker([inc.lat, inc.lng], {
          icon: createCustomIcon(emoji, 'marker-pwd')
        }).addTo(pwdMap);

        marker.on('click', () => openIncidentModal(inc));
        circle.on('click', () => openIncidentModal(inc));

        pwdGeofenceLayers.push(circle, marker);
      });

      if (!pwdBusMarker) {
        pwdBusMarker = L.marker([state.bus.lat, state.bus.lng], { icon: busIcon }).addTo(pwdMap);
      } else {
        pwdBusMarker.setLatLng([state.bus.lat, state.bus.lng]);
      }
    }

    // 3. Driver MADT Map
    if (driverMap) {
      driverGeofenceLayers.forEach(l => driverMap.removeLayer(l));
      driverGeofenceLayers = [];

      state.activeGeofences.forEach(geo => {
        const circleColor = geo.category === 'POLICE' ? '#ef4444' : '#00f3ff';
        const circle = L.circle([geo.lat, geo.lng], {
          radius: geo.geofence_radius || 160,
          color: circleColor,
          fillColor: circleColor,
          fillOpacity: 0.22,
          weight: 2
        }).addTo(driverMap);

        const emoji = getHazardEmoji(geo.hazard_type);
        const marker = L.marker([geo.lat, geo.lng], {
          icon: createCustomIcon(emoji, geo.category === 'POLICE' ? 'marker-police' : 'marker-pwd')
        }).addTo(driverMap);

        driverGeofenceLayers.push(circle, marker);
      });

      if (!driverBusMarker) {
        driverBusMarker = L.marker([state.bus.lat, state.bus.lng], { icon: busIcon }).addTo(driverMap);
      } else {
        driverBusMarker.setLatLng([state.bus.lat, state.bus.lng]);
      }

      if (driverScanCircle) {
        driverScanCircle.setLatLng([state.bus.lat, state.bus.lng]);
      }
    }
  }

  function getHazardEmoji(hazardType) {
    switch (hazardType) {
      case 'accident_collision': return '💥';
      case 'traffic_congestion': return '🚗';
      case 'signal_failure': return '🚦';
      case 'illegal_parking': return '⛔';
      case 'pothole': return '🕳️';
      case 'faded_zebra': return '🦓';
      case 'open_manhole': return '⭕';
      default: return '⚠️';
    }
  }

  // -------------------------------------------------------------------------
  // 8. QUEUE RENDERING (POLICE & PWD)
  // -------------------------------------------------------------------------
  function renderPoliceQueue() {
    const container = document.getElementById('policeIncidentList');
    if (!container) return;

    let incidents = state.policeIncidents;
    const countActive = incidents.filter(i => i.status === 'ACTIVE').length;
    const countAck = incidents.filter(i => i.status === 'ACKNOWLEDGED').length;
    const countRepaired = incidents.filter(i => ['REPAIRED', 'CLEARED'].includes(i.status)).length;

    document.getElementById('polCountActive').textContent = countActive;
    document.getElementById('polCountAck').textContent = countAck;
    document.getElementById('polCountRepaired').textContent = countRepaired;

    if (state.filterPolice !== 'ALL') {
      incidents = incidents.filter(i => i.status === state.filterPolice);
    }

    document.getElementById('polQueueCount').textContent = `${incidents.length} Incidents`;

    if (incidents.length === 0) {
      container.innerHTML = `<div class="empty-state-box">No ${state.filterPolice.toLowerCase()} Police traffic incidents registered.</div>`;
      return;
    }

    container.innerHTML = incidents.map(inc => createIncidentCardHtml(inc, 'POLICE')).join('');
    bindIncidentCardActions(container, 'POLICE');
  }

  function renderPwdQueue() {
    const container = document.getElementById('pwdIncidentList');
    if (!container) return;

    let incidents = state.pwdIncidents;
    const countActive = incidents.filter(i => i.status === 'ACTIVE').length;
    const countAck = incidents.filter(i => i.status === 'ACKNOWLEDGED').length;
    const countRepaired = incidents.filter(i => ['REPAIRED', 'CLEARED'].includes(i.status)).length;

    document.getElementById('pwdCountActive').textContent = countActive;
    document.getElementById('pwdCountAck').textContent = countAck;
    document.getElementById('pwdCountRepaired').textContent = countRepaired;

    if (state.filterPwd !== 'ALL') {
      incidents = incidents.filter(i => i.status === state.filterPwd);
    }

    document.getElementById('pwdQueueCount').textContent = `${incidents.length} Defects`;

    if (incidents.length === 0) {
      container.innerHTML = `<div class="empty-state-box">No ${state.filterPwd.toLowerCase()} Road defects registered.</div>`;
      return;
    }

    container.innerHTML = incidents.map(inc => createIncidentCardHtml(inc, 'PWD')).join('');
    bindIncidentCardActions(container, 'PWD');
  }

  function createIncidentCardHtml(inc, category) {
    const statusClass = inc.status.toLowerCase();
    const tagClass = `tag-${statusClass}`;
    const isPolice = category === 'POLICE';
    const imgUrl = inc.image_url || (isPolice ? '/static/samples/police_accident_collision.jpg' : '/static/samples/pothole_severe.jpg');
    const ackLabel = isPolice ? '🚓 Dispatch Patrol' : '👁️ Schedule Repair';
    const clearLabel = isPolice ? '🟢 Mark Cleared (Reopen Road)' : '🛠️ Mark as Repaired';

    return `
      <div class="incident-card status-${statusClass}" data-id="${inc.id}">
        <div class="inc-top-row">
          <span class="inc-id">${inc.id}</span>
          <span class="inc-status-tag ${tagClass}">${inc.status === 'REPAIRED' && isPolice ? 'CLEARED' : inc.status}</span>
        </div>
        <div class="inc-main">
          <img src="${imgUrl}" class="inc-thumb" alt="Thumbnail" data-action="view-modal" />
          <div class="inc-content">
            <h4 class="inc-title">${inc.title}</h4>
            <p class="inc-desc">${inc.description || ''}</p>
          </div>
        </div>
        <div class="inc-meta-row">
          <span class="inc-meta-item">📍 <strong>${inc.address || 'Transit Corridor'}</strong></span>
          <span class="inc-meta-item">⚠️ <strong>${inc.severity}</strong></span>
          <span class="inc-meta-item">⭕ Geofence: <strong>${inc.geofence_radius}m</strong></span>
        </div>
        <div class="inc-actions-row">
          ${inc.status === 'ACTIVE' ? `<button class="btn-card-action btn-card-ack" data-action="ack" data-id="${inc.id}">${ackLabel}</button>` : ''}
          ${!['REPAIRED', 'CLEARED'].includes(inc.status) ? `<button class="btn-card-action btn-card-repair" data-action="repair" data-id="${inc.id}">${clearLabel}</button>` : '<span class="badge badge-emerald">✔ Resolved & Geofence Cleared</span>'}
          <button class="btn-card-action btn-card-locate" data-action="locate" data-lat="${inc.lat}" data-lng="${inc.lng}">📍 Locate</button>
        </div>
      </div>
    `;
  }

  function bindIncidentCardActions(container, category) {
    const pillContainer = category === 'POLICE' ? document.getElementById('polFilterPills') : document.getElementById('pwdFilterPills');
    if (pillContainer) {
      pillContainer.querySelectorAll('.filter-pill').forEach(pill => {
        pill.onclick = () => {
          pillContainer.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          if (category === 'POLICE') {
            state.filterPolice = pill.dataset.filter;
            renderPoliceQueue();
          } else {
            state.filterPwd = pill.dataset.filter;
            renderPwdQueue();
          }
        };
      });
    }

    container.querySelectorAll('[data-action]').forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const action = btn.dataset.action;
        const id = btn.dataset.id;

        if (action === 'ack') {
          await acknowledgeIncident(id, category);
        } else if (action === 'repair') {
          await repairIncident(id, category);
        } else if (action === 'locate') {
          const lat = parseFloat(btn.dataset.lat);
          const lng = parseFloat(btn.dataset.lng);
          const map = category === 'POLICE' ? policeMap : pwdMap;
          if (map) map.flyTo([lat, lng], 16, { duration: 1.2 });
        } else if (action === 'view-modal') {
          const inc = (category === 'POLICE' ? state.policeIncidents : state.pwdIncidents).find(i => i.id === id);
          if (inc) openIncidentModal(inc);
        }
      };
    });
  }

  // -------------------------------------------------------------------------
  // 9. ACTIONS: ACKNOWLEDGE & CLEAR / REPAIR (REMOVES GEOFENCE)
  // -------------------------------------------------------------------------
  async function acknowledgeIncident(incidentId, category) {
    const endpoint = category === 'POLICE'
      ? `/api/police-hq/incidents/${incidentId}/acknowledge`
      : `/api/pwd/incidents/${incidentId}/acknowledge`;

    try {
      const res = await fetch(endpoint, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor_name: `${category} Officer`, notes: 'Patrol dispatched to site.' })
      });

      if (res.ok) {
        showToast(`✔ Incident ${incidentId} marked as Acknowledged / Patrol Dispatched.`, category.toLowerCase());
        await fetchAllData();
      }
    } catch (err) {
      console.error('Ack error:', err);
    }
  }

  async function repairIncident(incidentId, category) {
    const endpoint = category === 'POLICE'
      ? `/api/police-hq/incidents/${incidentId}/repair`
      : `/api/pwd/incidents/${incidentId}/repair`;

    try {
      const res = await fetch(endpoint, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor_name: `${category} Unit`, notes: 'Road cleared and reopened.' })
      });

      if (res.ok) {
        const msg = category === 'POLICE'
          ? `🎉 Traffic incident ${incidentId} CLEARED & REOPENED! Geofence removed from bus radar.`
          : `🎉 Road defect ${incidentId} REPAIRED! Geofence removed from bus radar.`;
        showToast(msg, 'repair');
        await fetchAllData();
        updateDriverProximityHUD();
      }
    } catch (err) {
      console.error('Repair error:', err);
    }
  }

  // -------------------------------------------------------------------------
  // 10. DRIVER MADT (MOUNTED ALERT DISPLAY TERMINAL) HUD
  // -------------------------------------------------------------------------
  function initDriverCockpitControls() {
    const btnSimDrive = document.getElementById('btnToggleSimDrive');
    const btnResetPos = document.getElementById('btnResetBusPos');
    const sliderSpeed = document.getElementById('sliderBusSpeed');
    const btnAudio = document.getElementById('btnMadtAudioToggle');
    const btnAck = document.getElementById('btnDriverAck');
    const btnSos = document.getElementById('btnDriverSos');

    btnSimDrive?.addEventListener('click', () => {
      state.bus.isDriving = !state.bus.isDriving;
      if (state.bus.isDriving) {
        document.getElementById('simDriveIcon').textContent = '⏸️';
        document.getElementById('simDriveText').textContent = 'Pause Bus Simulation';
        btnSimDrive.classList.add('active-pulse');
        startSimulatedDriving();
        showToast('🚌 Simulated Bus Route Driving Active!', 'police');
      } else {
        document.getElementById('simDriveIcon').textContent = '▶️';
        document.getElementById('simDriveText').textContent = 'Resume Simulated Route';
        btnSimDrive.classList.remove('active-pulse');
        clearInterval(state.bus.driveInterval);
      }
    });

    btnResetPos?.addEventListener('click', () => {
      state.bus.currentWaypointIdx = 0;
      const startPt = ROUTE_WAYPOINTS[0];
      state.bus.lat = startPt.lat;
      state.bus.lng = startPt.lng;
      updateDriverProximityHUD();
      if (driverMap) driverMap.setView([state.bus.lat, state.bus.lng], 15);
      showToast('🔄 Bus reset to Central Station Terminal', 'police');
    });

    sliderSpeed?.addEventListener('input', (e) => {
      const speed = parseFloat(e.target.value);
      state.bus.speedKmh = speed;
      document.getElementById('madtSpeedDisplay').textContent = Math.round(speed);
      updateSpeedSvgGauge(speed);
    });

    btnAudio?.addEventListener('click', () => {
      state.audioEnabled = !state.audioEnabled;
      if (state.audioEnabled) {
        btnAudio.classList.add('active');
        document.getElementById('audioIcon').textContent = '🔊';
        document.getElementById('audioStatusText').textContent = 'BUZZER ON';
        showToast('🔊 Cabin Warning Voice & Buzzer ON', 'police');
      } else {
        btnAudio.classList.remove('active');
        document.getElementById('audioIcon').textContent = '🔇';
        document.getElementById('audioStatusText').textContent = 'MUTED';
        showToast('🔇 Cabin Audio Muted', 'pwd');
      }
    });

    btnAck?.addEventListener('click', () => {
      showToast('👍 Driver Acknowledged Hazard Warning.', 'police');
    });

    btnSos?.addEventListener('click', () => {
      document.getElementById('btnTabBusEdge')?.click();
      document.getElementById('btnInjectCustomHazard')?.click();
    });
  }

  function startSimulatedDriving() {
    clearInterval(state.bus.driveInterval);
    state.bus.driveInterval = setInterval(() => {
      if (!state.bus.isDriving) return;

      const targetPt = ROUTE_WAYPOINTS[state.bus.currentWaypointIdx];
      const dist = calculateDistanceMeters(state.bus.lat, state.bus.lng, targetPt.lat, targetPt.lng);

      if (dist < 30) {
        state.bus.currentWaypointIdx = (state.bus.currentWaypointIdx + 1) % ROUTE_WAYPOINTS.length;
      } else {
        const step = (state.bus.speedKmh / 3.6) * 0.4;
        const ratio = Math.min(step / dist, 1);
        state.bus.lat += (targetPt.lat - state.bus.lat) * ratio;
        state.bus.lng += (targetPt.lng - state.bus.lng) * ratio;
      }

      updateDriverProximityHUD();
    }, 400);
  }

  function updateDriverProximityHUD() {
    const coordsEl = document.getElementById('madtGpsCoords');
    if (coordsEl) coordsEl.textContent = `${state.bus.lat.toFixed(4)}° N, ${state.bus.lng.toFixed(4)}° E`;

    if (driverBusMarker) driverBusMarker.setLatLng([state.bus.lat, state.bus.lng]);
    if (driverScanCircle) driverScanCircle.setLatLng([state.bus.lat, state.bus.lng]);
    if (policeBusMarker) policeBusMarker.setLatLng([state.bus.lat, state.bus.lng]);
    if (pwdBusMarker) pwdBusMarker.setLatLng([state.bus.lat, state.bus.lng]);

    // Find closest active geofence ahead
    let closestHazard = null;
    let minDistance = Infinity;

    const nearbyHazards = [];

    state.activeGeofences.forEach(geo => {
      const dist = calculateDistanceMeters(state.bus.lat, state.bus.lng, geo.lat, geo.lng);
      nearbyHazards.push({ ...geo, distance: Math.round(dist) });
      if (dist < minDistance) {
        minDistance = dist;
        closestHazard = geo;
      }
    });

    nearbyHazards.sort((a, b) => a.distance - b.distance);
    renderApproachingHazardsList(nearbyHazards);

    const banner = document.getElementById('madtAlertBanner');
    const icon = document.getElementById('madtAlertIcon');
    const badge = document.getElementById('madtAlertBadge');
    const headline = document.getElementById('madtAlertHeadline');
    const subtext = document.getElementById('madtAlertSubtext');
    const distBox = document.getElementById('madtDistanceContainer');
    const distVal = document.getElementById('madtDistanceVal');
    const distBar = document.getElementById('madtDistBar');
    const recText = document.getElementById('madtActionRec');

    if (!banner) return;

    if (closestHazard && minDistance < 280) {
      const isCritical = closestHazard.severity === 'CRITICAL' || minDistance < 120;
      banner.className = `madt-alert-banner ${isCritical ? 'alert-state-danger' : 'alert-state-caution'}`;
      icon.textContent = isCritical ? '🚨' : '⚠️';
      badge.textContent = isCritical ? 'CRITICAL HAZARD AHEAD' : 'CAUTION ADVISED';
      headline.textContent = `${closestHazard.title.toUpperCase()}`;
      subtext.textContent = `Geofenced ${closestHazard.category} zone at ${closestHazard.address || 'Transit Corridor'}. Follow diversion directives.`;

      if (distBox) distBox.style.display = 'flex';
      if (distVal) distVal.textContent = `${Math.round(minDistance)} m`;

      const barPct = Math.max(0, Math.min(100, 100 - (minDistance / 280) * 100));
      if (distBar) distBar.style.width = `${barPct}%`;

      if (recText) {
        recText.textContent = isCritical ? '⚠️ REDUCE SPEED TO 15 KM/H & SWITCH LANES' : '⚠️ CAUTION: SLOW DOWN TO 25 KM/H';
      }

      // Voice Audio Alert
      if (state.audioEnabled && state.lastSpokenAlertId !== closestHazard.id && minDistance < 200) {
        speakAlert(`Warning! Approaching ${closestHazard.hazard_type.replace('_', ' ')} in ${Math.round(minDistance)} meters.`);
        state.lastSpokenAlertId = closestHazard.id;
      }
    } else {
      banner.className = 'madt-alert-banner alert-state-safe';
      icon.textContent = '🛡️';
      badge.textContent = 'ROUTE SAFE & CLEAR';
      headline.textContent = 'NO IMMEDIATE ACCIDENTS OR GEOFENCED HAZARDS AHEAD';
      subtext.textContent = 'Real-time geofence proximity engine scanning 300 meters forward on navigation trajectory.';
      if (distBox) distBox.style.display = 'none';
    }
  }

  function renderApproachingHazardsList(hazards) {
    const container = document.getElementById('madtApproachingList');
    const countEl = document.getElementById('madtUpcomingCount');
    if (!container) return;

    const nearItems = hazards.filter(h => h.distance < 800);
    if (countEl) countEl.textContent = `${nearItems.length} Nearby`;

    if (nearItems.length === 0) {
      container.innerHTML = '<div class="no-hazards-msg">Scanning forward corridor... (All clear)</div>';
      return;
    }

    container.innerHTML = nearItems.map(h => `
      <div class="approaching-item">
        <span>${getHazardEmoji(h.hazard_type)} <strong>${h.title}</strong></span>
        <span class="mono-font accent-cyan">${h.distance}m</span>
      </div>
    `).join('');
  }

  function updateSpeedSvgGauge(speed) {
    const circle = document.getElementById('speedSvgProgress');
    if (!circle) return;

    const maxDash = 502; // circumference of r=80
    const ratio = Math.min(speed / 80, 1);
    const offset = maxDash - ratio * (maxDash * 0.75);
    circle.style.strokeDashoffset = offset;

    if (speed > 55) {
      circle.style.stroke = 'var(--accent-red)';
    } else if (speed > 40) {
      circle.style.stroke = 'var(--accent-amber)';
    } else {
      circle.style.stroke = 'var(--accent-emerald)';
    }
  }

  function speakAlert(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }

  // -------------------------------------------------------------------------
  // 11. BUS EDGE AI PERCEPTION & AES-256 LAB
  // -------------------------------------------------------------------------
  function initEdgePerceptionLab() {
    const buttons = document.querySelectorAll('#edgeSampleButtons .sample-pick-btn');
    const camImg = document.getElementById('edgeCamImage');
    const tag = document.getElementById('edgeHudDetectionTag');
    const btnTrigger = document.getElementById('btnTriggerEdgeAlert');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const sample = btn.dataset.sample;
        const simType = btn.dataset.sim;
        if (camImg) camImg.src = `/static/samples/${sample}`;

        const label = btn.textContent.trim();
        if (tag) tag.textContent = `AI DETECTED: ${label.toUpperCase()} (96%)`;

        updateCryptoInspectorScenario(simType, label);
      });
    });

    btnTrigger?.addEventListener('click', triggerEdgeAlertTransmission);
  }

  function updateCryptoInspectorScenario(simType, label) {
    const isPolice = ['accident_collision', 'traffic_congestion', 'signal_failure', 'illegal_parking'].includes(simType);
    const payload = {
      bus_id: state.bus.id,
      category: isPolice ? 'POLICE' : 'PWD',
      hazard_type: simType,
      title: label,
      severity: 'CRITICAL',
      lat: state.bus.lat,
      lng: state.bus.lng,
      geofence_radius: isPolice ? 180.0 : 140.0,
      speed_kmh: state.bus.speedKmh,
      confidence: 0.96
    };

    const plaintextEl = document.getElementById('jsonPlaintextPayload');
    if (plaintextEl) plaintextEl.textContent = JSON.stringify(payload, null, 2);
  }

  async function triggerEdgeAlertTransmission() {
    const activeSampleBtn = document.querySelector('#edgeSampleButtons .sample-pick-btn.active');
    const simType = activeSampleBtn?.dataset.sim || 'accident_collision';
    const label = activeSampleBtn?.textContent.trim() || 'Vehicle Collision (Police)';
    const isPolice = ['accident_collision', 'traffic_congestion', 'signal_failure', 'illegal_parking'].includes(simType);

    const payload = {
      bus_id: state.bus.id,
      category: isPolice ? 'POLICE' : 'PWD',
      hazard_type: simType,
      title: label,
      severity: 'CRITICAL',
      lat: state.bus.lat + 0.0008,
      lng: state.bus.lng + 0.0008,
      geofence_radius: isPolice ? 180.0 : 140.0,
      speed_kmh: state.bus.speedKmh,
      confidence: 0.96
    };

    try {
      // Step 1: Encrypt via backend crypto endpoint
      const res = await fetch('/api/bus/test-aes-crypto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const cryptData = await res.json();
        document.getElementById('dispKeyHex').textContent = cryptData.key_hex.slice(0, 32) + '...';
        document.getElementById('dispIvBase64').textContent = cryptData.iv_base64;
        document.getElementById('jsonCiphertextPayload').textContent = JSON.stringify(cryptData.encrypted_packet, null, 2);

        // Step 2: Transmit to Cloud Receiver
        const sendRes = await fetch('/api/bus/send-alert-encrypted', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cryptData.encrypted_packet)
        });

        if (sendRes.ok) {
          const cloudResp = await sendRes.json();
          document.getElementById('cloudVerifText').textContent =
            `Incident ${cloudResp.incident_id} registered. Geofence radius of ${cloudResp.geofence_created.radius_meters}m active. Assigned to ${cloudResp.assigned_authority}.`;

          showToast(`🔒 AES-256 Encrypted Alert transmitted to ${cloudResp.assigned_authority}!`, cloudResp.assigned_authority.toLowerCase());
          await fetchAllData();
        }
      }
    } catch (e) {
      console.error('Edge alert transmission error:', e);
    }
  }

  // -------------------------------------------------------------------------
  // 12. MODALS & UTILITIES
  // -------------------------------------------------------------------------
  let currentModalIncident = null;

  function initModals() {
    const modal = document.getElementById('incidentModal');
    const btnClose = document.getElementById('btnModalClose');

    const closeModal = () => {
      modal?.classList.remove('open');
      modal?.classList.remove('active');
    };

    btnClose?.addEventListener('click', closeModal);
    modal?.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    document.getElementById('btnModalAck')?.addEventListener('click', async () => {
      if (!currentModalIncident) return;
      await acknowledgeIncident(currentModalIncident.id, currentModalIncident.category);
      closeModal();
    });

    document.getElementById('btnModalRepair')?.addEventListener('click', async () => {
      if (!currentModalIncident) return;
      await repairIncident(currentModalIncident.id, currentModalIncident.category);
      closeModal();
    });

    // Custom Hazard Inject Modal
    const injectModal = document.getElementById('injectHazardModal');
    const closeInjectModal = () => {
      injectModal?.classList.remove('open');
      injectModal?.classList.remove('active');
    };

    document.getElementById('btnInjectCustomHazard')?.addEventListener('click', () => {
      injectModal?.classList.add('open');
      injectModal?.classList.add('active');
    });
    document.getElementById('btnInjectClose')?.addEventListener('click', closeInjectModal);

    document.getElementById('btnSubmitInjectHazard')?.addEventListener('click', async () => {
      const cat = document.getElementById('injectCategory').value;
      const haz = document.getElementById('injectHazardType').value;
      const title = document.getElementById('injectTitle').value;
      const sev = document.getElementById('injectSeverity').value;
      const rad = parseFloat(document.getElementById('injectRadius').value);
      const lat = parseFloat(document.getElementById('injectLat').value);
      const lng = parseFloat(document.getElementById('injectLng').value);

      const payload = {
        category: cat,
        hazard_type: haz,
        title: title,
        severity: sev,
        geofence_radius: rad,
        lat: lat,
        lng: lng,
        bus_id: state.bus.id,
        speed_kmh: state.bus.speedKmh
      };

      try {
        const cryptoRes = await fetch('/api/bus/test-aes-crypto', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (cryptoRes.ok) {
          const cryptPacket = await cryptoRes.json();
          await fetch('/api/bus/send-alert-encrypted', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cryptPacket.encrypted_packet)
          });

          showToast(`➕ Injected ${cat} Incident! Geofence established.`, cat.toLowerCase());
          closeInjectModal();
          await fetchAllData();
        }
      } catch (err) {
        console.error('Inject error:', err);
      }
    });

    document.getElementById('btnExportDbJson')?.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/cloud/export-db');
        if (res.ok) {
          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `raksha_ai_cloud_backup_${new Date().toISOString().slice(0, 10)}.json`;
          a.click();
          showToast('✔ Cloud database backup downloaded.', 'repair');
        }
      } catch (err) {
        console.error('Export error:', err);
      }
    });

    // Real Map & Mapbox API Key Modal
    const mapModal = document.getElementById('mapConfigModal');
    const closeMapModal = () => {
      mapModal?.classList.remove('open');
      mapModal?.classList.remove('active');
    };

    document.getElementById('btnMapConfigClose')?.addEventListener('click', closeMapModal);

    document.getElementById('btnSaveMapConfig')?.addEventListener('click', () => {
      const selectedProvider = document.getElementById('modalMapProviderSelect').value;
      const mapboxKey = (document.getElementById('inputMapboxApiKey').value || '').trim();
      if (mapboxKey) {
        localStorage.setItem('roadvision_mapbox_key', mapboxKey);
      }
      setAllMapTileLayers(selectedProvider);
      closeMapModal();
    });

    document.getElementById('btnQuickSwitchOsm')?.addEventListener('click', () => {
      setAllMapTileLayers('osm');
      closeMapModal();
    });
  }

  function openMapConfigModal() {
    const modal = document.getElementById('mapConfigModal');
    if (!modal) return;
    const currentProvider = state.mapProvider || localStorage.getItem('roadvision_map_provider') || 'osm';
    const currentKey = localStorage.getItem('roadvision_mapbox_key') || '';
    const sel = document.getElementById('modalMapProviderSelect');
    if (sel) sel.value = currentProvider;
    const inp = document.getElementById('inputMapboxApiKey');
    if (inp) inp.value = currentKey;

    modal.classList.add('open');
    modal.classList.add('active');
  }

  function openIncidentModal(inc) {
    currentModalIncident = inc;
    const modal = document.getElementById('incidentModal');
    if (!modal) return;

    const isPolice = inc.category === 'POLICE';
    document.getElementById('modalCatBadge').textContent = inc.category;
    document.getElementById('modalTitle').textContent = inc.title;
    document.getElementById('modalId').textContent = inc.id;
    document.getElementById('modalSeverity').textContent = inc.severity;
    document.getElementById('modalAddress').textContent = inc.address || 'Transit Corridor';
    document.getElementById('modalGps').textContent = `${inc.lat.toFixed(4)}, ${inc.lng.toFixed(4)}`;
    document.getElementById('modalRadius').textContent = `${inc.geofence_radius || 160} meters`;
    document.getElementById('modalBus').textContent = `${inc.bus_id || 'BUS-104'} (${inc.speed_kmh || 40} km/h)`;
    document.getElementById('modalStatus').textContent = inc.status === 'REPAIRED' && isPolice ? 'CLEARED' : inc.status;
    document.getElementById('modalTime').textContent = inc.created_at || 'Just now';
    document.getElementById('modalDescription').textContent = inc.description || '';

    const img = document.getElementById('modalImg');
    if (img) img.src = inc.image_url || (isPolice ? '/static/samples/police_accident_collision.jpg' : '/static/samples/pothole_severe.jpg');

    const btnAck = document.getElementById('btnModalAck');
    const btnRepair = document.getElementById('btnModalRepair');
    if (btnAck) {
      btnAck.textContent = isPolice ? '🚓 Dispatch Patrol / Acknowledge' : '👁️ Schedule Repair Work Order';
      btnAck.style.display = inc.status === 'ACTIVE' ? 'block' : 'none';
    }
    if (btnRepair) {
      btnRepair.textContent = isPolice ? '🟢 Mark as Cleared / Reopen Road (Remove Geofence)' : '🛠️ Mark as Repaired (Remove Geofence)';
      btnRepair.style.display = !['REPAIRED', 'CLEARED'].includes(inc.status) ? 'block' : 'none';
    }

    modal.classList.add('open');
    modal.classList.add('active');
  }

  function showToast(message, type = 'police') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

})();
