import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/contexts/sidebar-context";
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
    <SidebarProvider>
      <Switch>
        {/* Route with sidebar for create flow */}
        <Route path="/flows/create" component={() => (
          <MainLayout>
            <CreateFlowPage />
          </MainLayout>
        )} />
        
        {/* Routes with sidebar */}
        <Route path="/" component={() => (
          <MainLayout>
            <DashboardPage />
          </MainLayout>
        )} />
        <Route path="/flows" component={() => (
          <MainLayout>
            <FlowsPage />
          </MainLayout>
        )} />
        <Route path="/flows/:id/dashboard" component={() => (
          <MainLayout>
            <FlowDashboardPage />
          </MainLayout>
        )} />
        {/* Workflow editor also without sidebar for focused editing */}
        <Route path="/flows/:id/edit" component={WorkflowEditPage} />
        <Route path="/connections" component={() => (
          <MainLayout>
            <ConnectionsPage />
          </MainLayout>
        )} />
        <Route path="/settings" component={() => (
          <MainLayout>
            <SettingsPage />
          </MainLayout>
        )} />
        <Route component={NotFound} />
      </Switch>
    </SidebarProvider>
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
