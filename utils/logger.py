import logging
from rich.logging import RichHandler

def setup_logger(name: str = "Assistant") -> logging.Logger:
    """
    Configure and return a reusable logger with rich terminal formatting.
    
    Args:
        name (str): The name of the logger instance.
        
    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers are present to avoid duplication
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler with Rich formatting
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False
        )
        
        # Set a simple format since Rich handles most of the formatting
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
    return logger

# Create a default logger instance that can be imported directly
logger = setup_logger()
