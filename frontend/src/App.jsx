import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import InvestigatePage from "./pages/InvestigatePage.jsx";
import InvestigationsList from "./pages/InvestigationsList.jsx";
import InvestigationDetail from "./pages/InvestigationDetail.jsx";
import AlertHistory from "./pages/AlertHistory.jsx";
import Chat from "./pages/Chat.jsx";

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/investigate" element={<InvestigatePage />} />
          <Route path="/history" element={<InvestigationsList />} />
          <Route path="/history/:id" element={<InvestigationDetail />} />
          <Route path="/alerts" element={<AlertHistory />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </div>
  );
}
