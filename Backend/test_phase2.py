from app.agents.coordinator import run_agent


# ==========================================================
# Phase 2 Integration Test
# ==========================================================

context = """
Artificial Intelligence in Healthcare

This research paper investigates the use of deep learning
for medical image classification.

The authors propose a convolutional neural network (CNN)
based approach for detecting diseases from chest X-ray images.

The model is evaluated using a medical image dataset.
The paper reports improved classification performance
compared with traditional machine learning approaches.

The paper states that deep learning can support medical
diagnosis.

Further validation is required before real-world clinical
deployment.

The provided context does not specify the exact dataset
name, dataset size, hardware, software configuration,
evaluation metrics, or numerical performance values.
"""


query = "Perform a complete analysis of this research paper."


print("=" * 70)
print("RESEARCHX PHASE 2 INTEGRATION TEST")
print("=" * 70)

try:

    result = run_agent(
        query=query,
        context=context,
    )

    print("\n" + "=" * 70)
    print("PHASE 2 RESULT")
    print("=" * 70)

    if result is None:
        print("❌ TEST FAILED")
        print("Coordinator returned None.")

    else:
        print("✅ Coordinator executed successfully.")

        print("\nResult:")
        print(result)

except Exception as error:

    print("\n" + "=" * 70)
    print("❌ PHASE 2 TEST FAILED")
    print("=" * 70)

    print(type(error).__name__)
    print(error)