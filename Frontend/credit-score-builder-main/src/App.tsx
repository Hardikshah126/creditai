import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";

import Landing from "./pages/Landing";
import Signup from "./pages/Signup";
import AppShell from "./components/AppShell";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Assistant from "./pages/Assistant";
import Report from "./pages/Report";
import History from "./pages/History";
import SettingsPage from "./pages/Settings";
import LenderShell from "./components/LenderShell";
import Lender from "./pages/Lender";
import LenderReport from "./pages/LenderReport";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/dashboard" element={<AppShell />}>
            <Route index element={<Dashboard />} />
            <Route path="upload" element={<Upload />} />
            <Route path="assistant" element={<Assistant />} />
            <Route path="report" element={<Report />} />
            <Route path="history" element={<History />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="/lender" element={<LenderShell />}>
            <Route index element={<Lender />} />
            <Route path="report/:id" element={<LenderReport />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
