import { type User, type InsertUser, type Workflow, type InsertWorkflow } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  getWorkflow(id: string): Promise<Workflow | undefined>;
  getWorkflows(): Promise<Workflow[]>;
  createWorkflow(workflow: InsertWorkflow): Promise<Workflow>;
  updateWorkflow(id: string, workflow: Partial<InsertWorkflow>): Promise<Workflow | undefined>;
  deleteWorkflow(id: string): Promise<boolean>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private workflows: Map<string, Workflow>;

  constructor() {
    this.users = new Map();
    this.workflows = new Map();
    
    // Add a sample workflow
    const sampleWorkflow: Workflow = {
      id: randomUUID(),
      name: "Customer Onboarding Flow",
      description: "Automated customer onboarding process",
      nodes: [
        {
          id: "webhook-1",
          type: "webhook",
          position: { x: 200, y: 150 },
          data: {
            label: "Webhook Trigger",
            description: "Listens for HTTP requests",
            category: "trigger",
            config: {
              method: "POST",
              path: "/webhook/abc123"
            }
          }
        },
        {
          id: "filter-1",
          type: "filter",
          position: { x: 500, y: 150 },
          data: {
            label: "Filter Data",
            description: "Only process valid emails",
            category: "transform",
            config: {
              condition: "email != null",
              action: "Continue if true"
            }
          }
        },
        {
          id: "http-1",
          type: "http-request",
          position: { x: 350, y: 300 },
          data: {
            label: "API Request",
            description: "Create user account",
            category: "action",
            config: {
              url: "api.example.com/users",
              method: "POST"
            }
          }
        },
        {
          id: "email-1",
          type: "email",
          position: { x: 800, y: 150 },
          data: {
            label: "Send Email",
            description: "Welcome message",
            category: "action",
            config: {
              to: "{{user.email}}",
              template: "welcome_email"
            }
          }
        },
        {
          id: "database-1",
          type: "database",
          position: { x: 650, y: 300 },
          data: {
            label: "Save to Database",
            description: "Store user data",
            category: "action",
            config: {
              table: "users",
              operation: "INSERT"
            }
          }
        }
      ],
      edges: [
        {
          id: "webhook-filter",
          source: "webhook-1",
          target: "filter-1"
        },
        {
          id: "filter-http",
          source: "filter-1",
          target: "http-1"
        },
        {
          id: "filter-email",
          source: "filter-1",
          target: "email-1"
        },
        {
          id: "http-database",
          source: "http-1",
          target: "database-1"
        }
      ],
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    this.workflows.set(sampleWorkflow.id, sampleWorkflow);
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  async getWorkflow(id: string): Promise<Workflow | undefined> {
    return this.workflows.get(id);
  }

  async getWorkflows(): Promise<Workflow[]> {
    return Array.from(this.workflows.values());
  }

  async createWorkflow(insertWorkflow: InsertWorkflow): Promise<Workflow> {
    const id = randomUUID();
    const workflow: Workflow = {
      ...insertWorkflow,
      id,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.workflows.set(id, workflow);
    return workflow;
  }

  async updateWorkflow(id: string, updateData: Partial<InsertWorkflow>): Promise<Workflow | undefined> {
    const workflow = this.workflows.get(id);
    if (!workflow) return undefined;

    const updatedWorkflow: Workflow = {
      ...workflow,
      ...updateData,
      updatedAt: new Date()
    };
    this.workflows.set(id, updatedWorkflow);
    return updatedWorkflow;
  }

  async deleteWorkflow(id: string): Promise<boolean> {
    return this.workflows.delete(id);
  }
}

export const storage = new MemStorage();
