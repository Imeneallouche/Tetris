import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import DeleteIcon from "../../assets/delete.svg";
import Filters from "../../assets/filter-lines.svg";
import ConfirmationPopup from "../../components/ConfirmationPopUp";
import Navbar from "../../components/navbar";

export default function OrdersTable() {
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const orders = [
    {
      id: 1,
      number: "12345",
      arrivalDate: "12/09/2028",
      deliveryDate: "20/03/2026",
      client: "Regular text column",
    },
  ];

  const toggleRow = (id) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRows(newSelected);
  };

  const handlePlanifierClick = () => {
    console.log("Opening popup"); // Pour déboguer
    setIsPopupOpen(true);
  };

  const handleClosePopup = () => {
    console.log("Closing popup"); // Pour déboguer
    setIsPopupOpen(false);
  };

  return (
    <>
    <Navbar title={""} />
      <div className="bg-white rounded-lg shadow mt-10 px-6">
        
        <div className="p-4">
        <h2 className="text-4xl font-semibold">Commandes</h2>
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-lg font-semibold mt-4">En attente</h2>
              <p className="text-sm text-gray-500">
                La liste des commandes en attente
              </p>
            </div>
            <div className="flex gap-2">
              <button className="px-3 py-2 text-gray-500 hover:text-gray-700 flex items-center">
                <img src={DeleteIcon} alt="Delete Icon" className="pr-2" />
                Delete
              </button>
              <button className="px-3 py-2 text-gray-500 hover:text-gray-700 flex items-center">
                <img src={Filters} alt="Filter Icon" className="pr-2" /> Filtre
              </button>
              <button 
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                onClick={handlePlanifierClick}
              >
                Planifier & charger
              </button>
            </div>
          </div>

          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-8 p-4">
                  <input type="checkbox" className="rounded" />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  N° commande{" "}
                  <ChevronDown className="w-4 h-4 inline-block ml-1" />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date d'arrivée{" "}
                  <ChevronDown className="w-4 h-4 inline-block ml-1" />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date de livraison{" "}
                  <ChevronDown className="w-4 h-4 inline-block ml-1" />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Client <ChevronDown className="w-4 h-4 inline-block ml-1" />
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="p-4">
                    <input
                      type="checkbox"
                      className="rounded"
                      checked={selectedRows.has(order.id)}
                      onChange={() => toggleRow(order.id)}
                    />
                  </td>
                  <td className="px-6 py-4 font-medium">{order.number}</td>
                  <td className="px-6 py-4 text-gray-500">{order.arrivalDate}</td>
                  <td className="px-6 py-4 text-gray-500">{order.deliveryDate}</td>
                  <td className="px-6 py-4 text-gray-500">{order.client}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Le popup à l'extérieur du conteneur principal */}
      <ConfirmationPopup
        isOpen={isPopupOpen}
        onClose={handleClosePopup}
      />
    </>
  );
}