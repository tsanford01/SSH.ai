import os
import requests
from pathlib import Path
import platform

def download_llamafile():
    """Download the appropriate llamafile model."""
    
    # Create models directory if it doesn't exist
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Define model path
    model_path = models_dir / "llava-v1.5-7b-q4.llamafile"
    if platform.system() == "Windows":
        model_path = model_path.with_suffix('.exe')
    
    # Download URL
    url = "https://huggingface.co/Mozilla/llava-v1.5-7b-llamafile/resolve/main/llava-v1.5-7b-q4.llamafile"
    
    print(f"Downloading llamafile model to {model_path}...")
    
    # Download the file
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Write to file
    with open(model_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Make executable on Unix systems
    if platform.system() != "Windows":
        os.chmod(model_path, 0o755)
    
    print("Download complete!")

if __name__ == "__main__":
    download_llamafile() 