from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"

client = MongoClient(MONGO_URL)

db = client["researchx"]

# Users
users_collection = db["users"]

# Papers selected by user
papers_collection = db["papers"]

# Research Sessions
research_sessions_collection = db["research_sessions"]

# Agent Outputs (NEW)
agent_outputs_collection = db["agent_outputs"]

# Analytics
agent_runs_collection = db["agent_runs"]

# Search History
search_history_collection = db["search_history"]