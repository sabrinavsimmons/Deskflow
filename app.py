from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db, init_db
import csv
import io
from flask import Response

app = Flask(__name__)
app.secret_key = 'deskflow-secret-key-change-in-production'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access DeskFlow.'

with app.app_context():
    init_db()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            login_user(User(user['id'], user['username']))
            return redirect(url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = get_db()
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '')
    query = 'SELECT * FROM tickets WHERE 1=1'
    params = []
    if status_filter != 'all':
        query += ' AND status = ?'
        params.append(status_filter)
    if search_query:
        query += ' AND (title LIKE ? OR category LIKE ? OR assignee LIKE ?)'
        params.extend(['%' + search_query + '%'] * 3)
    query += ' ORDER BY created_at DESC'
    tickets = conn.execute(query, params).fetchall()
    all_tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()
    open_count = sum(1 for t in all_tickets if t['status'] == 'open')
    in_progress_count = sum(1 for t in all_tickets if t['status'] == 'in-progress')
    resolved_count = sum(1 for t in all_tickets if t['status'] == 'resolved')
    critical_count = sum(1 for t in all_tickets if t['priority'] == 'critical')
    return render_template('index.html',
        tickets=tickets,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        critical_count=critical_count,
        status_filter=status_filter,
        search_query=search_query
    )

@app.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        category = request.form['category']
        assignee = request.form['assignee']
        requester = request.form['requester']
        conn = get_db()
        conn.execute(
            'INSERT INTO tickets (title, description, priority, category, assignee, requester) VALUES (?, ?, ?, ?, ?, ?)',
            (title, description, priority, category, assignee, requester)
        )
        conn.commit()
        conn.close()
        flash('Ticket created successfully.')
        return redirect(url_for('index'))
    return render_template('new_ticket.html')

@app.route('/ticket/<int:ticket_id>')
@login_required
def ticket(ticket_id):
    conn = get_db()
    t = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    notes = conn.execute('SELECT * FROM notes WHERE ticket_id = ? ORDER BY created_at ASC', (ticket_id,)).fetchall()
    conn.close()
    if t is None:
        return 'Ticket not found.', 404
    return render_template('ticket.html', ticket=t, notes=notes)

@app.route('/ticket/<int:ticket_id>/update', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    status = request.form['status']
    conn = get_db()
    conn.execute('UPDATE tickets SET status = ? WHERE id = ?', (status, ticket_id))
    conn.commit()
    conn.close()
    flash('Status updated.')
    return redirect(url_for('ticket', ticket_id=ticket_id))

@app.route('/ticket/<int:ticket_id>/note', methods=['POST'])
@login_required
def add_note(ticket_id):
    author = current_user.username
    content = request.form['content']
    conn = get_db()
    conn.execute('INSERT INTO notes (ticket_id, author, content) VALUES (?, ?, ?)', (ticket_id, author, content))
    conn.commit()
    conn.close()
    flash('Note added.')    
    return redirect(url_for('ticket', ticket_id=ticket_id))

@app.route('/ticket/<int:ticket_id>/edit')
@login_required
def edit_ticket(ticket_id):
    conn = get_db()
    t = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()
    if t is None:
        return 'Ticket not found.', 404
    return render_template('edit_ticket.html', ticket=t)

@app.route('/ticket/<int:ticket_id>/edit', methods=['POST'])
@login_required
def update_ticket_full(ticket_id):
    title = request.form['title']
    description = request.form['description']
    priority = request.form['priority']
    category = request.form['category']
    assignee = request.form['assignee']
    requester = request.form['requester']
    conn = get_db()
    conn.execute(
        '''UPDATE tickets SET title = ?, description = ?, priority = ?,
           category = ?, assignee = ?, requester = ? WHERE id = ?''',
        (title, description, priority, category, assignee, requester, ticket_id)
    )
    conn.commit()
    conn.close()
    flash('Ticket updated.')
    return redirect(url_for('ticket', ticket_id=ticket_id))

@app.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    conn = get_db()
    conn.execute('DELETE FROM notes WHERE ticket_id = ?', (ticket_id,))
    conn.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
    conn.commit()
    conn.close()
    flash('Ticket deleted.')
    return redirect(url_for('index'))

@app.route('/export')
@login_required
def export_csv():
    conn = get_db()
    tickets = conn.execute('SELECT * FROM tickets ORDER BY created_at DESC').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Title', 'Priority', 'Status', 'Category', 'Assignee', 'Requester', 'Created'])
    for t in tickets:
        writer.writerow([t['id'], t['title'], t['priority'], t['status'], t['category'], t['assignee'], t['requester'], t['created_at']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=deskflow-tickets.csv'}
    )
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()

        if not check_password_hash(user['password_hash'], current_password):
            conn.close()
            flash('Current password is incorrect.')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            conn.close()
            flash('New passwords do not match.')
            return redirect(url_for('change_password'))

        if len(new_password) < 8:
            conn.close()
            flash('Password must be at least 8 characters.')
            return redirect(url_for('change_password'))

        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?',
            (generate_password_hash(new_password), current_user.id))
        conn.commit()
        conn.close()
        flash('Password changed successfully.')
        return redirect(url_for('index'))

    return render_template('change_password.html')
@app.route('/users')
@login_required
def manage_users():
    conn = get_db()
    users = conn.execute('SELECT id, username FROM users ORDER BY username').fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    username = request.form['username'].strip()
    password = request.form['password']

    if not username or not password:
        flash('Username and password are required.')
        return redirect(url_for('manage_users'))

    if len(password) < 8:
        flash('Password must be at least 8 characters.')
        return redirect(url_for('manage_users'))

    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        flash('Username already exists.')
        return redirect(url_for('manage_users'))

    conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
        (username, generate_password_hash(password)))
    conn.commit()
    conn.close()
    flash('User ' + username + ' created.')
    return redirect(url_for('manage_users'))

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.')
        return redirect(url_for('manage_users'))

    conn = get_db()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted.')
    return redirect(url_for('manage_users'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
