import sqlite3
from logg.dns_logging_config import logging


DB_FILE = 'dns_cache.db'


def create_table():
    """Create a table for DNS cache if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dns_cache (
            domain TEXT PRIMARY KEY,
            record TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_into_cache(domain, record):
    """Insert a DNS record into the cache."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO dns_cache (domain, record)
        VALUES (?, ?)
    ''', (domain, record))
    conn.commit()
    conn.close()
    logging.info(f"Inserted/Updated record for {domain} into cache.")


def query_cache(domain):
    """Query the cache for a DNS record."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT record FROM dns_cache WHERE domain = ?
    ''', (domain,))
    result = cursor.fetchone()
    conn.close()
    if result:
        logging.info(f"Cache hit for domain: {domain}")
        return result[0]
    else:
        logging.info(f"Cache miss for domain: {domain}")
        return None


def getzone(domain):
    """Simulate fetching DNS records from a zone."""
    
    logging.info(f"Fetching zone record for {domain}")
    return "192.168.1.1"
