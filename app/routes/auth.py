from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Client
from app import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        client = Client.query.filter_by(username=username).first()
        if client and client.check_password(password):
            login_user(client)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        password = request.form.get('password')
        
        user_exists = Client.query.filter_by(username=username).first()
        if user_exists:
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'danger')
            return redirect(url_for('auth.register'))
        
        new_client = Client(username=username, nom=nom, prenom=prenom, email=email, telephone=telephone)
        new_client.set_password(password)
        
        db.session.add(new_client)
        db.session.commit()
        flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
