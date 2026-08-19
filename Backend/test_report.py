from app.agents.report_agent import generate_ieee_report


context = """
Artificial Intelligence in Healthcare

This research paper investigates the use of deep learning
for medical image classification.

The authors propose a convolutional neural network (CNN)
based approach for detecting diseases from chest X-ray images.

The model is evaluated using a medical image dataset.
The paper reports improved classification performance
compared with traditional machine learning approaches.

The authors conclude that deep learning can support
medical diagnosis, while further validation is required
before real-world clinical deployment.

No specific dataset name, dataset size, hardware,
software configuration, or numerical performance values
are provided in this context.
"""


result = generate_ieee_report(context)


print("=" * 70)
print("IEEE REPORT AGENT OUTPUT")
print("=" * 70)

print(result)