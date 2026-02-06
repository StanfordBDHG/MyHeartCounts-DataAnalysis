import os
import logging
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
local_flag = False

class FirestoreStreamer:
    """Focuses solely on streaming data out of Firestore efficiently."""
    
    def __init__(self, logger):
        self.logger = logger
        self.initialize_firebase()
        self.db = firestore.client()        
    
    def initialize_firebase(self):
        if not firebase_admin._apps:
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            
            if cred_path and os.path.exists(cred_path):
                # LOCAL: Use the JSON file provided in the env var
                self.logger.info(f"Initializing with local credentials: {cred_path}")
                cred = credentials.Certificate(cred_path)
            else:
                # CLOUD RUN: Use the built-in Service Account identity
                self.logger.info("Initializing with Application Default Credentials (ADC)")
                cred = credentials.ApplicationDefault()
                
            firebase_admin.initialize_app(cred)
    

def main():
    if local_flag:
        creds = "/home/juan/Desktop/Juan/code/.creds/creds-myheart-counts-development.json"
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds

    streamer = FirestoreStreamer(logger)
    
    # check for users first
    healthobservation_cols = []
    user_col = streamer.db.collection("users")
    for user_doc in user_col.stream():
        user_id = user_doc.id
        for col in user_col.document(user_id).collections():
            if col.id.startswith("HealthObservations"):
                healthobservation_cols.append(col.id)
    # deduplicate column names
    healthobservation_cols = np.unique(healthobservation_cols).tolist()
    streamer.db.collection("variables").document("healthobservation_cols").set({"cols": healthobservation_cols})
    logger.info(f"Identified {len(healthobservation_cols)} unique health observation columns: {healthobservation_cols}")

if __name__ == "__main__":
    main()