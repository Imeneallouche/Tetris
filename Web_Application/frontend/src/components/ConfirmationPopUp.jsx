import React from "react";
import { X, Clock, CalendarDays, Users } from "lucide-react";

const ConfirmationPopup = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-xl mx-4 relative">
        {/* Close button */}
        <button 
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-500 hover:text-gray-700"
        >
          <X className="w-6 h-6" />
        </button>

        {/* Success icon */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center">
            <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
        </div>

        {/* Title */}
        <h2 className="text-3xl text-center font-medium text-gray-900 mb-6">
        Planification effectuée avec succès
        </h2>

        <div className="text-center mb-8">
          <h3 className="text-xl font-medium mb-2">Vous pouvez consulter et ajuster la planification de votre commande.</h3>
        </div>

        {/* Details grid */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="flex flex-col items-center p-4 rounded-lg border border-gray-200">
            <CalendarDays className="w-6 h-6 text-gray-600 mb-2" />
            <span className="text-gray-900">09 Fév 2025</span>
          </div>
          <div className="flex flex-col items-center p-4 rounded-lg border border-gray-200">
            <Clock className="w-6 h-6 text-gray-600 mb-2" />
            <span className="text-gray-900">9:00 PM - 10:00PM</span>
          </div>
          <div className="flex flex-col items-center p-4 rounded-lg border border-gray-200">
            <Users className="w-6 h-6 text-gray-600 mb-2" />
            <span className="text-gray-900">3 camions</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button className="flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            Itinéraire
          </button>
          <button className="flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Visualiser
          </button>
        </div>

        {/* Cancel button */}
        <button 
          onClick={onClose}
          className="w-full mt-4 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center justify-center"
        >
          <X className="w-5 h-5 mr-2" />
          Annuler la planification
        </button>
      </div>
    </div>
  );
};

export default ConfirmationPopup;