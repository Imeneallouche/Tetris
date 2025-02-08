import React, { useState } from "react";
import { Responsive, WidthProvider } from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import Input from "../../components/ui/input";
import { Link, useNavigate } from 'react-router-dom';
import Header from "../../components/header";
import { Search, Bell, Alert, Truck, Info, AlertCircle  } from "lucide-react";
import Navbar from "../../components/navbar";

const ResponsiveGridLayout = WidthProvider(Responsive);

const initialTrucks = [
  {
    id: "truck1",
    name: "Camion A",
    driver: "Ali Ben",
    cost: "5000 DA",
    start: 1,
    hasSupplierNotification: false,
    orders: [
      { color: "#3b82f6", size: 3, label: "C3" },
      { color: "#22c55e", size: 4, label: "C4" },
    ],
  },
  {
    id: "truck2",
    name: "Camion B",
    driver: "Karim Said",
    cost: "4500 DA",
    start: 3,
    hasSupplierNotification: true,
    supplierInfo: {
      location: "Zone Industrielle Est",
      optimizationDetails: "Possibilité de passage par fournisseur",
      timeWindow: "14h30 - 15h30"
    },
    orders: [
      { color: "#3b82f6", size: 2, label: "C10" },
      { color: "#22c55e", size: 1, label: "C8" },
    ],
  },
  {
    id: "truck3",
    name: "Camion C",
    driver: "Mohamed Ali",
    cost: "4800 DA",
    start: 9,
    hasSupplierNotification: true,
    supplierInfo: {
      location: "Zone Industrielle Nord",
      optimizationDetails: "Possibilité de passage par fournisseur",
      timeWindow: "13h30 - 14h30"
    },
    orders: [
      { color: "#f97316", size: 3, label: "C9" },
      { color: "#6b7280", size: 5, label: "C15" },
    ],
  },
  {
    //N'affiche pas le camion lorsqu'il n'a aucune commande
    id: "truck4",
    name: "Camion D",
    driver: "Hassan Ahmed",
    cost: "4700 DA",
    start: 8,
    hasSupplierNotification: false,
    orders: [],
  },
];

