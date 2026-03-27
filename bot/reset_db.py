import os
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv("c:/Users/rishabh/.gemini/antigravity/scratch/aico/bot/.env")

def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f"Deleting doc {doc.id} => {doc.reference.path}")
        # recursively delete subcollections
        for sub_coll in doc.reference.collections():
            delete_collection(sub_coll, batch_size)
        
        doc.reference.delete()
        deleted += 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

if __name__ == "__main__":
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        print("GCP_PROJECT_ID not found in bot/.env")
        exit(1)
        
    db = firestore.Client(project=project_id)
    
    print("Deleting 'servers' collection...")
    delete_collection(db.collection("servers"), 50)
    
    print("Deleting 'system' collection...")
    delete_collection(db.collection("system"), 50)
    
    print("Firestore reset complete.")
