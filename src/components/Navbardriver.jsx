// components/Navbar.jsx
import React from 'react';
import { Search, Bell } from 'lucide-react';

const NavbarDriver = () => {
  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center flex-1">
          <div className="relative w-96">
            <input
              type="text"
              placeholder="Chercher une livraison"
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
            />
            <Search className="absolute left-3 top-2.5 text-gray-400 h-5 w-5" />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Bell className="h-5 w-5 text-gray-500" />
          <div className="h-8 w-8 rounded-full bg-blue-500" />
        </div>
      </div>
    </nav>
  );
};

export default NavbarDriver;