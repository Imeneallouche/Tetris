import React from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Sidebare from "./components/sidebar"; // Sidebar
import Itineraire from "./pages/itinéraire"; // Page itinéraire
import Gantt from "./pages/Admin/chgmCamion"; // Page Gantt
import Chargement from "./pages/Admin/loading3d"; // Page chargement 3D
import Commande from "./pages/Admin/cmds";
import Stock from './components/charts'
import NewDelivery from './pages/Driver/NewlivraisonDriver';
import Appdriver from "./pages/Driver/Appdriver";

const App = () => {
  const location = useLocation(); // Utiliser useLocation pour obtenir la route actuelle

  const showSidebar = location.pathname !== "/loading3d"; // Condition pour afficher la sidebar

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Affiche la sidebar si ce n'est pas la page /loading3d */}
      {showSidebar && <Sidebare />}

      {/* Ajoute de la marge à gauche pour ne pas cacher le contenu sous la sidebar */}
      <div className={`flex-1 ${showSidebar ? 'ml-[50vh]' : 'ml-0'}`}>
        <Routes>
          <Route path="/" element={<Commande />} /> {/* Page d'accueil */}
          <Route path="/gant" element={<Gantt />} /> {/* Page pour voir la planification */}
          <Route path="/itineraire" element={<Itineraire />} /> {/* Page itinéraire */}
          <Route path="/loading3d" element={<Chargement />} /> {/* Page chargement 3D */}
          <Route path="/commandes" element={<Commande />} /> {/* Page liste des commandes à livrer */}
          <Route path="/stocks" element={<Stock />} /> {/* Page pour visualiser les stocks */}

        </Routes>
      </div>
    </div>
  );
};

export default App;

