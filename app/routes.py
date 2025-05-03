from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Cliente, Cita
from app import db
from datetime import datetime, date, timedelta
import calendar

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    citas = Cita.query.filter(
        db.func.date(Cita.fecha) == date.today()
    ).all()
    clientes = Cliente.query.all()
    return render_template('citas.html', citas=citas, clientes=clientes)

@bp.route('/calendario')
@bp.route('/calendario/<int:year>/<int:month>')
def calendario(year=None, month=None):
    hoy = date.today()
    
    # Si no se especifica año y mes, usar el actual
    if year is None or month is None:
        year = hoy.year
        month = hoy.month
    
    # Asegurarse que el mes esté entre 1 y 12
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    primer_dia_mes = date(year, month, 1)
    ultimo_dia_mes = date(year, month, calendar.monthrange(year, month)[1])
    
    # Obtener todas las citas del mes
    citas_mes = Cita.query.filter(
        db.func.date(Cita.fecha) >= primer_dia_mes,
        db.func.date(Cita.fecha) <= ultimo_dia_mes
    ).all()
    
    # Crear el calendario
    cal = calendar.monthcalendar(year, month)
    calendario_mes = []
    
    for semana in cal:
        semana_cal = []
        for dia in semana:
            if dia == 0:
                semana_cal.append({'fecha': None, 'citas': []})
            else:
                fecha_dia = date(year, month, dia)
                citas_dia = [c for c in citas_mes if c.fecha.date() == fecha_dia]
                semana_cal.append({'fecha': fecha_dia, 'citas': citas_dia})
        calendario_mes.append(semana_cal)
    
    # Obtener citas de hoy
    citas_hoy = Cita.query.filter(
        db.func.date(Cita.fecha) == hoy
    ).all()
    
    # Calcular mes anterior y siguiente
    mes_anterior = month - 1 if month > 1 else 12
    año_anterior = year if month > 1 else year - 1
    mes_siguiente = month + 1 if month < 12 else 1
    año_siguiente = year if month < 12 else year + 1
    
    return render_template('calendario.html', 
                         calendario=calendario_mes,
                         citas_hoy=citas_hoy,
                         hoy=hoy,
                         mes_actual=month,
                         año_actual=year,
                         mes_anterior=mes_anterior,
                         año_anterior=año_anterior,
                         mes_siguiente=mes_siguiente,
                         año_siguiente=año_siguiente)

@bp.route('/clientes')
def clientes():
    busqueda = request.args.get('busqueda', '').strip()
    if busqueda:
        # Dividir la búsqueda en palabras
        palabras = busqueda.split()
        
        # Construir la consulta base
        query = Cliente.query
        
        # Para cada palabra, buscar en nombre y apellido
        for palabra in palabras:
            query = query.filter(
                db.or_(
                    Cliente.nombre.ilike(f'%{palabra}%'),
                    Cliente.apellido.ilike(f'%{palabra}%')
                )
            )
        
        clientes = query.all()
    else:
        clientes = Cliente.query.all()
    
    return render_template('clientes.html', clientes=clientes, busqueda=busqueda)

@bp.route('/cliente/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form.get('telefono')  # Teléfono es opcional
        
        cliente = Cliente(nombre=nombre, apellido=apellido, telefono=telefono)
        db.session.add(cliente)
        db.session.commit()
        
        flash('Cliente agregado exitosamente', 'success')
        return redirect(url_for('main.clientes'))
    
    return render_template('nuevo_cliente.html')

@bp.route('/cita/nueva', methods=['POST'])
def nueva_cita():
    cliente_id = request.form['cliente_id']
    fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%dT%H:%M')
    descripcion = request.form['descripcion']
    
    cita = Cita(
        cliente_id=cliente_id,
        fecha=fecha,
        descripcion=descripcion,
        estado='pendiente'
    )
    db.session.add(cita)
    db.session.commit()
    
    flash('Cita agendada exitosamente', 'success')
    return redirect(url_for('main.index'))

@bp.route('/cliente/<int:id>')
def cliente_detalle(id):
    cliente = Cliente.query.get_or_404(id)
    citas = Cita.query.filter_by(cliente_id=id).order_by(Cita.fecha).all()
    return render_template('cliente_detalle.html', cliente=cliente, citas=citas)

@bp.route('/cita/<int:id>/completar', methods=['POST'])
def completar_cita(id):
    cita = Cita.query.get_or_404(id)
    cita.estado = 'completada'
    db.session.commit()
    flash('Cita marcada como completada', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/cita/<int:id>/cancelar', methods=['POST'])
def cancelar_cita(id):
    cita = Cita.query.get_or_404(id)
    cita.estado = 'cancelada'
    db.session.commit()
    flash('Cita marcada como cancelada', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/cliente/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.apellido = request.form['apellido']
        cliente.telefono = request.form.get('telefono')
        
        db.session.commit()
        flash('Cliente actualizado exitosamente', 'success')
        return redirect(url_for('main.cliente_detalle', id=cliente.id))
    
    return render_template('editar_cliente.html', cliente=cliente)

@bp.route('/cliente/<int:id>/borrar', methods=['POST'])
def borrar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    # Verificar si el cliente tiene citas pendientes
    citas_pendientes = Cita.query.filter_by(cliente_id=id, estado='pendiente').count()
    if citas_pendientes > 0:
        flash('No se puede borrar el cliente porque tiene citas pendientes', 'danger')
        return redirect(url_for('main.cliente_detalle', id=id))
    
    # Borrar todas las citas del cliente
    Cita.query.filter_by(cliente_id=id).delete()
    
    # Borrar el cliente
    db.session.delete(cliente)
    db.session.commit()
    
    flash('Cliente borrado exitosamente', 'success')
    return redirect(url_for('main.clientes')) 