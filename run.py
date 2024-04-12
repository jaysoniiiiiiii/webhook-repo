from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import datetime
import json  


app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["webhook_events"]
collection = db["events"]

# Function to store webhook event in MongoDB
def store_webhook_event(payload):
    # Convert ImmutableMultiDict to regular Python dictionary
    payload_dict = dict(payload)

    # Check if the payload contains the "action" key
    if "action" in payload_dict:
        # Extract the event type from the payload
        event_type = payload_dict["action"]
        
        # Handle different event types (e.g., push, pull_request, delete)
        if event_type == "push":
            # Process push event
            author = payload_dict["pusher"]["name"]
            branch = payload_dict["ref"].split("/")[-1]
            timestamp = payload_dict["head_commit"]["timestamp"]
            # Construct the message
            message = f"{author} pushed to {branch} on {timestamp}"
            print(message)
        elif event_type == "pull_request":
            # Process pull_request event
            author = payload_dict["pull_request"]["user"]["login"]
            from_branch = payload_dict["pull_request"]["head"]["ref"]
            to_branch = payload_dict["pull_request"]["base"]["ref"]
            timestamp = payload_dict["pull_request"]["created_at"]
            # Construct the message
            message = f"{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}"
            print(message)
        elif event_type == "merge":
            # Process merge event
            author = payload_dict["sender"]["login"]
            from_branch = payload_dict["pull_request"]["head"]["ref"]
            to_branch = payload_dict["pull_request"]["base"]["ref"]
            timestamp = payload_dict["pull_request"]["merged_at"]
            # Construct the message
            message = f"{author} merged branch {from_branch} to {to_branch} on {timestamp}"
            print(message)
        else:
            print("Unhandled event type:", event_type)
    else:
        print("No action key found in the payload")

    # Perform further processing or store the webhook event data in MongoDB
    try:
        # Insert the payload into MongoDB
        db.events.insert_one(payload_dict)
        print("Webhook event stored in MongoDB successfully")
    except Exception as e:
        print("Error storing webhook event in MongoDB:", e)


@app.route('/')
def index():
    # Fetch data from MongoDB
    events = db.events.find()
    
    # Format data for display
    formatted_events = []
    for event in events:
        payload = event['payload']
        payload_data = json.loads(payload)
        
        # Check if the payload contains the "action" key
        if 'action' in payload_data:
            action = payload_data['action']
            if action == 'push':
                author = payload_data['pusher']['name']
                branch = payload_data['ref'].split("/")[-1]
                timestamp = datetime.datetime.strptime(payload_data['head_commit']['timestamp'], "%Y-%m-%dT%H:%M:%S%z")
                formatted_event = f"{author} pushed to {branch} on {timestamp.strftime('%d %B %Y - %I:%M %p %Z')}"
            elif action == 'closed':
                author = payload_data['sender']['login']
                from_branch = payload_data['pull_request']['head']['ref']
                to_branch = payload_data['pull_request']['base']['ref']
                timestamp = datetime.datetime.strptime(payload_data['pull_request']['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                formatted_event = f"{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp.strftime('%d %B %Y - %I:%M %p %Z')}"
            elif action == 'merge':
                author = payload_data['sender']['login']
                from_branch = payload_data['pull_request']['head']['ref']
                to_branch = payload_data['pull_request']['base']['ref']
                timestamp = datetime.datetime.strptime(payload_data['pull_request']['merged_at'], "%Y-%m-%dT%H:%M:%SZ")
                formatted_event = f"{author} merged branch {from_branch} to {to_branch} on {timestamp.strftime('%d %B %Y - %I:%M %p %Z')}"
            else:
                formatted_event = "Unknown action"
        else:
            # If no action key found, assume it's a push event
            branch = payload_data['ref'].split("/")[-1]
            author = payload_data['pusher']['name']
            timestamp = datetime.datetime.strptime(payload_data['head_commit']['timestamp'], "%Y-%m-%dT%H:%M:%S%z")
            formatted_event = f"{author} pushed to {branch} on {timestamp.strftime('%d %B %Y - %I:%M %p %Z')}"

        formatted_events.append(formatted_event)

    return render_template('index.html', events=formatted_events)


@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    # Check if the content type is application/json or application/x-www-form-urlencoded
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json' and content_type != 'application/x-www-form-urlencoded':
        return jsonify({"error": "Unsupported Media Type"}), 415
    
    # Parse the request data based on content type
    if content_type == 'application/json':
        data = request.json
    elif content_type == 'application/x-www-form-urlencoded':
        data = request.form
    
    # Print the received data
    print("Received webhook data:")
    print(data)
    
    # Process the webhook event data
    store_webhook_event(data)
    
    webhook_data = collection.find()
    # Iterate over the data and print or process it as needed
    for data in webhook_data:
        print(data)

    # Send a response (optional)
    return jsonify({"message": "Webhook received successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
