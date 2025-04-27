import inspect
import os
import sys

from dotenv import load_dotenv
import logfire

def init_logfire(service_name: str = ""):
    if not os.getenv("LOGFIRE_INITIALIZED"):
        # initialize once only
        os.environ["LOGFIRE_INITIALIZED"] = "true"

        load_dotenv()
        service_name = service_name or get_full_module_name()
        logfire.configure(send_to_logfire="if-token-present",
                          token=os.getenv("LOGFIRE_TOKEN"),
                          environment=os.getenv("LOGFIRE_ENVIRONMENT", "development"),
                          distributed_tracing=True,
                          service_name=service_name)
        logfire.instrument_pydantic(record='failure')
        logfire.instrument_mcp()
        logfire.instrument_system_metrics()
        
        # logfire.install_auto_tracing(modules=['fastapi', 'mcp'],
        #                             min_duration=0.01,
        #                             check_imported_modules='ignore')


def get_full_module_name(stack_offset: int = 2) -> str:
    """
    Gets the full module name (x.y.z format) of the calling file,
    even if the file was run directly, handling duplicate sys.path entries.
    """
    frame = inspect.stack()[stack_offset]
    abs_filename = os.path.abspath(frame.filename)

    # Create a list of unique paths sorted by specificity (length)
    unique_paths = []
    for path in sys.path:
        abs_path = os.path.abspath(path)
        if abs_path not in [p for p in unique_paths]:
            unique_paths.append(abs_path)

    unique_paths.sort(key=len, reverse=True)

    # Find potential module paths
    potential_modules = []
    for path in unique_paths:
        if abs_filename.startswith(path + os.sep):
            rel_path = abs_filename[len(path) + 1 :]
            module_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
            potential_modules.append(module_path)

    # If we're in a package structure, prefer the longer (more specific) module path
    # that follows the expected package naming convention
    if potential_modules:
        # Look for paths that match package naming conventions
        for module_path in potential_modules:
            # Check if this module path looks like a proper package path
            # For example: 'conexio.coco.main' instead of just 'main'
            if "." in module_path and not module_path.startswith("_"):
                return module_path

        # If we didn't find a good package path, return the most specific path
        return potential_modules[0]

    # Fallback to just the filename without extension
    return os.path.splitext(os.path.basename(abs_filename))[0]

