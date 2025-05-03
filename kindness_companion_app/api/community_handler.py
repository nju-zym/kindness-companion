from flask import Blueprint, request, jsonify
import datetime

# TODO: Implement Anonymous Kindness Wall API endpoints (Future Enhancement as per README)
# This requires a self-hosted backend (Flask/FastAPI) and likely a cloud database.
# Endpoints needed:
# 1. POST /api/community/wall: Submit a new anonymous post.
# 2. GET /api/community/wall: Retrieve recent anonymous posts (with pagination).

community_bp = Blueprint('community', __name__)

# Placeholder storage (replace with database interaction)
wall_posts = []
next_post_id = 1

@community_bp.route('/wall', methods=['POST'])
def submit_wall_post():
    """
    API endpoint to submit a new anonymous post to the kindness wall.
    Expects JSON: {"message": "..."}
    """
    global next_post_id
    data = request.get_json()
    if not data or 'message' not in data or not data['message'].strip():
        return jsonify({"error": "Missing or empty message"}), 400

    message = data['message'].strip()
    # Basic validation/sanitization might be needed here

    # TODO: Replace with database insertion
    new_post = {
        "id": next_post_id,
        "message": message,
        "timestamp": datetime.datetime.utcnow().isoformat() # Add timestamp
    }
    wall_posts.append(new_post)
    next_post_id += 1

    print(f"Received wall post: {message}") # Placeholder
    return jsonify({"success": True, "post_id": new_post["id"]}), 201

@community_bp.route('/wall', methods=['GET'])
def get_wall_posts():
    """
    API endpoint to retrieve recent posts from the kindness wall.
    Supports pagination via query parameters: ?page=1&limit=10
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
    except ValueError:
        return jsonify({"error": "Invalid page or limit parameter"}), 400

    if page < 1 or limit < 1:
        return jsonify({"error": "Page and limit must be positive"}), 400

    # TODO: Replace with database query with pagination and ordering (e.g., newest first)
    # Simple in-memory pagination (newest first)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_posts = sorted(wall_posts, key=lambda p: p['timestamp'], reverse=True)[start_index:end_index]

    total_posts = len(wall_posts) # TODO: Get total count from database
    total_pages = (total_posts + limit - 1) // limit

    print(f"Retrieving wall posts: page={page}, limit={limit}") # Placeholder
    return jsonify({
        "posts": paginated_posts,
        "page": page,
        "limit": limit,
        "total_posts": total_posts,
        "total_pages": total_pages
    })