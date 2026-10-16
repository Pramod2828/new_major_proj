# Smart-Log Backend Package
# Ensure torch mock is available to prevent DLL load failures in shap
import sys
import types

if "torch" not in sys.modules:
    try:
        import torch  # noqa: F401
    except (ImportError, OSError):
        m = types.ModuleType("torch")
        m.Tensor = type("Tensor", (), {})
        sys.modules["torch"] = m
