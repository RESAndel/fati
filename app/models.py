from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(int(user_id))

class Client(db.Model, UserMixin):
    id_client = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    commandes = db.relationship('Commande', backref='client', lazy=True)
    devis = db.relationship('Devis', backref='client', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id_client)

class Fournisseur(db.Model):
    id_fournisseur = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.String(200))
    ville = db.Column(db.String(100))
    ice = db.Column(db.String(50))
    rc = db.Column(db.String(50))
    if_legal = db.Column(db.String(50))
    banque = db.Column(db.String(100))
    rib = db.Column(db.String(100))
    contact_nom = db.Column(db.String(100))
    contact_fonction = db.Column(db.String(100))
    
    produits = db.relationship('Produit', backref='fournisseur', lazy=True)

class Categorie(db.Model):
    id_categorie = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    produits = db.relationship('Produit', backref='categorie', lazy=True)

class Produit(db.Model):
    id_produit = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100), nullable=False)
    reference = db.Column(db.String(100))
    marque = db.Column(db.String(100))
    couleur = db.Column(db.String(50))
    description = db.Column(db.Text)
    prix_achat = db.Column(db.Float, default=0.0)
    prix_vente = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(100))
    id_categorie = db.Column(db.Integer, db.ForeignKey('categorie.id_categorie'), nullable=False)
    id_fournisseur = db.Column(db.Integer, db.ForeignKey('fournisseur.id_fournisseur'), nullable=True)
    
    lignes_commande = db.relationship('LigneCommande', backref='produit', lazy=True)
    lignes_devis = db.relationship('LigneDevis', backref='produit', lazy=True)

class Devis(db.Model):
    id_devis = db.Column(db.Integer, primary_key=True)
    date_devis = db.Column(db.DateTime, default=datetime.utcnow)
    validite = db.Column(db.Integer, default=30) # in days
    statut = db.Column(db.String(20), default='Brouillon') # Brouillon, Envoyé, Accepté, Refusé
    id_client = db.Column(db.Integer, db.ForeignKey('client.id_client'), nullable=False)
    montant_total = db.Column(db.Float, default=0.0)
    
    lignes = db.relationship('LigneDevis', backref='devis', lazy=True, cascade="all, delete-orphan")

class LigneDevis(db.Model):
    id_ligne_devis = db.Column(db.Integer, primary_key=True)
    id_devis = db.Column(db.Integer, db.ForeignKey('devis.id_devis'), nullable=False)
    id_produit = db.Column(db.Integer, db.ForeignKey('produit.id_produit'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)

class Commande(db.Model):
    id_commande = db.Column(db.Integer, primary_key=True)
    date_commande = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='En attente') # En attente, Validée, Livrée, Annulée
    id_client = db.Column(db.Integer, db.ForeignKey('client.id_client'), nullable=False)
    
    lignes = db.relationship('LigneCommande', backref='commande', lazy=True, cascade="all, delete-orphan")
    facture = db.relationship('Facture', backref='commande', uselist=False)
    livraison = db.relationship('Livraison', backref='commande', uselist=False)

class LigneCommande(db.Model):
    id_ligne = db.Column(db.Integer, primary_key=True)
    id_commande = db.Column(db.Integer, db.ForeignKey('commande.id_commande'), nullable=False)
    id_produit = db.Column(db.Integer, db.ForeignKey('produit.id_produit'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)

class Facture(db.Model):
    id_facture = db.Column(db.Integer, primary_key=True)
    date_facture = db.Column(db.DateTime, default=datetime.utcnow)
    date_reglement = db.Column(db.DateTime)
    montant_total = db.Column(db.Float, nullable=False)
    mode_paiement = db.Column(db.String(50))
    id_commande = db.Column(db.Integer, db.ForeignKey('commande.id_commande'), nullable=False)

class Livraison(db.Model):
    id_livraison = db.Column(db.Integer, primary_key=True)
    adresse = db.Column(db.String(200), nullable=False)
    etat_livraison = db.Column(db.String(50), default='En préparation')
    id_commande = db.Column(db.Integer, db.ForeignKey('commande.id_commande'), nullable=False)
