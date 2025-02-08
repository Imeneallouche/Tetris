import React, { useState } from 'react';
import { Search, Bell, Edit2 } from "lucide-react";

const Navbar = ({ title }) => {
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    "Nouvelle commande #1234",
    "Nouvelle commande #5678",
    "Nouvelle commande #9101"
  ]);

  const toggleNotification = () => {
    setIsNotificationOpen(!isNotificationOpen);
  };

  return (
    <div className="flex justify-between items-center mb-8 pt-8 px-4 py-5 shadow-md">
      <div className="flex items-center space-x-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Chercher une commande"
            className="pl-10 pr-4 py-2 border rounded-lg w-64"
          />
          <Search className="w-4 h-4 absolute right-3 top-3 text-gray-400" />
        </div>
        <h1 className="text-2xl font-medium">{title}</h1>
      </div>
      <div className="flex items-center space-x-4">
        <nav className="flex space-x-4">
          <NavItem label="Commandes" />
          <NavItem label="Planification" />
          <NavItem label="Historique" />
          <NavItem label="Statistiques" active />
        </nav>
        <button className="p-2 relative" onClick={toggleNotification}>
          <Bell className="w-5 h-5 text-gray-600" />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        {isNotificationOpen && (
          <div className="absolute right-4 mt-40 w-64 bg-white border z-50 border-gray-200 rounded-lg shadow-lg">
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-900">Notifications</h3>
              <ul className="mt-2">
                {notifications.map((notification, index) => (
                  <li key={index} className="text-sm text-gray-700 py-1">
                    {notification}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const NavItem = ({ label, active }) => (
  <button className={`px-3 py-1 text-sm ${active ? "text-gray-900" : "text-gray-600"}`}>
    {label}
  </button>
);

export default Navbar;