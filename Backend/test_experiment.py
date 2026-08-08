from app.agents.experiment_agent import recommend_experiments


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


result = recommend_experiments(context)


print("=" * 70)
print("EXPERIMENT AGENT OUTPUT")
print("=" * 70)

print(result)