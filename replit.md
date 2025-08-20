# Workflow Automation Platform

## Overview

This is a workflow automation platform that allows users to create, edit, and execute visual workflows through a drag-and-drop interface. Built with React and Express, it provides a comprehensive solution for building automated workflows with support for triggers, actions, and data transformations. The platform features a visual flow editor similar to tools like Zapier or Microsoft Power Automate, enabling users to connect different services and automate business processes.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **React SPA**: Built with Vite for fast development and optimized builds
- **UI Framework**: Utilizes shadcn/ui components with Radix UI primitives for a polished interface
- **Styling**: Tailwind CSS with custom design tokens and CSS variables for theming
- **State Management**: TanStack Query for server state management and React hooks for local state
- **Routing**: Wouter for lightweight client-side routing
- **Visual Editor**: ReactFlow library powers the drag-and-drop workflow canvas with custom node types

### Backend Architecture
- **Express.js Server**: RESTful API with middleware for request logging and error handling
- **TypeScript**: Full type safety across client, server, and shared schemas
- **Storage Layer**: Abstracted storage interface with in-memory implementation (MemStorage) for development
- **API Design**: RESTful endpoints for workflow CRUD operations with proper HTTP status codes
- **Development Setup**: Vite integration for hot reloading in development mode

### Data Storage Solutions
- **Database**: PostgreSQL configured with Drizzle ORM for type-safe database operations
- **Schema Management**: Drizzle Kit for migrations and schema synchronization
- **Connection**: Neon Database serverless PostgreSQL for cloud deployment
- **Development Storage**: In-memory storage implementation for rapid prototyping

### Component Architecture
- **Workflow Canvas**: ReactFlow-based visual editor with custom node types and connection handling
- **Node Library**: Categorized drag-and-drop node components (triggers, actions, transforms)
- **Property Panel**: Dynamic configuration interface for workflow nodes
- **Sidebar Interface**: Workflow controls, execution status, and node library browser

### External Dependencies
- **Database**: Neon Database (PostgreSQL) for persistent data storage
- **UI Components**: Radix UI primitives for accessible, unstyled components
- **Icons**: Lucide React for modern, consistent iconography
- **Development**: Replit-specific plugins for enhanced development experience
- **Fonts**: Google Fonts (Inter, DM Sans, Fira Code, Geist Mono, Architects Daughter)
- **Session Management**: PostgreSQL session store with connect-pg-simple