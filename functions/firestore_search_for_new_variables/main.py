import os
import logging
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore_admin_v1

project_id = "	myheart-counts-development"
database_id = "(default)"
    
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
    
def update_indexes(collection,field_path = "issued"):
    client = firestore_admin_v1.FirestoreAdminClient()
    
    parent = f"projects/{project_id}/databases/{database_id}/collectionGroups/{collection}/fields/{field_path}"
    
    # 3. Deploy via API call (This replaces 'firebase deploy')
    field_config = firestore_admin_v1.Field(
        name=parent,
        index_config={
            "indexes": [
        {
          "order": "ASCENDING",
          "queryScope": "COLLECTION"
        },
        {
          "order": "DESCENDING",
          "queryScope": "COLLECTION"
        },
        {
          "arrayConfig": "CONTAINS",
          "queryScope": "COLLECTION"
        },
        {
          "order": "ASCENDING",
          "queryScope": "COLLECTION_GROUP"
        },
        {
          "order": "DESCENDING",
          "queryScope": "COLLECTION_GROUP"
        },
        {
          "arrayConfig": "CONTAINS",
          "queryScope": "COLLECTION_GROUP"
        }
      ], # Empty list creates an exemption
            "uses_ancestor_config": False
        }
    )
    
    operation = client.update_field(field=field_config)
    return f"Update started: {operation.operation.name}"

def main(request=None):
    if local_flag:
        creds = "/home/juan/Desktop/Juan/code/.creds/creds-myheart-counts-development.json"
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds

    streamer = FirestoreStreamer(logger)

    # health observation columns from database
    preexisting_healthobs_cols = streamer.db.collection("variables").document("healthobservation_cols").get()
    
    # check for users first
    healthobservation_cols = []
    user_col = streamer.db.collection("users")
    for user_doc in user_col.stream():
        user_id = user_doc.id
        for col in user_col.document(user_id).collections():
            if col.id.startswith("HealthObservations") and col not in preexisting_healthobs_cols:
                healthobservation_cols.append(col.id)
                # add to the index
                try:
                    update_indexes(col.id,field_path = "issued")
                except Exception as e: 
                    print(e)

    # deduplicate column names
    healthobservation_cols = np.unique(healthobservation_cols).tolist()
    streamer.db.collection("variables").document("healthobservation_cols").set({"cols": healthobservation_cols + preexisting_healthobs_cols})
    logger.info(f"Identified {len(healthobservation_cols)} new unique health observation columns: {healthobservation_cols}")
    
    return "Success", 200

if __name__ == "__main__":
    main()