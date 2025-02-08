import React, { useState } from 'react';
import { Search, ArrowLeft, Settings, RotateCw, ChevronDown, Eye, ChevronRight } from 'lucide-react';
import CargoVisualization from '../../components/CargoVisualization';  // Import du composant 3D

const LoadingSimulator = () => {
  const [expandedItem, setExpandedItem] = useState(null);

  const items = [
    {
      id: 1,
      name: 'Item 1',
      weight: '150 kg',
      dimensions: '120 x 80 x 90 cm',
      quantity: '1/2',
      volume: '0.864 m³',
      status: 'ready'
    },
    {
      id: 2,
      name: 'Item 2',
      weight: '200 kg',
      dimensions: '150 x 100 x 120 cm',
      quantity: '2/2',
      volume: '1.8 m³',
      status: 'ready'
    },
    {
      id: 3,
      name: 'Item 3',
      weight: '175 kg',
      dimensions: '100 x 80 x 100 cm',
      quantity: '3/4',
      volume: '0.8 m³',
      status: 'pending'
    }
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="h-14 bg-white border-b flex items-center px-4 justify-between">
        <div className="flex items-center gap-4">
          <span className="font-medium">Dashboard</span>
          <div className="flex items-center bg-gray-50 rounded-md px-3 py-1.5">
            <Search className="w-4 h-4 text-gray-400" />
            <input 
              className="bg-transparent border-none outline-none px-2 text-sm"
              placeholder="Chercher une commande"
            />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-600">Commandes</span>
          <span className="text-gray-600">Planification</span>
          <span className="text-gray-600">Historique</span>
          <span className="text-gray-600">Workspaces</span>
          <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 bg-white border-r overflow-y-auto h-full">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <span className="font-medium">Items</span>
              <div className="flex gap-2">
                <button className="p-1 hover:bg-gray-100 rounded">
                  <Settings className="w-4 h-4" />
                </button>
                <button className="p-1 hover:bg-gray-100 rounded">
                  <RotateCw className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-4">
              <div className="font-medium text-sm text-gray-600">Group 1</div>
              {items.map((item) => (
                <div key={item.id} className="border rounded-lg overflow-hidden">
                  <div 
                    className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100"
                    onClick={() => setExpandedItem(expandedItem === item.id ? null : item.id)}
                  >
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${item.status === 'ready' ? 'bg-green-400' : 'bg-yellow-400'}`}></div>
                      <span className="font-medium">{item.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-500">{item.quantity}</span>
                      {expandedItem === item.id ? 
                        <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      }
                    </div>
                  </div>

                  {expandedItem === item.id && (
                    <div className="p-3 border-t bg-white">
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Dimensions:</span>
                          <span className="text-gray-700">{item.dimensions}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Weight:</span>
                          <span className="text-gray-700">{item.weight}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Volume:</span>
                          <span className="text-gray-700">{item.volume}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Status:</span>
                          <span className={`${item.status === 'ready' ? 'text-green-600' : 'text-yellow-600'}`}>
                            {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          <div className="h-12 border-b flex items-center px-4">
            <button className="flex items-center gap-2 text-gray-600">
              <ArrowLeft className="w-4 h-4" />
              <span>Visualisation 3D du chargement</span>
            </button>
          </div>

          <div className="flex-1 relative">
            <div className="absolute inset-0 bg-gray-50">
              <CargoVisualization items={items} /> {/* Visualisation 3D */}
            </div>
            <button className="absolute top-4 right-4 p-2 bg-white rounded-lg shadow">
              <Eye className="w-4 h-4" />
            </button>
          </div>

          <div className="h-32 border-t bg-white p-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="text-sm text-gray-600 mb-2">Loading Items: 3/5</div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="w-3/5 h-full bg-blue-500"></div>
                </div>
              </div>
              <button className="px-6 py-2 bg-blue-500 text-white rounded-lg">
                Load
              </button>
            </div>
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-sm text-gray-600">
                Remaining time: 15 min
              </div>
              <div className="text-sm text-gray-600">
                Remaining volume: 4.6m³
              </div>
              <div className="text-sm text-gray-600">
                Remaining weight: 2450kg
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingSimulator;
