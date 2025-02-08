// components/DeliveryTable.jsx
import React from 'react';
import { Check, Filter } from 'lucide-react';

const DeliveryTable = () => {
  const deliveries = [
    {
      id: '12345',
      arrivalDate: '12/09/2028',
      deliveryDate: '20/03/2026',
      client: 'Regular text column',
      status: 'completed'
    },
    // Add more mock data as needed
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Livraisons</h1>
          <p className="text-sm text-gray-500 mt-1">
            Voici vos nouvelles livraisons à faire
          </p>
        </div>
        <div className="flex gap-4">
          <button className="flex items-center gap-2 px-4 py-2 border rounded-lg">
            <Filter className="h-4 w-4" />
            Filters
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-lg">
            Confirmer
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr>
              <th className="w-12 px-6 py-3 text-left">
                <input type="checkbox" className="rounded border-gray-300" />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                N° commande
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date d'arrivée
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date de livraison
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Client
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {deliveries.map((delivery) => (
              <tr key={delivery.id}>
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <input type="checkbox" className="rounded border-gray-300" />
                  </div>
                </td>
                <td className="px-6 py-4 font-medium">{delivery.id}</td>
                <td className="px-6 py-4 text-gray-500">{delivery.arrivalDate}</td>
                <td className="px-6 py-4 text-gray-500">{delivery.deliveryDate}</td>
                <td className="px-6 py-4 text-gray-500">{delivery.client}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DeliveryTable;