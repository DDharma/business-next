# Blueprint: Agentic AI for Banking CRM

## 🎯 What to Build
An **AI-powered Banking Assistant Dashboard** tailored for Relationship Managers to seamlessly find high-value targets and generate bespoke outreach material.

1. **Chat Workspace:** A simple conversational input where managers type natural language requests.
2. **Reasoning Steps (The "Why"):** A live terminal style or step-by-step display showcasing the AI's internal logic and data collection markers before showing results.
3. **Structured Cards:** Clean visual UI cards displaying recommended client profiles, an analytical conversion score, and ready-to-copy text templates.

---

## 💻 Tech Stack

* **Frontend:** Next.js
* **Backend:** Python FastAPI
* **Orchestration:** LangChain
* **Database:** Supabase PostgreSQL

---

## 🔄 Core Workflow

1. **Trigger:** Relationship Manager asks for high-potential loan clients.
2. **Analysis Loop (LangChain):**
   * Connects to **PostgreSQL** to extract high-income demographics and historical cash flow trends.
   * Feeds the raw metrics into a custom logic/heuristic function to calculate conversion probability.
   * Compiles individual background attributes to compose a contextual pitch.
3. **Delivery:** Streams the final formatted payload back to the **Next.js** layer in real-time.