const GanttTruckScheduler = () => {
  const [trucks, setTrucks] = useState(initialTrucks);
  const [hoveredTruck, setHoveredTruck] = useState(null);
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [showSupplierPopup, setShowSupplierPopup] = useState(false);
  const columnWidth = 100;
  const navigate = useNavigate();

  const trucksWithOrders = trucks.filter((truck) => truck.orders && truck.orders.length > 0);

  const layout = trucksWithOrders.map((truck) => ({
    i: truck.id,
    x: truck.start,
    y: trucksWithOrders.indexOf(truck),
    w: truck.orders.reduce((acc, order) => acc + order.size, 0),
    h: 1,
  }));

  const handleNotificationClick = (truck, event) => {
    event.stopPropagation();
    setSelectedTruck(truck);
    setShowSupplierPopup(true);
  };

  const SupplierPopup = ({ truck, onClose }) => {
    if (!truck) return null;
  
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-3xl p-6 w-[vh] relative">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-2">
              <Truck className="h-5 w-5" />
              <span className="font-medium">Solo truck up 18</span>
            </div>
            <button 
              onClick={onClose}
              className="hover:bg-gray-100 rounded-full p-1"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
  
          {/* Warning Message */}
          <div className="flex items-center gap-2 text-red-500 mb-4">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">Possibilité de passage par fournisseur</span>
          </div>
  
          {/* "Plus de details" Link */}
          <div className="mb-6">
            <a href="#" className="text-blue-600 hover:underline text-sm">
              Moins de détails
            </a>
          </div>
  
          {/* Content Grid */}
          <div className="grid grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <div className="bg-white outline outline-1 outline-gray-400 rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-600 mb-2">
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 6v6l4 2" />
                  </svg>
                  <span>Fournisseur</span>
                </div>
                <span className="font-medium">Ifri</span>
              </div>
  
              <div className="bg-white outline outline-1 outline-gray-400 rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-600 mb-2">
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  <span>Localisation</span>
                </div>
                <span className="font-medium">27 RUE AKID AMIROUCHE, AZAZGA</span>
              </div>
  
              <div className="bg-white outline outline-1 outline-gray-400 rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-600 mb-2">
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 6v6l4 2" />
                  </svg>
                  <span>Heure de livraison</span>
                </div>
                <span className="font-medium">15:45</span>
              </div>
            </div>
  
            {/* Right Column */}
            <div className="bg-white outline outline-1 outline-gray-400 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-4">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 12v7H4v-7M4 7h16m-8-3v16M3 3l18 18M21 3L3 21" />
                </svg>
                <span>Commande N°167</span>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Item 1</span>
                </div>
                <div className="text-xs text-gray-500 ml-4">
                  200 x 234 x 265 cm 15 kg
                </div>
                
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Item 2</span>
                </div>
                <div className="text-xs text-gray-500 ml-4">
                  150 x 134 x 150 cm 72 kg
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const generateTimeSlots = () => {
    const slots = [];
    for (let hour = 8; hour <= 18; hour++) {
      slots.push(`${hour}H`);
      slots.push(`${hour}H30`);
    }
    return slots;
  };

  const timeSlots = generateTimeSlots();
  const currentTime = new Date();
  const currentHour = currentTime.getHours();
  const currentMinute = currentTime.getMinutes();
  const currentTimePosition = ((currentHour - 8) * 2 + Math.floor(currentMinute / 30)) * 100;

  return (
    <div className="p-4 h-screen w-2/4">
      <Navbar title={""} />

      <div className="flex justify-between items-center mb-4">
        <h1 className="text-4xl font-semibold">Planification</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span>Capacité entrepôt : </span>
            <Input className="w-20" value="4" readOnly />
          </div>
        </div>
      </div>

      <div className="flex flex-col relative">
        <div className="absolute top-0 bottom-0 left-4 right-0 pointer-events-none">
          {timeSlots.map((_, index) => (
            <div
              key={index}
              className="absolute top-0 bottom-0 border-l"
              style={{
                left: `${index * 100}px`,
                borderStyle: index % 2 === 0 ? "dashed" : "none",
                borderColor: "#e5e7eb",
              }}
            />
          ))}
          <div
            className="absolute top-0 bottom-0 border-l-2 border-red-500"
            style={{
              left: `${currentTimePosition}px`,
              zIndex: 1,
            }}
          />
        </div>

        <div className="flex items-center justify-start ml-4">
          {timeSlots.map((time, index) => (
            <div
              key={index}
              className="text-center w-24 border-r border-gray-200 text-sm py-2"
            >
              {time}
            </div>
          ))}
        </div>

        <ResponsiveGridLayout
          className="layout"
          layouts={{ lg: layout }}
          breakpoints={{ lg: 1200 }}
          cols={{ lg: 24 }}
          rowHeight={80}
          margin={[0, 20]}
          isResizable={true}
        >
          {trucksWithOrders.map((truck) => (
            <div
              key={truck.id}
              className="truck relative"
              style={{
                width: "100%",
                height: "100%",
                cursor: "move",
              }}
              onMouseEnter={() => setHoveredTruck(truck.id)}
              onMouseLeave={() => setHoveredTruck(null)}
            >
              <div className="relative h-full flex items-center">
                <div className="absolute left-0 right-16 h-14 flex items-center">
                  <div className="w-full h-12 bg-gray-200 rounded-l-lg relative flex">
                    {truck.orders.map((order, index) => (
                      <div
                        key={index}
                        className="h-full flex items-center justify-center text-white font-bold relative"
                        style={{
                          width: `${(order.size / truck.orders.reduce((acc, order) => acc + order.size, 0)) * 100}%`,
                          backgroundColor: order.color,
                          borderRight: index < truck.orders.length - 1 ? "2px solid white" : "none",
                        }}
                      >
                        {order.label}
                      </div>
                    ))}
                    <div className="absolute -bottom-1 right-4 w-4 h-4 bg-black rounded-full border-2 border-gray-400" />
                    <div className="absolute -bottom-1 left-4 w-4 h-4 bg-black rounded-full border-2 border-gray-400" />
                  </div>
                </div>

                {/* Notification Icon */}
                {truck.hasSupplierNotification && (
                  <div 
                    className="absolute -top-3 -right-3 z-10 cursor-pointer"
                    onClick={(e) => handleNotificationClick(truck, e)}
                  >
                    <div className="bg-red-500 rounded-full p-1">
                      <Bell size={16} className="text-white" />
                    </div>
                  </div>
                )}

                <div className="absolute right-0 h-14 flex items-center">
                  <div className="relative">
                    <div
                      className="w-16 h-14 relative overflow-hidden"
                      style={{
                        clipPath: "polygon(0 0, 100% 20%, 100% 100%, 0 100%)"
                      }}
                    >
                      <div className="w-full h-full bg-gray-800" />
                    </div>
                    <div
                      className="absolute top-3 left-1 w-8 h-5 bg-blue-200"
                      style={{
                        clipPath: "polygon(0 0, 100% 20%, 100% 100%, 0 100%)"
                      }}
                    />
                    <div className="absolute -bottom-1 left-2 w-4 h-4 bg-black rounded-full border-2 border-gray-400" />
                    <div className="absolute -bottom-1 right-2 w-4 h-4 bg-black rounded-full border-2 border-gray-400" />
                  </div>
                </div>
              </div>

              {/* Hover Card */}
              {hoveredTruck === truck.id && (
                <div className="absolute left-0 -bottom-32 w-64 bg-white shadow-xl p-4 rounded-lg border z-50">
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Chauffeur: {truck.driver}</p>
                    <p className="text-sm text-gray-600">Coût: {truck.cost}</p>
                    <div className="flex gap-2 pt-2">
                      <button onClick={() => navigate('/itineraire')} className="flex-1 px-3 py-1.5 bg-white text-gray-900 text-sm rounded-xl hover:bg-gray-400 border border-gray-500">
                        Voir Itinéraire
                      </button>
                      <button onClick={() => navigate('/loading3d')} className="flex-1 px-3 py-1.5 bg-white text-gray-900 text-sm rounded-xl hover:bg-gray-400 border border-gray-500">
                        Chargement 3D
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </ResponsiveGridLayout>
      </div>

      <div className="flex justify-start mt-4 border-t">
        {timeSlots.map((_, index) => (
          <div
            key={index}
            className="w-24 border-r"
            style={{
              borderStyle: "dashed",
              borderColor: index % 2 === 0 ? "#e5e7eb" : "transparent",
              height: "20px",
            }}
          />
        ))}
      </div>

      {showSupplierPopup && (
        <SupplierPopup
          truck={selectedTruck}
          onClose={() => {
            setShowSupplierPopup(false);
            setSelectedTruck(null);
          }}
        />
      )}
    </div>
  );
};

export default GanttTruckScheduler;