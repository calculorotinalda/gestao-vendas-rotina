from flask import render_template, request, redirect, url_for, flash, session
from app import app

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Temporary login without database
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 1
            session['username'] = username
            session['user_role'] = 'admin'
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas. Use admin/admin123', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    # Mock dashboard data for now
    stats = {
        'monthly_sales': 0,
        'total_sales': 0,
        'monthly_purchases': 0,
        'total_purchases': 0,
        'profit': 0,
        'low_stock_alerts': 0,
        'recent_sales': [],
        'restock_products': []
    }
    
    return render_template('index.html', stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# Database connection test route
@app.route('/test-db')
def test_db():
    try:
        from app import db, init_database
        from models import User
        
        # Try to initialize database
        init_database()
        
        # Test query
        users = User.query.all()
        return f"Database connection successful! Found {len(users)} users."
    except Exception as e:
        return f"Database connection failed: {str(e)}"

@app.context_processor
def inject_user():
    return dict(
        current_user_id=session.get('user_id'),
        current_username=session.get('username'),
        current_user_role=session.get('user_role')
    )

@app.template_filter('currency')
def currency_filter(amount):
    if amount is None:
        amount = 0
    return f"{amount:,.2f} €"

# Register the filter
app.jinja_env.filters['currency'] = currency_filter

def format_currency(amount):
    if amount is None:
        amount = 0
    return f"{amount:,.2f} €"

app.jinja_env.globals.update(format_currency=format_currency)