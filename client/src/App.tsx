import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MainLayout } from "@/components/layout/main-layout";
import NotFound from "@/pages/not-found";
import DashboardPage from "@/pages/dashboard";
import FlowsPage from "@/pages/flows";
import FlowDashboardPage from "@/pages/flow-dashboard";
import CreateFlowPage from "@/pages/create-flow";
import WorkflowEditPage from "@/pages/workflow-edit";
import ConnectionsPage from "@/pages/connections";
import SettingsPage from "@/pages/settings";

function Router() {
  return (
    <MainLayout>
      <Switch>
        <Route path="/" component={DashboardPage} />
        <Route path="/flows" component={FlowsPage} />
        <Route path="/flows/create" component={CreateFlowPage} />
        <Route path="/flows/:id/dashboard" component={FlowDashboardPage} />
        <Route path="/flows/:id/edit" component={WorkflowEditPage} />
        <Route path="/connections" component={ConnectionsPage} />
        <Route path="/settings" component={SettingsPage} />
        <Route component={NotFound} />
      </Switch>
    </MainLayout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
