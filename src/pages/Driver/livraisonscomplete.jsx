import React, { useState } from 'react';
import { Check, Filter, MapPin } from 'lucide-react';

const DeliveryTableComplete = () => {
  const [activeTab, setActiveTab] = useState('en-cours');
  
  const deliveries = [
    {
      id: '12345',
      arrivalDate: '12/09/2028',
      deliveryDate: '20/03/2026',
      client: 'Regular text column'
    },
    {
      id: 'Bold text column',
      arrivalDate: 'Regular text column',
      deliveryDate: '--',
      client: 'Regular text column'
    },
    // Add more mock data to match the image
  ];

  const tabs = [
    { id: 'nouvelles', label: 'Nouvelles' },
    { id: 'en-cours', label: 'En cours' },
    { id: 'completees', label: 'Complétées' },
    { id: 'annulees', label: 'annulées' }
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold">Livraisons</h1>
            <button className="p-1">
              <svg className="w-4 h-4 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 20h9M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Voici la liste des livraisons à compléter
          </p>
        </div>
      </div>

      <div className="flex space-x-1 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${
              activeTab === tab.id
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex gap-4 mb-6">
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg">
            <Filter className="h-4 w-4" />
            Tableau
          </button>
          <button className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg">
            <Filter className="h-4 w-4" />
            Liste
          </button>
        </div>
        <div className="flex-1">
          <input
            type="text"
            placeholder="Chercher une livraison"
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {deliveries.map((delivery) => (
              <tr key={delivery.id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium">
                  {delivery.id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                  {delivery.arrivalDate}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                  {delivery.deliveryDate}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                  {delivery.client}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex gap-4">
                    <button className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                    </button>
                    <button className="text-green-600 hover:text-green-700 font-bold">
                      Terminer
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DeliveryTableComplete;