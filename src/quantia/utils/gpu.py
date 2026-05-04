"""GPU detection and hardware discovery utilities."""

from __future__ import annotations
import subprocess
import shutil


def is_nvidia_gpu_available() -> bool:
    """
    Check if an NVIDIA GPU is present and accessible via nvidia-smi.
    This is the core discovery mechanism for Phase 1.
    """
    if shutil.which("nvidia-smi") is None:
        return False
    
    try:
        # Run nvidia-smi -L to list GPUs. 
        # returncode 0 means drivers are working and a GPU was found.
        result = subprocess.run(
            ["nvidia-smi", "-L"], 
            capture_output=True, 
            text=True, 
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return result.returncode == 0 and "GPU" in result.stdout
    except Exception:
        return False


def get_gpu_info() -> str:
    """
    Get the name of the first detected NVIDIA GPU.
    """
    if not is_nvidia_gpu_available():
        return "None"
        
    try:
        # Query for the specific GPU name
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        if result.returncode == 0:
            # Take the first line (first GPU)
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
        
    return "NVIDIA GPU Detected"


def get_cuda_version() -> str:
    """
    Attempt to extract the CUDA version from nvidia-smi.
    """
    if not is_nvidia_gpu_available():
        return "N/A"
        
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        if result.returncode == 0:
            # The output usually contains "CUDA Version: XX.X"
            for line in result.stdout.split("\n"):
                if "CUDA Version:" in line:
                    return line.split("CUDA Version:")[1].split("|")[0].strip()
    except Exception:
        pass
        
    return "Unknown"
