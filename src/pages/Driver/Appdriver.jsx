import React from 'react'
import SidebarDriver from '../../components/SidebarDriver'
import NavbarDriver from '../../components/Navbardriver'
import DeliveryTable from './NewlivraisonDriver'
import DeliveryTableComplete from './livraisonscomplete'

const Appdriver = () => {
  return (
    <div className="flex h-screen bg-gray-50">
    <SidebarDriver />
    <div className="flex-1 flex flex-col">
      <NavbarDriver />
      <main className="flex-1 p-6">
        <DeliveryTableComplete />
      </main>
    </div>
  </div>
  )
}

export default Appdriver