from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import Categorie, Produit, Commande, Client, Facture, Livraison, LigneCommande, Fournisseur, Devis, LigneDevis
from app import db
import os
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__)

ORDER_STATUS_FLOW = [
    'En attente',
    'Confirmée',
    'En préparation',
    'Prête',
    'En livraison',
    'Livrée',
    'Annulée',
]

DEVIS_STATUS_FLOW = [
    'Brouillon',
    'Envoyé',
    'Accepté',
    'Refusé',
    'Converti en Commande'
]


DELIVERY_STATUS_FLOW = [
    'En prÃ©paration',
    'En cours de livraison',
    'LivrÃ©e',
    'AnnulÃ©e',
]

DELIVERY_TO_ORDER_STATUS = {
    'En prÃ©paration': 'En prÃ©paration',
    'En cours de livraison': 'En livraison',
    'LivrÃ©e': 'LivrÃ©e',
    'AnnulÃ©e': 'AnnulÃ©e',
}


def _sync_order_from_delivery(order, delivery_status):
    order.statut = DELIVERY_TO_ORDER_STATUS.get(delivery_status, order.statut)


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Accès réservé aux administrateurs.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated_function


@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_orders = Commande.query.count()
    total_clients = Client.query.count()
    total_revenue = db.session.query(db.func.sum(Facture.montant_total)).scalar() or 0
    total_suppliers = Fournisseur.query.count()
    total_devis = Devis.query.count()
    total_deliveries = Livraison.query.count()
    recent_orders = Commande.query.order_by(Commande.date_commande.desc()).limit(5).all()

    order_breakdown = {
        'En attente': Commande.query.filter_by(statut='En attente').count(),
        'Confirmée': Commande.query.filter_by(statut='Confirmée').count(),
        'En préparation': Commande.query.filter_by(statut='En préparation').count(),
        'Prête': Commande.query.filter_by(statut='Prête').count(),
        'En livraison': Commande.query.filter_by(statut='En livraison').count(),
        'Livrée': Commande.query.filter_by(statut='Livrée').count(),
        'Annulée': Commande.query.filter_by(statut='Annulée').count(),
    }

    return render_template(
        'admin/dashboard.html',
        total_orders=total_orders,
        total_clients=total_clients,
        total_revenue=total_revenue,
        total_suppliers=total_suppliers,
        total_devis=total_devis,
        total_deliveries=total_deliveries,
        recent_orders=recent_orders,
        order_breakdown=order_breakdown,
    )

# --- CATEGORIES ---

@admin.route('/categories')
@login_required
@admin_required
def categories():
    cats = Categorie.query.all()
    return render_template('admin/categories.html', categories=cats)


@admin.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    nom = request.form.get('nom')
    next_url = request.form.get('next') or url_for('admin.categories')
    if nom:
        new_cat = Categorie(nom=nom)
        db.session.add(new_cat)
        db.session.commit()
        flash('Catégorie ajoutée !', 'success')
    return redirect(next_url)


@admin.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    category = Categorie.query.get_or_404(category_id)

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        next_url = request.form.get('next') or url_for('admin.categories')

        if not nom:
            flash('Le nom de la catégorie est obligatoire.', 'danger')
            return redirect(url_for('admin.edit_category', category_id=category_id))

        category.nom = nom
        db.session.commit()
        flash('Catégorie modifiée !', 'success')
        return redirect(next_url)

    return render_template('admin/category_edit.html', category=category)


@admin.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = Categorie.query.get_or_404(category_id)

    if category.produits:
        flash('Impossible de supprimer une catégorie qui contient encore des produits.', 'danger')
        return redirect(url_for('admin.categories'))

    db.session.delete(category)
    db.session.commit()
    flash('Catégorie supprimée !', 'success')
    return redirect(url_for('admin.categories'))

# --- PRODUCTS ---

@admin.route('/products')
@login_required
@admin_required
def products():
    prods = Produit.query.all()
    cats = Categorie.query.all()
    sups = Fournisseur.query.all()
    return render_template('admin/products.html', products=prods, categories=cats, suppliers=sups)


