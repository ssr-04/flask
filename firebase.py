import firebase_admin
import os
from firebase_admin import credentials
from firebase_admin import db
import json

service_account_json_string = os.getenv('FIREBASE_CREDENTIALS_JSON')
service_account_info = json.loads(service_account_json_string)
DATABASE_URL = "https://cardio-e9bda-default-rtdb.asia-southeast1.firebasedatabase.app/"  # <--- UPDATE THIS

# Global variable to track initialization
_firebase_initialized = False

def initialize_firebase_app():
    """Initializes the Firebase Admin SDK if not already initialized."""
    global _firebase_initialized
    if not _firebase_initialized:
        try:
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred, {
                'databaseURL': DATABASE_URL
            })
            _firebase_initialized = True
            print("Firebase App initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase App: {e}")
            # Potentially raise the exception or handle it as critical
            raise
    # else:
    #     print("Firebase App already initialized.")


def get_health_data_from_firebase(index_to_fetch):
    global _firebase_initialized
    data_path = "/"
    if not _firebase_initialized:
        initialize_firebase_app()
    try:
        # Get a reference to the data path
        ref = db.reference(data_path)
        # Fetch the data from Firebase
        firebase_data = ref.get()

        if firebase_data is None:
            print(f"Error: No data found at path '{data_path}' in Firebase.")
            return None

        if not isinstance(firebase_data, dict):
            print(f"Error: Data at path '{data_path}' is not a dictionary as expected.")
            return None

        health_data_container = firebase_data.get("healthData")

        if health_data_container is None:
            print(f"Error: 'healthData' key not found in data at path '{data_path}'.")
            return None

        # Firebase stores array-like objects with integer keys as objects (dictionaries in Python)
        # The keys will be strings (e.g., "0", "1", "2").
        if isinstance(health_data_container, dict):
            str_index = str(index_to_fetch)
            if str_index in health_data_container:
                return health_data_container[str_index]
            else:
                # Fallback if by some chance it was stored with an integer key
                # (less likely with JSON from Firebase RTDB for non-sequential keys)
                if index_to_fetch in health_data_container:
                     return health_data_container[index_to_fetch]
                print(f"Error: Index '{index_to_fetch}' (as string '{str_index}' or int) not found in 'healthData' dictionary.")
                return None
        elif isinstance(health_data_container, list):
            # This case would occur if Firebase keys were "0", "1", "2", ... sequentially
            if 0 <= index_to_fetch < len(health_data_container):
                return health_data_container[index_to_fetch]
            else:
                print(f"Error: Index {index_to_fetch} is out of bounds for 'healthData' list (length {len(health_data_container)}).")
                return None
        else:
            print("Error: 'healthData' is neither a dictionary nor a list.")
            return None

    except Exception as e:
        print(f"An error occurred while fetching or processing Firebase data: {e}")
        return None
