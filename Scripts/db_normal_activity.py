import psycopg2
import time
import random
import numpy as np # (1) Import for generating random numbers

# --- CONFIGURATION ---
DB_HOST = '192.168.56.10'
DB_NAME = 'covert_analysis_db'
DB_USER = 'projectuser'
DB_PASSWORD = 'P@sswOrd2025'

# --- SIMULATION PARAMETERS ---
QUERY_COUNT = 5000  # Increased count for better data volume
AVG_DELAY_MS = 50   # (2) Target average delay (mean of the distribution)
STD_DEV_MS = 10     # (3) Standard deviation (how much noise/jitter)

# --- QUERY POOL ---
# (4) Define a pool of different query types for randomness
QUERY_POOL = [
    "SELECT COUNT(*) FROM test_table;",
    "SELECT * FROM test_table WHERE id = {};",
    "INSERT INTO test_table (data) VALUES ('normal_data_{}');",
    "UPDATE test_table SET data = 'updated_data_{}' WHERE id = (SELECT MIN(id) FROM test_table);"
]

def generate_queries(count):
    """Generates a list of queries by randomly selecting from the pool."""
    queries = []
    for i in range(count):
        # (5) Randomly choose a query template
        query_template = random.choice(QUERY_POOL)
        
        # Format the query with a random number to ensure different database input
        random_id = random.randint(1, 100000) 
        queries.append(query_template.format(random_id))
    return queries

def run_db_simulation():
    # ... (Connection setup remains the same) ...
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        print(f"Successfully connected to PostgreSQL at {DB_HOST}")
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return

    queries_to_run = generate_queries(QUERY_COUNT) # (6) Generate the randomized list
    print(f"Starting simulation of {QUERY_COUNT} randomized queries...")
    
    for i, query in enumerate(queries_to_run):
        # --- TIMING ---
        # (7) Generate a random delay using a normal (Gaussian) distribution
        delay_ms = np.random.normal(AVG_DELAY_MS, STD_DEV_MS) 
        # Ensure delay is positive
        delay_ms = max(5, delay_ms) 
        delay_seconds = delay_ms / 1000.0
        
        time.sleep(delay_seconds) # Pauses for a realistic, noisy duration
        
        # ... (Query execution remains the same) ...
        try:
            cur.execute(query)
            conn.commit()
            
            if i % 500 == 0:
                print(f"Executed query {i}/{QUERY_COUNT} with delay: {delay_ms:.2f}ms")
                
        except Exception as e:
            # Note: INSERT/UPDATE errors might occur if the random ID doesn't exist. This is normal noise.
            print(f"Query execution error on query: '{query[:30]}...' Error: {e}")

    cur.close()
    conn.close()
    print("Simulation complete.")

if __name__ == '__main__':
    run_db_simulation()