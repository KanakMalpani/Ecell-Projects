"""
10-K SEC filing risk classification pipeline.

This package contains the core machine-learning code for Task 1:
  - preprocess.py  → download and clean filing text
  - features.py    → convert text into numeric features (TF-IDF)
  - train.py       → train XGBoost, AdaBoost, and CatBoost
  - evaluate.py    → compare models and save the best one
  - utils.py       → shared paths, constants, and logging
"""
