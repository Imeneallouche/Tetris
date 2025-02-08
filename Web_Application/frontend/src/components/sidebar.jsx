import React from "react";
import { ChevronDown, Clock, Package, Calendar,  LogOut } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom"; // Importer useNavigate et useLocation

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="w-[45vh] fixed top-0 left-0 bg-white h-screen border-r flex flex-col justify-between">
      <div>
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <span className="font-medium">Nancy Martino</span>
            <ChevronDown className="w-4 h-4 text-gray-500" />
          </div>
        </div>
        <div className="p-4">
          <h3 className="text-xs font-semibold text-gray-500 mb-4">DASHBOARDS</h3>
          <div className="space-y-2">
            <div className={`flex items-center p-2 rounded-lg cursor-pointer ${location.pathname === "/commandes" ? "bg-blue-50 text-blue-600" : "text-gray-600 hover:bg-gray-50"}`} onClick={() => navigate("/commandes")}>
              <Package className="w-5 h-5 mr-3" />
              <span>Commandes</span>
              <span className="ml-auto bg-white px-2 py-1 rounded text-xs">435</span>
            </div>
            <div className={`flex items-center p-2 rounded-lg cursor-pointer ${location.pathname === "/gant" ? "bg-blue-50 text-blue-600" : "text-gray-600 hover:bg-gray-50"}`} onClick={() => navigate("/gant")}>
              <Calendar className="w-5 h-5 mr-3" />
              <span>Planification</span>
              <span className="ml-auto bg-gray-100 px-2 py-1 rounded text-xs">5</span>
            </div>
            <div className={`flex items-center p-2 rounded-lg cursor-pointer ${location.pathname === "/stocks" ? "bg-blue-50 text-blue-600" : "text-gray-600 hover:bg-gray-50"}`} onClick={() => navigate("/stocks")}>
              <Clock className="w-5 h-5 mr-3" />
              <span>Stock</span>
              <span className="ml-auto bg-gray-100 px-2 py-1 rounded text-xs">2</span>
            </div>
          </div>
        </div>
      </div>
      <button className="flex items-center justify-center p-4 text-gray-600 hover:text-red-600 border-t w-full">
        <LogOut className="w-5 h-5 mr-2" />
        Déconnexion
      </button>
    </div>
  );
}

export default Sidebar;