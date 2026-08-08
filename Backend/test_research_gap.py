from app.agents.research_gap import find_research_gaps

context = """
Artificial Intelligence in Healthcare

This research paper investigates the use of deep learning
for medical image classification. The authors propose a
convolutional neural network based approach for detecting
diseases from chest X-ray images.

The model is evaluated using a medical image dataset.
The paper reports improved classification performance
compared with traditional machine learning approaches.

The authors conclude that deep learning can support
medical diagnosis, while further validation is required
before real-world clinical deployment.
"""

result = find_research_gaps(context)

print("=" * 70)
print("RESEARCH GAP AGENT OUTPUT")
print("=" * 70)

print(result)