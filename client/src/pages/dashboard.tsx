import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Workflow, CheckCircle, AlertCircle, Clock, TrendingUp, Play, Plus } from "lucide-react";
import { Link } from "wouter";
import { Workflow as WorkflowType } from "@shared/schema";

export default function DashboardPage() {
  const { data: workflows, isLoading } = useQuery<WorkflowType[]>({
    queryKey: ['/api/workflows'],
  });

  const activeFlows = workflows?.filter(w => w.isActive) || [];
  const totalRuns = 42; // Mock data - would come from API
  const successRate = 95.2; // Mock data
  const avgExecutionTime = 2.3; // Mock data

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  return null;
}