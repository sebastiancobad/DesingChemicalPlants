import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import HeatExchangerPage from "./pages/HeatExchangerPage";
import PipingPage from "./pages/PipingPage";
import PumpPage from "./pages/PumpPage";
import SeparatorPage from "./pages/SeparatorPage";
import MaterialsPage from "./pages/MaterialsPage";
import LayoutPage from "./pages/LayoutPage";
import EconomicsPage from "./pages/EconomicsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/modules/heat-exchanger" element={<HeatExchangerPage />} />
        <Route path="/modules/piping" element={<PipingPage />} />
        <Route path="/modules/pump" element={<PumpPage />} />
        <Route path="/modules/separator" element={<SeparatorPage />} />
        <Route path="/modules/materials" element={<MaterialsPage />} />
        <Route path="/modules/layout" element={<LayoutPage />} />
        <Route path="/modules/economics" element={<EconomicsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
