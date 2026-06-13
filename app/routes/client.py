from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.models import Categorie, Produit, Commande, LigneCommande, Facture, Livraison, Devis, LigneDevis
from app import db

client_bp = Blueprint('client_bp', __name__)


@client_bp.route('/menu')
def menu():
    category_id = request.args.get('category_id', type=int)
    categories = Categorie.query.all()
    if category_id:
        products = Produit.query.filter_by(id_categorie=category_id).all()
        selected_cat = Categorie.query.get(category_id)
    else:
        products = Produit.query.all()
        selected_cat = None
    return render_template('client/menu.html', products=products, categories=categories, selected_cat=selected_cat)


@client_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}

    pid = str(product_id)
    cart = session['cart']
    if pid in cart:
        cart[pid] += 1
    else:
        cart[pid] = 1

    session.modified = True
    flash('Produit ajouté au panier !', 'success')
    return redirect(request.referrer or url_for('client_bp.menu'))


@client_bp.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}

    quantity = request.form.get('quantity', type=int)
    pid = str(product_id)

    if quantity is None or quantity <= 0:
        session['cart'].pop(pid, None)
        flash('Produit retiré du panier.', 'success')
    else:
        session['cart'][pid] = quantity
        flash('Quantité mise à jour.', 'success')

    session.modified = True
    return redirect(url_for('client_bp.cart'))


@client_bp.route('/cart')
def cart():
    cart_items = []
    total = 0
    if 'cart' in session:
        for pid, qty in session['cart'].items():
            product = Produit.query.get(int(pid))
            if product:
                item_total = product.prix_vente * qty
                total += item_total
                cart_items.append({
                    'product': product,
                    'quantity': qty,
                    'total': item_total
                })
    return render_template('client/cart.html', cart_items=cart_items, total=total)


@client_bp.route('/cart/remove/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        pid = str(product_id)
        if pid in session['cart']:
            del session['cart'][pid]
            session.modified = True
            flash('Produit retiré du panier.', 'success')
    return redirect(url_for('client_bp.cart'))


@client_bp.route('/cart/clear', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    flash('Panier vidé.', 'success')
    return redirect(url_for('client_bp.menu'))


@client_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Votre panier est vide.', 'danger')
        return redirect(url_for('client_bp.menu'))

    total = 0
    cart_items = []
    for pid, qty in session['cart'].items():
        product = Produit.query.get(int(pid))
        if product:
            total += product.prix_vente * qty
            cart_items.append((product, qty))

    if request.method == 'POST':
        adresse = request.form.get('adresse')
        mode_paiement = request.form.get('mode_paiement')
        type_commande = request.form.get('type_commande', 'Livraison')

        if type_commande == 'Livraison' and not adresse:
            flash('Une adresse est requise pour une livraison.', 'danger')
            return redirect(url_for('client_bp.checkout'))

        # 1. Create Commande
        new_order = Commande(id_client=current_user.id_client)
        db.session.add(new_order)
        db.session.flush()  # Get id_commande

        # 2. Create LigneCommandes
        for product, qty in cart_items:
            ligne = LigneCommande(
                id_commande=new_order.id_commande,
                id_produit=product.id_produit,
                quantite=qty,
                prix_unitaire=product.prix_vente
            )
            db.session.add(ligne)
            
            # Decrease stock
            if product.stock >= qty:
                product.stock -= qty
            else:
                product.stock = 0 # Or handle error if stock is strictly managed

        # 3. Create Facture
        facture = Facture(
            id_commande=new_order.id_commande,
            montant_total=total,
            mode_paiement=mode_paiement
        )
        db.session.add(facture)

        # 4. Create Livraison only for delivery orders
        if type_commande == 'Livraison' and adresse:
            livraison = Livraison(
                id_commande=new_order.id_commande,
                adresse=adresse
            )
            db.session.add(livraison)

        db.session.commit()
        session.pop('cart', None)
        flash('Commande passée avec succès !', 'success')
        return redirect(url_for('client_bp.history'))

    return render_template('client/checkout.html', total=total)


@client_bp.route('/history')
@login_required
def history():
    orders = Commande.query.filter_by(id_client=current_user.id_client).order_by(Commande.date_commande.desc()).all()
    return render_template('client/history.html', orders=orders)


@client_bp.route('/history/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Commande.query.filter_by(
        id_commande=order_id,
        id_client=current_user.id_client
    ).first_or_404()
    return render_template('client/order_detail.html', order=order, back_url=url_for('client_bp.history'))

@client_bp.route('/devis')
@login_required
def my_devis():
    user_devis = Devis.query.filter_by(id_client=current_user.id_client).order_by(Devis.date_devis.desc()).all()
    return render_template('client/devis.html', devis_list=user_devis)
