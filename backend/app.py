from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Issue
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///issues.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

@app.before_first_request
def create_tables():
    db.create_all()
    
    # Add sample data if database is empty
    if Issue.query.count() == 0:
        sample_issues = [
            Issue(
                title="Fix login bug",
                description="Users cannot login with special characters in password",
                status="Open",
                priority="High",
                assignee="John Doe"
            ),
            Issue(
                title="Add dark mode",
                description="Implement dark mode theme for better user experience",
                status="In Progress",
                priority="Medium",
                assignee="Jane Smith"
            ),
            Issue(
                title="Optimize database queries",
                description="Database queries are running slowly on large datasets",
                status="Open",
                priority="Low",
                assignee="Bob Johnson"
            ),
            Issue(
                title="Update documentation",
                description="API documentation needs to be updated with new endpoints",
                status="Closed",
                priority="Medium",
                assignee="Alice Wilson"
            )
        ]
        
        for issue in sample_issues:
            db.session.add(issue)
        db.session.commit()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/issues', methods=['GET'])
def get_issues():
    # Get query parameters
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    assignee_filter = request.args.get('assignee', '')
    sort_by = request.args.get('sortBy', 'updatedAt')
    sort_order = request.args.get('sortOrder', 'desc')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    # Build query
    query = Issue.query
    
    # Apply search
    if search:
        query = query.filter(Issue.title.contains(search))
    
    # Apply filters
    if status_filter:
        query = query.filter(Issue.status == status_filter)
    if priority_filter:
        query = query.filter(Issue.priority == priority_filter)
    if assignee_filter:
        query = query.filter(Issue.assignee == assignee_filter)
    
    # Apply sorting
    sort_column = getattr(Issue, sort_by.replace('At', '_at') if 'At' in sort_by else sort_by)
    if sort_order.lower() == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    paginated = query.paginate(
        page=page, 
        per_page=page_size, 
        error_out=False
    )
    
    return jsonify({
        'data': [issue.to_dict() for issue in paginated.items],
        'total': paginated.total,
        'page': page,
        'pageSize': page_size,
        'totalPages': paginated.pages
    })

@app.route('/issues/<issue_id>', methods=['GET'])
def get_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    return jsonify(issue.to_dict())

@app.route('/issues', methods=['POST'])
def create_issue():
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    issue = Issue.from_dict(data)
    db.session.add(issue)
    db.session.commit()
    
    return jsonify(issue.to_dict()), 201

@app.route('/issues/<issue_id>', methods=['PUT'])
def update_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update fields
    if 'title' in data:
        issue.title = data['title']
    if 'description' in data:
        issue.description = data['description']
    if 'status' in data:
        issue.status = data['status']
    if 'priority' in data:
        issue.priority = data['priority']
    if 'assignee' in data:
        issue.assignee = data['assignee']
    
    issue.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(issue.to_dict())

if __name__ == '__main__':
    app.run(debug=True, port=5000)