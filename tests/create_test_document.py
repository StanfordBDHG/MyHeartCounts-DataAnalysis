# this is a file to add a new document to the firestore database for testing purposes. It will be used to test the parser and the export to BQ. It will be added to the same user as the existing documents, with a unique subcollection name and a unique document ID. The document will have the same structure as the existing documents, but with different values. This will allow us to test that the parser can handle new documents and that the export to BQ can handle new documents.

import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Generator, Dict
import logging
import time
import re

# Simplified Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

prefixes = [
    "HealthObservations_HKQuantityTypeIdentifier",
    "HealthObservations_HKCategoryTypeIdentifier",
    "HealthObservations_com.apple.SensorKit.",
    "HealthObservations_HKDataTypeIdentifier",
    "HealthObservations_HKWorkoutTypeIdentifier",
    "HealthObservations_MHC"
]
pattern = re.compile(f"^({'|'.join(map(re.escape, prefixes))})")

def clean_metric(metric):
    clean = pattern.sub('', metric)
    return clean if clean else 'Workout'

class FirestoreStreamer:
    """Focuses solely on streaming data out of Firestore efficiently."""
    
    def __init__(self, creds_path: str):
        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def stream_collection(self, collection_ref, batch_size: int = 500) -> Generator[Dict, None, None]:
        """Generic generator to handle pagination logic once."""
        last_doc = None
        while True:
            query = collection_ref.limit(batch_size)
            if last_doc:
                query = query.start_after(last_doc)
            
            docs = list(query.stream())
            if not docs:
                break
                
            for doc in docs:
                yield doc
            
            last_doc = docs[-1]
            time.sleep(0.1) # Soft rate limit

    def get_user_observations(self, user_id: str) -> Generator[Dict, None, None]:
        """Streams health observations for a single user."""
        user_ref = self.db.collection("users").document(user_id)
        
        # Only fetch subcollections that match the pattern
        for sub in user_ref.collections():
            if not sub.id.startswith("HealthObservations"):
                continue
                
            for doc in self.stream_collection(sub):
                data = doc.to_dict()
                period = data.get('effectivePeriod')
                
                if period and isinstance(period, dict):
                    yield {
                        **period,
                        'user_id': user_id,
                        'metric': clean_metric(sub.id),
                        'value': data.get('valueQuantity', {}).get('value'),
                        'unit': data.get('valueQuantity', {}).get('unit'),
                        'value_str': data.get('valueString')
                    }


if __name__ == "__main__":
    creds = "/home/juan/Desktop/Juan/code/.creds/creds-myheart-counts-development.json"
    streamer = FirestoreStreamer(creds)
    # # get one doc
    # doc = streamer.db.collection("users").document("PmkvUwmPOaYOvlbT4AtXsxKHXjM2").get()
    # # write another document to firestore - the exact user_doc as a test
    # test_doc_ref = streamer.db.collection("users").document("PmkvUwmPOaYOvlbT4AtXsxKHXjM2")
    # test_doc_ref.set(doc.to_dict())  # Write the first user document as a test   



    # Reference the specific subcollection under the user
    obs_subcollection = "HealthObservations_HKQuantityTypeIdentifierStepCount"
    user_id = "PmkvUwmPOaYOvlbT4AtXsxKHXjM2"

    new_observation = {
        "effectivePeriod": {
            "start": "2023-10-27T10:00:00Z",
            "end": "2023-10-27T10:15:00Z"
        },
        "valueQuantity": {
            "value": 500,
            "unit": "steps"
        },
        
        "issued": pd.Timestamp.now()  # Track when this observation was added
        
    }

    # .add() automatically creates a new document with a unique ID
    streamer.db.collection("users").document(user_id)\
        .collection(obs_subcollection).add(new_observation)