from app.agents.dataset_agent import recommend_datasets


# Test 1: Uploaded Research Paper Context
context = """
Artificial Intelligence in Healthcare: Deep Learning for Pneumonia Detection

This research paper investigates the use of deep convolutional neural networks (CNNs)
and vision transformers for medical image classification and pathology detection from frontal chest X-ray images.
The authors propose a dual-attention DenseNet-121 backbone trained with focal loss to detect
pneumonia, atelectasis, cardiomegaly, and pleural effusion.

The model is evaluated using chest radiograph baselines, reporting an AUROC of 0.912 and F1-score of 0.864.
The paper reports improved classification performance compared with standard ResNet-50 baselines.
The authors conclude that further multi-center external validation on diverse demographic cohorts is required.
"""

print("=" * 70)
print("TEST 1: DATASET AGENT FOR UPLOADED PAPER CONTEXT")
print("=" * 70)
result_paper = recommend_datasets(context=context)
print(result_paper)

print("\n" + "=" * 70)
print("TEST 2: DATASET AGENT FOR DIRECT USER QUERY")
print("=" * 70)
query = "Multi-hop Question Answering and Retrieval Augmented Generation (RAG)"
result_query = recommend_datasets(query=query)
print(result_query)