from app import create_app, db
from app.models import Client, Categorie, Produit

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Check if schema is out of sync
        try:
            db.create_all()
            admin = Client.query.filter_by(username='admin').first()
        except Exception as e:
            print("Schema out of sync, recreating database...")
            db.drop_all()
            db.create_all()
            admin = None
            
        # Seed default admin
        if not admin:
            admin = Client(username='admin', nom='Admin', prenom='System', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin / admin123")
    app.run(debug=True)
