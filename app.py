from flask import Flask, render_template, request, redirect, url_for
from database import get_db, init_db

app = Flask(__name__)

with app.app_context():
    init_db()

@app.route('/')
def index():
    conn = get_db()
    tickets = conn.execute(
        'SELECT * FROM tickets ORDER BY created_at DESC'
    ).fetchall()
    conn.close()

    open_count = sum(1 for t in tickets if t['status'] == 'open')
    in_progress_count = sum(1 for t in tickets if t['status'] == 'in-progress')
    resolved_count = sum(1 for t in tickets if t['status'] == 'resolved')
    critical_count = sum(1 for t in tickets if t['priority'] == 'critical')

    return render_template('index.html',
        tickets=tickets,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        critical_count=critical_count
    )

@app.route('/ticket/new', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))

    return render_template('new_ticket.html')

@app.route('/ticket/<int:ticket_id>')
def ticket(ticket_id):
    conn = get_db()
    t = conn.execute(
        'SELECT * FROM tickets WHERE id = ?', (ticket_id,)
    ).fetchone()
    notes = conn.execute(
        'SELECT * FROM notes WHERE ticket_id = ? ORDER BY created_at ASC', (ticket_id,)
    ).fetchall()
    conn.close()

    if t is None:
        return 'Ticket not found.', 404

    return render_template('ticket.html', ticket=t, notes=notes)

@app.route('/ticket/<int:ticket_id>/update', methods=['POST'])
def update_ticket(ticket_id):
    status = request.form['status']
    conn = get_db()
    conn.execute(
        'UPDATE tickets SET status = ? WHERE id = ?', (status, ticket_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('ticket', ticket_id=ticket_id))

@app.route('/ticket/<int:ticket_id>/note', methods=['POST'])
def add_note(ticket_id):
    author = request.form['author']
    content = request.form['content']
    conn = get_db()
    conn.execute(
        'INSERT INTO notes (ticket_id, author, content) VALUES (?, ?, ?)',
        (ticket_id, author, content)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('ticket', ticket_id=ticket_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
