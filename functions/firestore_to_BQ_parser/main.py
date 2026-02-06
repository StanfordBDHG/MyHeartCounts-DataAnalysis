"""
Firestore to BigQuery Delta Sync Pipeline for Health Observations

This script performs incremental (delta) syncing of user health data from Firestore to BigQuery.
It tracks the last sync timestamp and only processes health observations that have been newly 
issued since the last run, avoiding redundant full-table scans.

Key Features:
- Delta sync using 'issued' timestamp to detect new health observations
- Processes multiple HealthObservations subcollections per user
- Pagination support for large datasets
- Periodic checkpointing to CSV for recovery
- Sync metadata tracking in Firestore (_sync_metadata collection)
- Automatic skipping of users with no new data

Workflow:
1. Retrieves last sync timestamp from Firestore metadata
2. Iterates through all users, checking for new observations (issued > last_sync_time)
3. Filters and collects only newly issued health observations
4. Uploads users and observations to BigQuery (append mode)
5. Updates sync metadata with current timestamp for next run

Requirements:
- Firestore composite index on 'issued' field for each HealthObservations subcollection
- BigQuery tables: users3, observations3
- Firestore collection: _sync_metadata/last_sync (auto-created on first run)

Note: This script assumes that the 'issued' field is properly set on health observation documents and that the Firestore structure follows the expected pattern (users/{user_id}/HealthObservations_{
"""

import os
import pandas as pd
import pandas_gbq as pdg
import logging
import time
from utils import FirestoreStreamer
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
local_flag = True

def main():
    if local_flag:
        creds = "/home/juan/Desktop/Juan/code/.creds/creds-myheart-counts-development.json"
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds

    streamer = FirestoreStreamer(logger)
    
    # Capture start time for this sync
    sync_start_time = datetime.now()
    
    # Get last sync time
    last_sync_time = streamer.get_last_sync_time()
    if last_sync_time:
        logger.info(f"Running DELTA sync for documents issued after: {last_sync_time}")
    else:
        logger.info("Running FULL sync (no previous sync found)")
    
    users_accumulator = []
    obs_accumulator = []
    users_processed = 0
    users_with_updates = 0
    new_observations = 0
    
    # check for users first
    user_col = streamer.db.collection("users")
    for user_doc in streamer.stream_collection(user_col, batch_size=10):
        tic = time.time()
        user_id = user_doc.id
        users_processed += 1
        
        # is user_id in bigquery?
        if not user_id in streamer.users_in_BQ:
            # Add User Data
            users_accumulator.append({"user_id": user_id, **user_doc.to_dict(),'synced_at': sync_start_time})
            logger.info(f"Added user: {user_id} (not in BigQuery)")
            users_with_updates += 1
        
        tac = time.time()
        logger.info(f"Finished user: {user_id} in {tac - tic:.2f} seconds")
        
    if users_accumulator:
        # Save to BigQuery
        df = pd.DataFrame(users_accumulator)
        df['comorbidities'] = df['comorbidities'].astype(str)
        pdg.to_gbq(df, "myheart_counts_development.users3",
                    project_id="myheart-counts-development",
                    if_exists="replace",
                    table_schema=streamer.users_schema)
        logger.info(f"✓ Uploaded {len(df)} users to BigQuery")
        users_accumulator = []  # Clear after upload

    # check for observations after
    healthobservation_cols = streamer.db.collection("variables").document("healthobservation_cols").get().to_dict().get("cols", [])
    for heathobservation_col in healthobservation_cols:
        tic = time.time()
        try:
            # Add only new observations (filtered by 'issued' timestamp)
            obs_count = 0
            for obs in streamer.get_observations(heathobservation_col, last_sync_time):        
                obs_accumulator.append(obs)
                obs_count += 1
            
            logger.info(f"{heathobservation_col}  → Collected {obs_count} observations")        
            tac = time.time()
            logger.info(f"Finished healthobservation: {heathobservation_col} in {tac - tic:.2f} seconds")
                    
            if obs_accumulator:
                obs_df = pd.DataFrame(obs_accumulator)
                # Add sync timestamp for tracking
                obs_df['synced_at'] = pd.Timestamp.now()
                
                pdg.to_gbq(obs_df, "myheart_counts_development.observations3",
                            project_id="myheart-counts-development",
                            if_exists="replace",
                            chunksize=1000,
                            table_schema=streamer.observations_schema)
                logger.info(f"✓ Uploaded {len(obs_df)} observations to BigQuery")
                new_observations += len(obs_accumulator)
                obs_accumulator = []  # Clear after upload
        except Exception as e:
            logger.error(f"Error processing {heathobservation_col}: {e}")
            continue
        
        # add info to logs
        logger.info(f"\n{'='*60}")
        logger.info(f"Sync Summary:")
        logger.info(f"  Users scanned: {users_processed}")
        logger.info(f"  Users with new observations: {users_with_updates}")
        logger.info(f"  Total new observations collected: {new_observations}")
        logger.info(f"{'='*60}\n")

        # Update last sync time to the start of this sync
        streamer.update_last_sync_time(sync_start_time)
        logger.info("✓ Updated sync timestamp")
    else:
        logger.info("No new observations found - nothing to sync")
    
    logger.info("\n✅ Sync completed successfully")

if __name__ == "__main__":
    main()