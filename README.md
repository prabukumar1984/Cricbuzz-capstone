# Cricbuzz
🏏 Cricket Analytics Dashboard 
📌 Overview
This project is a full-stack cricket analytics platform that integrates live match data from the Cricbuzz API with a SQL-backed database and delivers an interactive web experience. Designed for both fans and analysts, it offers real-time insights, player statistics, and full data management capabilities.

🧱 Architecture & Tech Stack
- Frontend: Streamlit for rapid UI development with tabbed navigation and DataFrame outputs
- Backend:
- Python for API integration, data transformation, and CRUD logic
- SQL (MySQL) for structured data storage and analytics
- Data Source: Cricbuzz API (live match feeds, player stats)
- Deployment: Localhost  (Streamlit )

⚙️ Key Features
- ⚡ Real-Time Match Updates
- Live scores, commentary, and match status fetched via Cricbuzz API
- Auto-refresh logic for dynamic updates

- 📊 Detailed Player Statistics
- Batting, bowling, and fielding metrics
- Career aggregates and match-wise breakdowns
- Visualized using Streamlit DataFrames and charts

- 🔍 SQL-Driven Analytics
- Custom queries for performance trends, comparisons, and filters
- Aggregations like average, strike rate, economy, etc.
- Joins across match, player, and team tables

- 🛠️ Full CRUD Operations
- Tab-based UI for Create, Read, Update, Delete
- Safe practice via temporary tables (e.g., temp_cricket_stats)
- Form-based input with validation and feedback

🧠 Learning Highlights
- API integration and error handling for live data
- SQL joins, aggregations, and query optimization
- Streamlit UI enhancements: icons, tooltips, tabbed layout
- Data modeling for sports analytics
- Building learner-friendly interfaces for CRUD and stats exploration
- 
