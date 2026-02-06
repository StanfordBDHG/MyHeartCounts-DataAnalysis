import re
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Generator, Dict, Optional
from datetime import datetime
import time
import os
import pandas_gbq as pdg

prefixes = [
    "HealthObservations_HKQuantityTypeIdentifier",
    "HealthObservations_HKCategoryTypeIdentifier",
    "HealthObservations_com.apple.SensorKit.",
    "HealthObservations_HKDataTypeIdentifier",
    "HealthObservations_HKWorkoutTypeIdentifier",
    "HealthObservations_MHC"
]

users_schema  = [
    {'name': 'user_id', 'type': 'STRING'},
    {'name': 'educationUS', 'type': 'STRING'},
    {'name': 'futureStudies', 'type': 'BOOL'},
    {'name': 'comorbidities', 'type': 'STRING'}, # Stored as string since BQ doesn't have a generic 'object'
    {'name': 'preferredNotificationTime', 'type': 'STRING'},
    {'name': 'householdIncomeUS', 'type': 'INT64'},
    {'name': 'mhcGenderIdentity', 'type': 'INT64'},
    {'name': 'disabled', 'type': 'BOOL'},
    {'name': 'lastSignedConsentDate', 'type': 'TIMESTAMP'},
    {'name': 'bloodType', 'type': 'INT64'},
    {'name': 'timeZone', 'type': 'STRING'},
    {'name': 'usRegion', 'type': 'STRING'},
    {'name': 'dateOfBirth', 'type': 'TIMESTAMP'},
    {'name': 'mostRecentOnboardingStep', 'type': 'STRING'},
    {'name': 'raceEthnicity', 'type': 'INT64'},
    {'name': 'preferredWorkoutTypes', 'type': 'STRING'},
    {'name': 'fcmToken', 'type': 'STRING'},
    {'name': 'biologicalSexAtBirth', 'type': 'INT64'},
    {'name': 'heightInCM', 'type': 'FLOAT64'},
    {'name': 'stageOfChange', 'type': 'STRING'},
    {'name': 'lastSignedConsentVersion', 'type': 'STRING'},
    {'name': 'latinoStatus', 'type': 'INT64'},
    {'name': 'dateOfEnrollment', 'type': 'TIMESTAMP'},
    {'name': 'didOptInToTrial', 'type': 'BOOL'},
    {'name': 'language', 'type': 'STRING'},
    {'name': 'lastActiveDate', 'type': 'TIMESTAMP'},
    {'name': 'participantGroup', 'type': 'INT64'},
    {'name': 'weightInKG', 'type': 'FLOAT64'},
    {'name': 'synced_at', 'type': 'TIMESTAMP'}
]

observations_schema = [
    {'name': 'user_id', 'type': 'STRING'},
    {'name': 'metric', 'type': 'STRING'},
    {'name': 'value', 'type': 'FLOAT64'},
    {'name': 'unit', 'type': 'STRING'},
    {'name': 'value_str', 'type': 'STRING'},
    {'name': 'issued', 'type': 'TIMESTAMP'},
    {'name': 'synced_at', 'type': 'TIMESTAMP'}
]

pattern = re.compile(f"^({'|'.join(map(re.escape, prefixes))})")

def clean_metric(metric):
    clean = pattern.sub('', metric)
    return clean if clean else 'Workout'

class FirestoreStreamer:
    """Focuses solely on streaming data out of Firestore efficiently."""
    
    def __init__(self, logger):
        self.logger = logger
        self.initialize_firebase()
        self.db = firestore.client()
        query = f"SELECT user_id FROM `myheart_counts_development.users3`"
        self.users_in_BQ = tuple(pdg.read_gbq(query, project_id="myheart-counts-development", dialect="standard")['user_id'])
        self.users_schema = users_schema
        self.observations_schema = observations_schema
    
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

    def get_last_sync_time(self) -> Optional[datetime]:
        """Retrieve the last sync timestamp from a tracking document."""
        try:
            sync_doc = self.db.collection("_sync_metadata").document("last_sync").get()
            if sync_doc.exists:
                timestamp = sync_doc.to_dict().get('timestamp')
                self.logger.info(f"Last sync was at: {timestamp}")
                return timestamp
            else:
                self.logger.info("No previous sync found")
                return None
        except Exception as e:
            self.logger.warning(f"Could not retrieve last sync time: {e}")
            return None
    
    def update_last_sync_time(self, sync_time: datetime):
        """Update the last sync timestamp."""
        try:
            self.db.collection("_sync_metadata").document("last_sync").set({
                'timestamp': sync_time,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            self.logger.info(f"Updated last sync time to: {sync_time}")
        except Exception as e:
            self.logger.error(f"Failed to update sync time: {e}")
    
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
            time.sleep(0.1)
    
    def get_observations(self, heathobservation_col: str, last_sync_time: Optional[datetime] = None) -> Generator[Dict, None, None]:
        """Streams health observations for a single user, filtering by issued timestamp."""
        # pagination was removed - might consider re-instantiating it for scalability if needed, but for now we rely on Firestore's internal optimizations for collection_group queries with proper indexing
        query = self.db.collection_group(heathobservation_col)
    
        if last_sync_time:
            query = query.where("issued", ">", last_sync_time).order_by("issued")
        
        docs = query.stream()

        for doc in docs:
            user_id = doc.reference.parent.parent.id
            data = doc.to_dict()
            period = data.get('effectivePeriod')
            issued = data.get('issued')
            
            if period and isinstance(period, dict):
                yield {
                    **period,
                    'user_id': user_id,
                    'metric': clean_metric(heathobservation_col),
                    'value': data.get('valueQuantity', {}).get('value'),
                    'unit': data.get('valueQuantity', {}).get('unit'),
                    'value_str': data.get('valueString'),
                    'issued': issued  # Include 'issued' timestamp for tracking
                }
        
        #time.sleep(0.05)
