from flask import Flask, render_template, request, jsonify, url_for
import time
import os

app = Flask(__name__)

# =========================
#  In-Memory Data Stores
# =========================

# Example structure for annotations:
# {
#   'video_id': {
#       'annotations': [
#           { 'time': 10.2, 'comment': 'Oversize rock', 'user': 'Alice', 'timestamp': '2025-01-01 12:00:00' },
#           { 'time': 12.7, 'comment': 'Fly-rock hazard', 'user': 'Bob',   'timestamp': '2025-01-01 12:01:00' }
#       ],
#       'critical_moment': 5.0    # E.g., 'the moment of face movement'
#   }
# }
annotations_db = {}

@app.route('/')
def index():
    """
    Main page. We pass a video_id to identify which video is being annotated.
    In a real app, you might have multiple videos or pull this from a database.
    """
    # For simplicity, we’ll hardcode a single video_id:
    video_id = 'static/328_109.MP4'
    return render_template('index.html', video_id=video_id)

@app.route('/save_annotation', methods=['POST'])
def save_annotation():
    """
    Save annotation data (timestamp, comment, user, etc.) for a given video.
    """
    data = request.get_json()
    # Expected JSON structure:
    # {
    #   "video_id": "blast_demo_001",
    #   "time": "12.34",
    #   "comment": "Observing oversize rock near left corner",
    #   "user": "Alice"
    # }

    video_id = data.get('video_id')
    if not video_id:
        return jsonify({"status": "error", "message": "No video_id provided"}), 400

    # Initialize the video entry in our in-memory DB if not present
    if video_id not in annotations_db:
        annotations_db[video_id] = {'annotations': [], 'critical_moment': None}

    # Add server-side timestamp
    data['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Convert time to float for consistency
    data['time'] = float(data['time'])

    # Store the annotation
    annotations_db[video_id]['annotations'].append(data)

    return jsonify({"status": "success", "data": data}), 200

@app.route('/get_annotations', methods=['GET'])
def get_annotations():
    """
    Return all annotations for a given video_id.
    Example request: /get_annotations?video_id=blast_demo_001
    """
    video_id = request.args.get('video_id', None)
    if not video_id or video_id not in annotations_db:
        return jsonify([])  # Return empty list if no data

    return jsonify(annotations_db[video_id]['annotations'])

@app.route('/set_critical_moment', methods=['POST'])
def set_critical_moment():
    """
    Set the critical moment (auto-seek time) for a given video.
    Example: { "video_id": "blast_demo_001", "critical_moment": 5.0 }
    """
    data = request.get_json()
    video_id = data.get('video_id')
    critical_moment = data.get('critical_moment')

    if not video_id:
        return jsonify({"status": "error", "message": "No video_id provided"}), 400

    if video_id not in annotations_db:
        annotations_db[video_id] = {'annotations': [], 'critical_moment': None}

    # Store critical moment
    annotations_db[video_id]['critical_moment'] = float(critical_moment)

    return jsonify({"status": "success", "critical_moment": critical_moment}), 200

@app.route('/get_critical_moment', methods=['GET'])
def get_critical_moment():
    """
    Get the critical moment for a given video_id.
    Example request: /get_critical_moment?video_id=blast_demo_001
    """
    video_id = request.args.get('video_id', None)
    if not video_id or video_id not in annotations_db:
        return jsonify({"critical_moment": None})

    return jsonify({"critical_moment": annotations_db[video_id]['critical_moment']})

# =========================
#   Simple Reconciliation
# =========================
@app.route('/review_annotations', methods=['GET'])
def review_annotations():
    """
    Example endpoint to show how you might do a simple 'review' of multiple users' annotations.
    This is very minimal. In a real app, you would create a dedicated UI for reconciling labels.
    """
    video_id = request.args.get('video_id', None)
    if not video_id or video_id not in annotations_db:
        return jsonify({"annotations": [], "message": "No data for this video_id"})

    # In a real scenario, you’d group by time range, user, etc.
    # Here, we just return them all so we can see if multiple users differ.
    return jsonify({
        "video_id": video_id,
        "annotations": annotations_db[video_id]['annotations']
    })


@app.route('/videos')
def list_videos():
    # Path to your blasts directory inside static/
    blasts_dir = os.path.join(app.static_folder, 'blasts')
    
    # Subfolders like C1_328_109, C1_340_102, etc.
    blast_folders = [
        f for f in os.listdir(blasts_dir)
        if os.path.isdir(os.path.join(blasts_dir, f))
    ]

    blasts = []
    for folder in blast_folders:
        folder_path = os.path.join(blasts_dir, folder)
        # We'll scan for .mp4, .csv, and .pdf inside this folder
        video_file = None
        csv_file = None
        pdf_file = None

        # Iterate all files in the current subfolder
        for filename in os.listdir(folder_path):
            full_path = os.path.join(folder_path, filename)
            # Skip subdirectories if any
            if os.path.isdir(full_path):
                continue

            # Identify the file type by extension
            ext = os.path.splitext(filename)[1].lower()  # e.g., ".mp4" or ".pdf"
            if ext == '.mp4':
                video_file = filename
            elif ext == '.csv':
                csv_file = filename
            elif ext == '.pdf':
                pdf_file = filename
        
        # If we found all three, let's record them
        if video_file and csv_file and pdf_file:
            blasts.append({
                'folder': folder,
                'video_url': url_for('static', filename=f'blasts/{folder}/{video_file}'),
                'csv_url':   url_for('static', filename=f'blasts/{folder}/{csv_file}'),
                'pdf_url':   url_for('static', filename=f'blasts/{folder}/{pdf_file}'),
            })

    return render_template('videos.html', blasts=blasts)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
