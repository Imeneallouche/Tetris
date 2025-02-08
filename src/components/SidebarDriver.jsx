// components/Sidebar.jsx
import React from 'react';
import { Package, History } from 'lucide-react';

const SidebarDriver = () => {
  return (
    <aside className="w-64 bg-white border-r border-gray-200">
      <div className="p-4">
        <h1 className="text-xl font-bold">tetris.</h1>
      </div>
      <div className="p-4">
        <div className="text-sm text-gray-500">Nancy Martino</div>
      </div>
      <div className="mt-4">
        <h2 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          DASHBOARDS
        </h2>
        <nav className="mt-2">
          <a href="#" className="flex items-center px-4 py-2 text-sm bg-blue-50 text-blue-600">
            <Package className="h-5 w-5 mr-3" />
            Livraisons
            <span className="ml-auto bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full text-xs">
              5
            </span>
          </a>
          <a href="#" className="flex items-center px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
            <History className="h-5 w-5 mr-3" />
            Historique des livraisons
            <span className="ml-auto bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
              435
            </span>
          </a>
        </nav>
      </div>
    </aside>
  );
};

export default SidebarDriver;