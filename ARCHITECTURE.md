# MythoStack Architecture & Setup Guide

This document provides a comprehensive overview of the **MythoStack** system, its intelligence layer, and how it supports compounding growth for businesses.

## 🧠 System Intelligence

MythoStack is a multi-agent orchestration system designed for commercial growth, embodying the principle: "Every campaign builds on the last."

### **1. Multi-Agent Orchestration**
The system uses a two-agent flow to process user requests, forming a "Compounding Loop":
- **Growth Architect**: Diagnoses the user's needs, interviews them to gather business context, and architects a high-leverage marketing strategy.
- **Asset Engine**: Takes the architected strategy and uses RAG (Retrieval-Augmented Generation) to write high-quality marketing assets in the user's voice.

### **2. Retrieval-Augmented Generation (RAG)**
The backend integrates a framework retriever that pulls in proven marketing frameworks to guide the AI's output, ensuring that the generated assets are not just creative but also strategically sound.

### **3. Voice Profiling**
The system can analyze user-provided samples to create a "Voice Profile," allowing the Asset Engine to mimic the user's unique tone and style across all generated content.

## 🛠 Technical Architecture

### **Backend (FastAPI)**
- **Framework**: FastAPI with asynchronous streaming support (SSE).
- **Orchestration**: Built on `langgraph` for stateful multi-agent flows.
- **Security**: Fail-closed JWT authentication compatible with Supabase.
- **Persistence**: SQLAlchemy with Alembic migrations (supports Postgres/SQLite).

### **Frontend (Next.js)**
- **Framework**: Next.js 15 with Tailwind CSS.
- **Auth**: Integrated with Supabase Auth for multi-tenant isolation.
- **State Management**: React hooks with local storage persistence for developer settings.

## ⚙️ Environment Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MYTHOSTACK_AUTH_DISABLED` | Bypasses JWT verification for local development. | `false` |
| `MYTHOSTACK_ANTHROPIC_API_KEY` | Required for real AI intelligence. | `None` (uses Fake LLM) |
| `MYTHOSTACK_DATABASE_URL` | SQLAlchemy connection string. | `None` (uses In-Memory) |
| `MYTHOSTACK_CORS_ORIGINS` | Allowed origins for API access. | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Frontend setting for the backend endpoint. | `http://127.0.0.1:8000` |

## 🚀 Operational Benefits

1.  **Consistency**: Ensures all marketing assets follow an architected strategy.
2.  **Scalability**: Allows a single user to manage multiple marketing angles and assets effortlessly.
3.  **Security**: Strict tenant isolation ensures that one user's data and sessions are never accessible to another.
