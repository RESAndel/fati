from flask import Blueprint, render_template
from app.models import Produit, Categorie

main = Blueprint('main', __name__)

@main.route('/')
def index():
    categories = Categorie.query.all()
    featured_products = Produit.query.limit(6).all()
    return render_template('index.html', categories=categories, featured_products=featured_products)
