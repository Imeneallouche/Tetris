import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import { Search, Bell, Edit2 } from "lucide-react";
import { Card, CardContent } from "../components/ui/card";

const stockData = [
  { name: "Jul 2023", value: 4450 },
  { name: "Aug 2023", value: 4440 },
  { name: "Sep 2023", value: 4250 },
  { name: "Oct 2023", value: 4580 },
  { name: "Nov 2023", value: 4450 }
];

const Details = () => (
  <div className="w-full max-w-lg p-12 bg-white rounded-lg">
    <div className="flex justify-between items-center mb-4">
      <h2 className="text-lg top-0 bottom-2 font-medium">Details</h2>
      <button className="text-gray-400">•••</button>
    </div>
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4"> {/* Affichage en deux colonnes */}
        <DetailRow label="S&P500" value="S&P500" />
        <DetailRow label="Entrepot" value="Alger centre" />
        <DetailRow label="Date de mise à jour" value="08/02/2025" />
        <DetailRow label="Nombre total d'articles" value="120000 unités" />
        <DetailRow label="Valeur totale du stock" value="25 600 000 DZD" />
        <DetailRow label="Produit le plus stocké" value="Prod1" />
        <DetailRow label="Capacité utilisé" value="85%" />
        <DetailRow label="Produits proches de la rupture" value="Prod3" />
      </div>
      <div className="mt-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">Market Cap</span>
        </div>
        <div className="text-2xl font-semibold">$40.3 T</div>
      </div>
    </div>
  </div>
);

const DetailRow = ({ label, value }) => (
  <div className="flex flex-col">
    <span className="text-sm text-gray-600">{label}</span>
    <span className="font-medium">{value}</span>
  </div>
);

export default function StockDashboard() {
  return (
    <div className="flex-1 p-8 bg-gray-50">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-medium">Stock</h1>
          <Edit2 className="w-4 h-4 text-gray-400" />
        </div>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Chercher une commande"
              className="pl-10 pr-4 py-2 border rounded-lg w-64"
            />
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          </div>
          <nav className="flex space-x-4">
            <NavItem label="Commandes" />
            <NavItem label="Planification" />
            <NavItem label="Historique" />
            <NavItem label="Statistiques" active />
          </nav>
          <button className="p-2 relative">
            <Bell className="w-5 h-5 text-gray-600" />
            <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full" />
          </button>
        </div>
      </div>

      <div className="flex gap-3">
        <Card className="flex-1">
          <CardContent className="px-6 mt-8">
            <div className="flex items-center justify-between mb-[-2]">
              <div className="flex items-center gap-1 mt-[6vh]">
                <div className="w-8 h-8 bg-gray-200 rounded flex items-center justify-center">
                  S&P
                </div>
                <div>
                  <h2 className="font-medium">S&P 500</h2>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-semibold">4,566.48</span>
                    <span className="text-green-500">+1.66%</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1 text-sm rounded-full bg-gray-100">1d</button>
                <button className="px-3 py-1 text-sm rounded-full bg-gray-100">5d</button>
                <button className="px-3 py-1 text-sm rounded-full bg-gray-100">1m</button>
                <button className="px-3 py-1 text-sm rounded-full bg-gray-100">6m</button>
                <button className="px-3 py-1 text-sm rounded-full bg-gray-100">1y</button>
                <button className="px-3 py-1 text-sm rounded-full bg-gray-100">5d</button>
                <button className="px-3 py-1 text-sm rounded-full bg-gray-100">Max</button>
              </div>
            </div>
            <BarChart
              width={600} // Réduction de la largeur du graphique
              height={300}
              data={stockData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis domain={[4000, 4700]} />
              <Bar dataKey="value" fill="#4CAF50" />
            </BarChart>
          </CardContent>
        </Card>
        <Details />
      </div>
    </div>
  );
}

const NavItem = ({ label, active }) => (
  <button className={`px-3 py-1 text-sm ${active ? "text-gray-900" : "text-gray-600"}`}>
    {label}
  </button>
);
