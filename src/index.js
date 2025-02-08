import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import Chargement from "./pages/Admin/loading3d"
import { BrowserRouter } from "react-router-dom";
import Appdriver from "./pages/Driver/Appdriver";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <BrowserRouter>
    {/*<Appdriver />*/}
    <App />
    </BrowserRouter>

  </React.StrictMode>
);
