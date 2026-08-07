from difflib import SequenceMatcher


def remove_duplicate_papers(papers, similarity_threshold=0.90):
    """
    Remove duplicate research papers using title similarity.
    """

    unique_papers = []

    for paper in papers:

        title = paper.get("title", "").strip().lower()

        duplicate = False

        for existing in unique_papers:

            existing_title = existing.get("title", "").strip().lower()

            similarity = SequenceMatcher(
                None,
                title,
                existing_title
            ).ratio()

            if similarity >= similarity_threshold:
                duplicate = True
                break

        if not duplicate:
            unique_papers.append(paper)

    return unique_papers