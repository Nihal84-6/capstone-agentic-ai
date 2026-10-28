[project_readme.md](https://github.com/user-attachments/files/34060535/project_readme.md)
# 🎲 The Critical Hit Board Game Café — AI Operations Hub

An autonomous, multi-tool AI concierge and live café management dashboard built with **Python, Streamlit, and the Groq API**. 

This capstone project demonstrates how local businesses can automate customer support and operational state tracking (POS and Table Bookings) using Agentic AI, strict scope guardrails, and real-time database synchronization.

## ✨ Core Features

* 🧠 **RAG Knowledge Base:** Grounded entirely in local business data (`cafe_data.txt`). The AI accurately answers questions about operating hours, dietary restrictions (vegan/nut-free), and the board game library without hallucinating.
* 🛠️ **Autonomous Tool Execution:** The LLM autonomously triggers Python functions to:
  * Check live table and game availability (`bookings.json`).
  * Book, modify, or cancel single and multi-table group reservations.
  * Calculate itemized food orders with a 5% tax and save them to a POS database (`orders.json`).
* 🛜 **Dual-Engine Fallback (Demo-Day Safe):** Built-in network resilience. If the API key is missing or the venue Wi-Fi drops, the app instantly falls back to a local, regex-based offline routing engine so the UI and core booking flows never crash.
* 🎨 **Editorial UI/UX:** A bespoke, custom-CSS Streamlit dashboard featuring live KPI metrics, a visual 2x5 table floor plan, and reactive board game inventory cards.

## 🚀 Quickstart Guide

### 1. Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install streamlit pandas groq
```

### 2. Set Your API Key
The app uses Groq for blazing-fast tool calling. You can either paste your key directly into the **Admin tab** in the web UI, or set it in your terminal before launching:

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_api_key_here"
```
**Mac/Linux:**
```bash
export GROQ_API_KEY="your_api_key_here"
```

### 3. Launch the Hub
Run the Streamlit application:
```bash
python -m streamlit run cafe_agent.py
```

## 🧪 Live Demo Scenarios
Once the dashboard is running, use the **Admin Tab** to trigger one-click tests, or type these directly into the chat:
1. **RAG / Knowledge:** *"What vegan options do you have, and how much is the cover charge?"*
2. **Tool Execution:** *"Can I book a table for 4 people to play Catan at 7:00 PM under Alex?"*
3. **Edge Case Handling:** *"Can I book a table for 8 people to play Monopoly?"* (The agent will enforce the 6-person table limit and inform you Monopoly is not in stock).
4. **Large Group Planning:** *"I want to make a reservation for 20 people for 3 hours tonight at 6:00 PM."*
5. **Scope Guardrails:** *"Write me a Python script"* or *"What's the capital of France?"* (The agent politely redirects back to café operations).

## 🗄️ Architecture & State Management
* `cafe_agent.py`: Main application (Streamlit UI, Groq LLM logic, and fallback engine).
* `cafe_data.txt`: Read-only RAG context containing business rules and menus.
* `bookings.json`: Live read/write database for table and game reservations.
* `orders.json`: Live read/write database for POS food and drink orders.
