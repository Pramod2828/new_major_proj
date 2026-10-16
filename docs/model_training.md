# Smart-Log: Model Training & Evaluation Guide

This document describes the dual supervised machine learning algorithms, training protocols, evaluation metrics, and model activation standards in **Smart-Log**.

---

## 1. Supported Supervised Classifiers

Smart-Log strictly employs two supervised machine learning algorithms:

### 1.1 Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)
- **Ensemble Strategy**: Bagging of decision trees with bootstrap aggregation.
- **Configurable Hyperparameters**:
  - `n_estimators`: Number of trees in the forest (Default: `100`).
  - `max_depth`: Maximum tree depth to constrain overfitting (Default: `15`).
  - `min_samples_split`: Minimum samples required to split an internal node (Default: `2`).
  - `class_weight`: Handles severe anomaly imbalance (`balanced`, `balanced_subsample`, or `none`).
  - `random_state`: Seed for reproducible training results (Default: `42`).

### 1.2 XGBoost Classifier (`xgboost.XGBClassifier`)
- **Ensemble Strategy**: Gradient boosted decision tree optimization minimizing log-loss.
- **Configurable Hyperparameters**:
  - `n_estimators`: Boosting rounds (Default: `100`).
  - `max_depth`: Maximum depth of base learners (Default: `6`).
  - `learning_rate`: Shrinkage step size (Default: `0.1`).
  - `subsample`: Subsample ratio of training instances (Default: `0.8`).
  - `colsample_bytree`: Subsample ratio of columns per tree (Default: `0.8`).
  - `scale_pos_weight`: Controls class weighting for imbalanced anomaly data (Default: `1.0`).
  - `random_state`: Seed for reproducibility (Default: `42`).

---

## 2. Fair Model Comparison Protocol

To ensure fair comparison:
1. Both models are trained on the exact same `X_train`, `y_train` split.
2. If validation monitoring is enabled, both models use the exact same `X_val`, `y_val` split.
3. Both models are evaluated on the exact same held-out `X_test`, `y_test` split.
4. Neither model sees the held-out test split during training or hyperparameter tuning.

---

## 3. Evaluation Metrics

Evaluated strictly against the held-out test split:

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

$$\text{Precision} = \frac{TP}{TP + FP}$$

$$\text{Recall} = \frac{TP}{TP + FN}$$

$$\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

$$\text{False Positive Rate (FPR)} = \frac{FP}{FP + TN}$$

$$\text{ROC-AUC} = \text{Area under the Receiver Operating Characteristic curve}$$

$$\text{PR-AUC} = \text{Area under the Precision-Recall curve}$$

*Note: The positive class is always defined as the **Anomaly Class (1)**.*

---

## 4. Model Registry & Activation

Every trained model is serialized into an atomic `.joblib` bundle stored in `backend/artifacts/<model_id>.joblib`. The bundle contains:
- Trained estimator object.
- Fitted `PreprocessingBundle` (scalers, imputers, one-hot encoders).
- Exact feature column names and transformed feature schema.
- Comprehensive test evaluation metrics dictionary.
- Dataset identifier and version.
- Training duration in seconds.

**Activation Safety Rule**: A model can only be activated for production inference via explicit user selection in the **Model Comparison** screen. The system enforces feature schema compatibility before any incoming log can be evaluated.
