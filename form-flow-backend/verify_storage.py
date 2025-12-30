
import sys
import logging
from pathlib import Path
import json
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the storage logic directly from routers/pdf
# We need to mock fastapi stuff if imported, but _save_upload is standalone dependency-wise
# Actually, importing routers.pdf might trigger app creation / imports. 
# Let's just replicate the logic to test the PATH resolution first.

STORAGE_DIR = Path("storage")
UPLOAD_DIR = STORAGE_DIR / "uploads"
FILLED_DIR = STORAGE_DIR / "filled"

def test_storage():
    print(f"Current Working Directory: {Path.cwd()}")
    print(f"Target Storage Dir: {STORAGE_DIR.absolute()}")
    
    # Ensure directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Test Write
    test_id = "test_verify_storage"
    pdf_path = UPLOAD_DIR / f"{test_id}.pdf"
    content = b"fake pdf content"
    
    print(f"Attempting to write to: {pdf_path}")
    try:
        pdf_path.write_bytes(content)
        print("✅ Write successful")
    except Exception as e:
        print(f"❌ Write failed: {e}")
        return

    # Test Read
    try:
        read_content = pdf_path.read_bytes()
        if read_content == content:
            print("✅ Read match successful")
        else:
            print("❌ Read content mismatch")
    except Exception as e:
        print(f"❌ Read failed: {e}")

    # Cleanup
    try:
        pdf_path.unlink()
        print("✅ Cleanup successful")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    test_storage()
