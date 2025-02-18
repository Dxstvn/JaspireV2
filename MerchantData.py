# merchant_data.py
from square.client import Client

def get_merchant_info(access_token, environment="sandbox"):
    client = Client(access_token=access_token, environment=environment)
    resp = client.merchants.retrieve_merchant("me")
    if resp.is_success():
        return resp.body["merchant"]
    else:
        print("Error retrieving merchant info:", resp.errors)
        return None

def get_location_info(access_token, environment="sandbox", location_id=None):
    client = Client(access_token=access_token, environment=environment)
    resp = client.locations.list_locations()
    if resp.is_success():
        all_locations = resp.body["locations"]
        if not location_id:
            return all_locations
        for loc in all_locations:
            if loc["id"] == location_id:
                return loc
        print(f"Location ID {location_id} not found.")
        return None
    else:
        print("Error listing locations:", resp.errors)
        return None
