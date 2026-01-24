# Import functions from the bulk transcribe module
import importlib.util
import sys
from pathlib import Path

# Load the actual module dynamically
module_path = Path(__file__).parent / "02_Bulk_Transcribe.py"
spec = importlib.util.spec_from_file_location("bulk_transcribe_module", module_path)
bulk_transcribe_module = importlib.util.module_from_spec(spec)
sys.modules["bulk_transcribe_module"] = bulk_transcribe_module
spec.loader.exec_module(bulk_transcribe_module)

# Re-export the functions
categorize_error = bulk_transcribe_module.categorize_error
update_status_safe = bulk_transcribe_module.update_status_safe
