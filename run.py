from app import app, db
import os

if __name__ == '__main__':
    # Eliminar la base de datos si existe
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'peluqueria.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Crear la base de datos y las tablas
    with app.app_context():
        db.create_all()
    
    # Iniciar la aplicación
    app.run(debug=True) 