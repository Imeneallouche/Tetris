import React from "react";
import { LayoutGrid, List } from "lucide-react";

export default function TableHeader() {
  return (
    <div className="flex flex-col mb-4">
      <div className="flex justify-between items-center w-full">
        <h1 className="flex justify-center items-center  font-semibold text-4xl">
          Commandes
        </h1>
        <div className="flex justify-center items-center gap-4 ">
          <button className="text-blue-600 ">Tout</button>
          <button className="text-gray-500 hover:text-gray-700">
            en attente
          </button>
          <button className="text-gray-500 hover:text-gray-700">
            en cours
          </button>
          <button className="text-gray-500 hover:text-gray-700">
            complétées
          </button>
          <button className="text-gray-500 hover:text-gray-700">
            annulées
          </button>
        </div>
      </div>
      <div className="flex justify-start self-start mt-4 mb-3">
        <div className="flex justify-start items-center gap-2 border-[1px] border-[#C7CED9] rounded-lg bg-white">
          <div className="flex items-center gap-2 px-4 py-2">
            <LayoutGrid className="w-5 h-5" />
            <p>Tableau</p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2">
            <List className="w-5 h-5 text-blue-600" />
            <p>Liste</p>
          </div>
        </div>
      </div>
    </div>
  );
}
