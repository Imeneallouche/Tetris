import React from "react";
import { Search, Bell } from "lucide-react";

export default function Header() {
  return (
    <div className="bg-white border-b px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center flex-1">
          <div className="relative flex-1 max-w-2xl">
            <input
              type="text"
              placeholder="Chercher une commande"
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
            />
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Bell className="w-5 h-5 text-gray-500" />
          <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
        </div>
      </div>
    </div>
  );
}
