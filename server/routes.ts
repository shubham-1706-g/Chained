import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertWorkflowSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // Workflow routes
  app.get("/api/workflows", async (req, res) => {
    try {
      const workflows = await storage.getWorkflows();
      res.json(workflows);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch workflows" });
    }
  });

  app.get("/api/workflows/:id", async (req, res) => {
    try {
      const workflow = await storage.getWorkflow(req.params.id);
      if (!workflow) {
        return res.status(404).json({ message: "Workflow not found" });
      }
      res.json(workflow);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch workflow" });
    }
  });

  app.post("/api/workflows", async (req, res) => {
    try {
      const validatedData = insertWorkflowSchema.parse(req.body);
      const workflow = await storage.createWorkflow(validatedData);
      res.status(201).json(workflow);
    } catch (error) {
      res.status(400).json({ message: "Invalid workflow data" });
    }
  });

  app.put("/api/workflows/:id", async (req, res) => {
    try {
      const validatedData = insertWorkflowSchema.partial().parse(req.body);
      const workflow = await storage.updateWorkflow(req.params.id, validatedData);
      if (!workflow) {
        return res.status(404).json({ message: "Workflow not found" });
      }
      res.json(workflow);
    } catch (error) {
      res.status(400).json({ message: "Invalid workflow data" });
    }
  });

  app.delete("/api/workflows/:id", async (req, res) => {
    try {
      const success = await storage.deleteWorkflow(req.params.id);
      if (!success) {
        return res.status(404).json({ message: "Workflow not found" });
      }
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ message: "Failed to delete workflow" });
    }
  });

  // Workflow execution routes
  app.post("/api/workflows/:id/execute", async (req, res) => {
    try {
      const workflow = await storage.getWorkflow(req.params.id);
      if (!workflow) {
        return res.status(404).json({ message: "Workflow not found" });
      }
      
      // Mock execution - in a real implementation, this would trigger the workflow engine
      res.json({ 
        message: "Workflow execution started",
        executionId: `exec_${Date.now()}`,
        status: "running"
      });
    } catch (error) {
      res.status(500).json({ message: "Failed to execute workflow" });
    }
  });

  app.post("/api/workflows/:id/pause", async (req, res) => {
    try {
      res.json({ message: "Workflow paused", status: "paused" });
    } catch (error) {
      res.status(500).json({ message: "Failed to pause workflow" });
    }
  });

  app.post("/api/workflows/:id/stop", async (req, res) => {
    try {
      res.json({ message: "Workflow stopped", status: "stopped" });
    } catch (error) {
      res.status(500).json({ message: "Failed to stop workflow" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
