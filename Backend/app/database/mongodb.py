from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"

client = MongoClient(MONGO_URL)

db = client["researchx"]

# Users Collection
users_collection = db["users"]

# Papers Collection
papers_collection = db["papers"]

agent_runs_collection = db["agent_runs"]

search_history_collection = db["search_history"]

research_sessions_collection = db["research_sessions"]