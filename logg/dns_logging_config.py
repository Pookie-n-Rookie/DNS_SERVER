import logging
from pathlib import Path


LOG_FILE = "logs/dns_caching.log"
Path("logs").mkdir(exist_ok=True)  

# Setting up logging configuration
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,  
    format='%(asctime)s - %(levelname)s - %(message)s',  
    datefmt='%Y-%m-%d %H:%M:%S'  
)
