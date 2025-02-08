import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import startImg from '../assets/livreur.png';
import userImg from '../assets/entrepot.png';

// Create custom icons
const startIcon = new L.Icon({
  iconUrl: startImg,
  iconSize: [50, 50],
  iconAnchor: [25, 50],
  popupAnchor: [0, -50]
});

const userIcon = new L.Icon({
  iconUrl: userImg,
  iconSize: [50, 50],
  iconAnchor: [25, 50],
  popupAnchor: [0, -50]
});

const MapComponent = ({ driverInfo }) => {
  const [userLocation, setUserLocation] = useState(null);
  const [routePoints, setRoutePoints] = useState([]);
  
  const startPoint = [
    driverInfo?.restaurantLat || 36.744138113208315,
    driverInfo?.restaurantLong || 4.369579979473619
  ];

  // Get user's current location
  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation([position.coords.latitude, position.coords.longitude]);
        },
        (error) => {
          console.error("Error getting location:", error);
        }
      );
    }
  }, []);

  // Fetch route when both locations are available
  useEffect(() => {
    const fetchRoute = async () => {
      if (!userLocation) return;
      
      try {
        const response = await fetch(
          `https://router.project-osrm.org/route/v1/driving/${startPoint[1]},${startPoint[0]};${userLocation[1]},${userLocation[0]}?overview=full&geometries=geojson`
        );
        const data = await response.json();
        
        if (data.routes && data.routes[0]) {
          setRoutePoints(data.routes[0].geometry.coordinates.map(coord => [coord[1], coord[0]]));
        }
      } catch (error) {
        console.error("Error fetching route:", error);
      }
    };

    fetchRoute();
  }, [userLocation, startPoint]);

  // Component to update map view
  const MapUpdater = () => {
    const map = useMap();
    
    useEffect(() => {
      if (userLocation && startPoint) {
        const bounds = L.latLngBounds([userLocation, startPoint]);
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    }, [map, userLocation]);

    return null;
  };

  return (
    <div className="w-full h-[600px]">
      <MapContainer
        center={startPoint}
        zoom={8}
        className="w-full h-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {/* Start point marker */}
        <Marker position={startPoint} icon={startIcon} />

        {/* User location marker */}
        {userLocation && (
          <Marker position={userLocation} icon={userIcon} />
        )}

        {/* Route line */}
        {routePoints.length > 0 && (
          <Polyline
            positions={routePoints}
            pathOptions={{ color: '#0F6CD9', weight: 6 }}
          />
        )}

        <MapUpdater />
      </MapContainer>
    </div>
  );
};

export default MapComponent;