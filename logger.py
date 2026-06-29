import logging
import sys

def setup_logging():
  logging.getLogger("httpx").setLevel(logging.WARNING)
  logging.getLogger("telegram").setLevel(logging.WARNING)
  
  logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    handlers = [
      logging.StreamHandler(sys.stdout),
      logging.FileHandler("ootlot.log"),
    ]
  )