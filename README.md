# ResearchX

An AI-powered Multi-Agent Research Assistant built using React, FastAPI, Gemini, ChromaDB, and MongoDB.

> Work in progress.

## Documentation
- Minor documentation review.

## Documentation

- Improved project documentation structure for better readability.
- Reviewed the project architecture and workflow documentation.
- Minor formatting and documentation refinements.

## 🚀 Upcoming ResearchX v2 Enhancements

Based on project review feedback, the next phase of ResearchX will focus on improving research quality, explainability, and real-world usability.

### Planned Enhancements

- Integrate LangGraph for stateful multi-agent orchestration.
- Improve research paper retrieval using multiple academic sources (Semantic Scholar, OpenAlex, Crossref, arXiv).
- Develop a custom Paper Ranking Agent based on semantic similarity, citation count, publication year, venue quality, and relevance score.
- Add a Verification Agent to validate generated responses against retrieved research papers.
- Implement a Citation Agent for evidence-backed responses with proper source attribution.
- Introduce a Plagiarism Reduction Agent for producing more original academic content.
- Add Research Quality Evaluation including novelty, methodology assessment, dataset quality, and future work suggestions.
- Improve the RAG pipeline for higher retrieval accuracy and lower hallucination.
- Transform ResearchX into a production-ready AI-powered research assistant for literature review and academic writing.

### 📌 Development Note (July 2026)

ResearchX is entering its next development phase with a focus on improving research quality and real-world usability. Upcoming work includes enhancing the multi-agent workflow, strengthening research paper retrieval, improving RAG accuracy, and making AI-generated responses more reliable through verification and citation-aware generation.


## Latest Update (Paper Retrieval Enhancement)

ResearchX now supports multi-source research paper retrieval.

### Added
- Integrated Semantic Scholar API
- Integrated OpenAlex API
- Retained arXiv integration
- Created a centralized Retrieval Service to aggregate papers from multiple sources

### Current Retrieval Pipeline

Topic
↓
Semantic Scholar
+
OpenAlex
+
arXiv
↓
Combined Results

### Upcoming Improvements
- Duplicate paper removal
- Intelligent paper ranking
- Citation-based scoring
- Semantic relevance scoring
- Best paper recommendation