@admin.route('/products/add', methods=['POST'])
@login_required
@admin_required
def add_product():
    libelle = request.form.get('libelle')
    description = request.form.get('description')
    prix_vente = request.form.get('prix_vente')
    prix_achat = request.form.get('prix_achat')
    stock = request.form.get('stock')
    id_categorie = request.form.get('id_categorie')
    id_fournisseur = request.form.get('id_fournisseur')

    if not id_categorie:
        flash('Veuillez choisir une catégorie avant d’ajouter le produit.', 'danger')
        return redirect(url_for('admin.products'))

    file = request.files.get('image')
    filename = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

    new_prod = Produit(
        libelle=libelle,
        reference=request.form.get('reference'),
        marque=request.form.get('marque'),
        couleur=request.form.get('couleur'),
        description=description,
        prix_vente=float(prix_vente),
        prix_achat=float(prix_achat) if prix_achat else 0.0,
        stock=int(stock) if stock else 0,
        id_categorie=int(id_categorie),
        id_fournisseur=int(id_fournisseur) if id_fournisseur and id_fournisseur != "" else None,
        image=filename,
    )
    db.session.add(new_prod)
    db.session.commit()
    flash('Produit ajouté !', 'success')
    return redirect(url_for('admin.products'))

@admin.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    prod = Produit.query.get_or_404(product_id)
    cats = Categorie.query.all()
    sups = Fournisseur.query.all()

    if request.method == 'POST':
        prod.libelle = request.form.get('libelle')
        prod.reference = request.form.get('reference')
        prod.marque = request.form.get('marque')
        prod.couleur = request.form.get('couleur')
        prod.description = request.form.get('description')
        prod.prix_vente = float(request.form.get('prix_vente'))
        prod.prix_achat = float(request.form.get('prix_achat')) if request.form.get('prix_achat') else 0.0
        prod.stock = int(request.form.get('stock')) if request.form.get('stock') else 0
        prod.id_categorie = int(request.form.get('id_categorie'))
        
        id_fournisseur = request.form.get('id_fournisseur')
        prod.id_fournisseur = int(id_fournisseur) if id_fournisseur and id_fournisseur != "" else None

        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            prod.image = filename

        db.session.commit()
        flash('Produit mis à jour !', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_edit.html', product=prod, categories=cats, suppliers=sups)

@admin.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    prod = Produit.query.get_or_404(product_id)
    db.session.delete(prod)
    db.session.commit()
    flash('Produit supprimé !', 'success')
    return redirect(url_for('admin.products'))

# --- SUPPLIERS ---

@admin.route('/suppliers')
@login_required
@admin_required
def suppliers():
    sups = Fournisseur.query.all()
    return render_template('admin/suppliers.html', suppliers=sups)

@admin.route('/suppliers/add', methods=['POST'])
@login_required
@admin_required
def add_supplier():
    nom = request.form.get('nom')
    email = request.form.get('email')
    telephone = request.form.get('telephone')
    adresse = request.form.get('adresse')

    if nom:
        new_sup = Fournisseur(
            nom=nom, 
            email=email, 
            telephone=telephone, 
            adresse=adresse,
            ville=request.form.get('ville'),
            ice=request.form.get('ice'),
            rc=request.form.get('rc'),
            if_legal=request.form.get('if_legal'),
            banque=request.form.get('banque'),
            rib=request.form.get('rib'),
            contact_nom=request.form.get('contact_nom'),
            contact_fonction=request.form.get('contact_fonction')
        )
        db.session.add(new_sup)
        db.session.commit()
        flash('Fournisseur ajouté !', 'success')
    return redirect(url_for('admin.suppliers'))

@admin.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(supplier_id):
    sup = Fournisseur.query.get_or_404(supplier_id)
    if request.method == 'POST':
        sup.nom = request.form.get('nom')
        sup.email = request.form.get('email')
        sup.telephone = request.form.get('telephone')
        sup.adresse = request.form.get('adresse')
        sup.ville = request.form.get('ville')
        sup.ice = request.form.get('ice')
        sup.rc = request.form.get('rc')
        sup.if_legal = request.form.get('if_legal')
        sup.banque = request.form.get('banque')
        sup.rib = request.form.get('rib')
        sup.contact_nom = request.form.get('contact_nom')
        sup.contact_fonction = request.form.get('contact_fonction')
        db.session.commit()
        flash('Fournisseur mis à jour !', 'success')
        return redirect(url_for('admin.suppliers'))
    return render_template('admin/supplier_edit.html', supplier=sup)

@admin.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@login_required
@admin_required
def delete_supplier(supplier_id):
    sup = Fournisseur.query.get_or_404(supplier_id)
    if sup.produits:
        flash('Impossible de supprimer un fournisseur lié à des produits.', 'danger')
        return redirect(url_for('admin.suppliers'))
    db.session.delete(sup)
    db.session.commit()
    flash('Fournisseur supprimé !', 'success')
    return redirect(url_for('admin.suppliers'))

# --- QUOTES (DEVIS) ---

@admin.route('/devis')
@login_required
@admin_required
def list_devis():
    all_devis = Devis.query.order_by(Devis.date_devis.desc()).all()
    return render_template('admin/devis.html', all_devis=all_devis, status_options=DEVIS_STATUS_FLOW)

@admin.route('/devis/<int:devis_id>')
@login_required
@admin_required
def devis_detail(devis_id):
    devis = Devis.query.get_or_404(devis_id)
    return render_template('admin/devis_detail.html', devis=devis)

@admin.route('/devis/update_status/<int:devis_id>', methods=['POST'])
@login_required
@admin_required
def update_devis_status(devis_id):
    devis = Devis.query.get_or_404(devis_id)
    new_status = request.form.get('statut')
    validite = request.form.get('validite')
    
    if validite:
        devis.validite = int(validite)
        
    if new_status in DEVIS_STATUS_FLOW:
        devis.statut = new_status
        db.session.commit()
        flash('Devis mis à jour !', 'success')
    return redirect(url_for('admin.list_devis'))

@admin.route('/devis/delete/<int:devis_id>', methods=['POST'])
@login_required
@admin_required
def delete_devis(devis_id):
    devis = Devis.query.get_or_404(devis_id)
    db.session.delete(devis)
    db.session.commit()
    flash('Devis supprimé !', 'success')
    return redirect(url_for('admin.list_devis'))

# --- DELIVERIES ---

@admin.route('/deliveries')
@login_required
@admin_required
def deliveries():
    all_deliveries = Livraison.query.order_by(Livraison.id_livraison.desc()).all()
    available_orders = Commande.query.filter(~Commande.livraison.has()).order_by(Commande.date_commande.desc()).all()
    delivery_stats = {
        'total': len(all_deliveries),
        'En préparation': sum(1 for delivery in all_deliveries if delivery.etat_livraison == 'En préparation'),
        'En cours de livraison': sum(1 for delivery in all_deliveries if delivery.etat_livraison == 'En cours de livraison'),
        'Livrée': sum(1 for delivery in all_deliveries if delivery.etat_livraison == 'Livrée'),
        'Annulée': sum(1 for delivery in all_deliveries if delivery.etat_livraison == 'Annulée'),
    }
    return render_template(
        'admin/deliveries.html',
        deliveries=all_deliveries,
        available_orders=available_orders,
        status_options=DELIVERY_STATUS_FLOW,
        delivery_stats=delivery_stats,
    )


@admin.route('/deliveries/add', methods=['POST'])
@login_required
@admin_required
def add_delivery():
    order_id = request.form.get('order_id', type=int)
    adresse = request.form.get('adresse', '').strip()
    etat_livraison = request.form.get('etat_livraison', 'En prÃ©paration')

    if not order_id:
        flash('Veuillez choisir une commande.', 'danger')
        return redirect(url_for('admin.deliveries'))

    order = Commande.query.get_or_404(order_id)

    if order.livraison:
        flash('Cette commande dispose dÃ©jÃ  dâ€™une livraison. Vous pouvez la modifier.', 'warning')
        return redirect(url_for('admin.edit_delivery', delivery_id=order.livraison.id_livraison))

    if not adresse:
        flash('Lâ€™adresse de livraison est obligatoire.', 'danger')
        return redirect(url_for('admin.deliveries'))

    if etat_livraison not in DELIVERY_STATUS_FLOW:
        etat_livraison = 'En prÃ©paration'

    new_delivery = Livraison(
        id_commande=order.id_commande,
        adresse=adresse,
        etat_livraison=etat_livraison,
    )
    _sync_order_from_delivery(order, etat_livraison)
    db.session.add(new_delivery)
    db.session.commit()
    flash('Livraison ajoutÃ©e avec succÃ¨s !', 'success')
    return redirect(url_for('admin.deliveries'))


@admin.route('/deliveries/edit/<int:delivery_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_delivery(delivery_id):
    delivery = Livraison.query.get_or_404(delivery_id)

    if request.method == 'POST':
        adresse = request.form.get('adresse', '').strip()
        etat_livraison = request.form.get('etat_livraison', 'En prÃ©paration')

        if not adresse:
            flash('Lâ€™adresse de livraison est obligatoire.', 'danger')
            return redirect(url_for('admin.edit_delivery', delivery_id=delivery_id))

        if etat_livraison not in DELIVERY_STATUS_FLOW:
            etat_livraison = 'En prÃ©paration'

        delivery.adresse = adresse
        delivery.etat_livraison = etat_livraison
        _sync_order_from_delivery(delivery.commande, etat_livraison)
        db.session.commit()
        flash('Livraison mise Ã  jour !', 'success')
        return redirect(url_for('admin.deliveries'))

    return render_template('admin/delivery_edit.html', delivery=delivery, status_options=DELIVERY_STATUS_FLOW)


@admin.route('/print/delivery/<int:delivery_id>')
@login_required
@admin_required
def print_delivery(delivery_id):
    delivery = Livraison.query.get_or_404(delivery_id)
    return render_template('admin/print_delivery.html', delivery=delivery)

# --- PRINTING ---

@admin.route('/print/invoice/<int:order_id>')
@login_required
@admin_required
def print_invoice(order_id):
    order = Commande.query.get_or_404(order_id)
    return render_template('admin/print_invoice.html', order=order)

@admin.route('/print/devis/<int:devis_id>')
@login_required
@admin_required
def print_devis(devis_id):
    devis = Devis.query.get_or_404(devis_id)
    return render_template('admin/print_devis.html', devis=devis)

@admin.route('/print/products')
@login_required
@admin_required
def print_products():
    from datetime import datetime
    prods = Produit.query.all()
    return render_template('admin/print_products.html', products=prods, now=datetime.now())

@admin.route('/print/supplier/<int:supplier_id>')
@login_required
@admin_required
def print_supplier(supplier_id):
    sup = Fournisseur.query.get_or_404(supplier_id)
    return render_template('admin/print_supplier_sheet.html', supplier=sup)

@admin.route('/orders')
@login_required
@admin_required
def orders():
    all_orders = Commande.query.order_by(Commande.date_commande.desc()).all()
    return render_template('admin/orders.html', orders=all_orders, status_options=ORDER_STATUS_FLOW)


@admin.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    order = Commande.query.get_or_404(order_id)
    return render_template('client/order_detail.html', order=order, back_url=url_for('admin.orders'))


@admin.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(order_id):
    order = Commande.query.get_or_404(order_id)

    if request.method == 'POST':
        new_status = request.form.get('statut')
        mode_paiement = request.form.get('mode_paiement', '').strip()
        adresse = request.form.get('adresse', '').strip()

        if new_status not in ORDER_STATUS_FLOW:
            flash('Statut invalide.', 'danger')
            return redirect(url_for('admin.edit_order', order_id=order_id))

        order.statut = new_status

        if mode_paiement:
            if not order.facture:
                montant_total = sum((ligne.prix_unitaire or 0) * ligne.quantite for ligne in order.lignes)
                order.facture = Facture(
                    id_commande=order.id_commande,
                    montant_total=montant_total,
                    mode_paiement=mode_paiement,
                )
            else:
                order.facture.mode_paiement = mode_paiement
            
            date_reglement = request.form.get('date_reglement')
            if date_reglement:
                from datetime import datetime
                order.facture.date_reglement = datetime.strptime(date_reglement, '%Y-%m-%d')

        if adresse:
            if not order.livraison:
                order.livraison = Livraison(
                    id_commande=order.id_commande,
                    adresse=adresse,
                )
            else:
                order.livraison.adresse = adresse

        if order.livraison:
            delivery_state_map = {
                'En attente': 'En préparation',
                'Confirmée': 'En préparation',
                'En préparation': 'En préparation',
                'Prête': 'Prête',
                'En livraison': 'En cours de livraison',
                'Livrée': 'Livrée',
                'Annulée': 'Annulée',
            }
            order.livraison.etat_livraison = delivery_state_map.get(new_status, order.livraison.etat_livraison)

        db.session.commit()
        flash('Commande mise à jour avec succès !', 'success')
        return redirect(url_for('admin.orders'))

    return render_template('admin/order_edit.html', order=order, status_options=ORDER_STATUS_FLOW)


@admin.route('/orders/update/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Commande.query.get_or_404(order_id)
    new_status = request.form.get('statut')

    if new_status not in ORDER_STATUS_FLOW:
        flash('Statut invalide.', 'danger')
        return redirect(url_for('admin.orders'))

    order.statut = new_status

    if order.livraison:
        delivery_state_map = {
            'En attente': 'En préparation',
            'Confirmée': 'En préparation',
            'En préparation': 'En préparation',
            'Prête': 'Prête',
            'En livraison': 'En cours de livraison',
            'Livrée': 'Livrée',
            'Annulée': 'Annulée',
        }
        order.livraison.etat_livraison = delivery_state_map.get(new_status, order.livraison.etat_livraison)

    db.session.commit()
    flash('Statut de la commande mis à jour !', 'success')
    return redirect(url_for('admin.orders'))


@admin.route('/orders/delete/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def delete_order(order_id):
    order = Commande.query.get_or_404(order_id)

    LigneCommande.query.filter_by(id_commande=order.id_commande).delete(synchronize_session=False)
    Facture.query.filter_by(id_commande=order.id_commande).delete(synchronize_session=False)
    Livraison.query.filter_by(id_commande=order.id_commande).delete(synchronize_session=False)
    db.session.delete(order)
    db.session.commit()

    flash('Commande supprimée avec succès !', 'success')
    return redirect(url_for('admin.orders'))
