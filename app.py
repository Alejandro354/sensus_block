from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import sqlite3
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta_sensus_block_mela'

# BANCO DE FRASES
FRASES = {
    'feliz': [
        "¡Esa es la actitud! Sigue contagiando esa buena energía hoy.",
        "La felicidad es una dirección, no un lugar. ¡Sigue disfrutando el camino!",
        "Aprovecha este impulso para crear algo increíble hoy."
    ],
    'triste': [
        "Está bien no estar bien a veces. Respira, tómate un tiempo y ve a tu ritmo.",
        "Las nubes siempre pasan, el cielo siempre permanece. Mañana será otro día.",
        "Sé amable contigo mismo hoy. Un paso a la vez."
    ],
    'curioso': [
        "La curiosidad es el motor de las grandes ideas. ¡A explorar!",
        "Nunca dejes de hacer preguntas; ahí es donde vive la innovación.",
        "Hoy es un gran día para aprender algo completamente nuevo."
    ],
    'a_tope': [
        "¡Con toda la energía! Hoy es un buen día para romperla.",
        "Aprovecha esa chispa al máximo. ¡Nada te detiene hoy!",
        "Esa motivación es oro puro. ¡A darle con todo!"
    ],
    'paz': [
        "La tranquilidad mental es el verdadero éxito. Disfruta tu calma.",
        "En el silencio y la calma se aclaran las mejores ideas.",
        "Mantén ese equilibrio interno a lo largo del día."
    ],
    'estresado': [
        "Inhala profundo, exhala despacio. Una tarea a la vez, sin afán.",
        "No puedes controlar todo lo que pasa, pero sí cómo reaccionas a ello.",
        "Haz una pausa de 5 minutos. Tu mente te lo agradecerá."
    ],
    'agotado': [
        "Descansar también es parte del progreso. No te exijas más de la cuenta.",
        "Recargar baterías no es perder tiempo, es preparar la siguiente victoria.",
        "Bájale dos rayitas al ritmo y tómate una bebida caliente."
    ],
    'inspirado': [
        "¡Escribe esa idea ya antes de que vuele!",
        "La inspiración existe, pero tiene que encontrarte trabajando.",
        "Tu creatividad está en su punto máximo. ¡Aprovéchala!"
    ]
}

def init_db():
    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    
    # Tabla Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Tabla Notas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            fecha TEXT,
            categoria TEXT DEFAULT 'Personal',
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # Tabla Grupos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            creador_id INTEGER NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')

    # Tabla Miembros de Grupo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miembros_grupo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grupo_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (grupo_id) REFERENCES grupos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # Tabla Mensajes (sirve para chat 1 a 1 y para grupos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emisor_id INTEGER NOT NULL,
            receptor_id INTEGER,
            grupo_id INTEGER,
            contenido TEXT NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (emisor_id) REFERENCES usuarios (id),
            FOREIGN KEY (receptor_id) REFERENCES usuarios (id),
            FOREIGN KEY (grupo_id) REFERENCES grupos (id)
        )
    ''')
    
    # Migraciones por si ya existía la DB
    try:
        cursor.execute('ALTER TABLE notas ADD COLUMN fecha TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE notas ADD COLUMN categoria TEXT DEFAULT "Personal"')
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

# GARANTIZA QUE LAS TABLAS SE CREAN ANTES DE CUALQUIER PETICIÓN
with app.app_context():
    init_db()

# RUTA RAÍZ PRINCIPAL OBLIGATORIA
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# --- DE AQUÍ PARA ABAJO SIGUEN TUS RUTAS NORMALES (/login, /dashboard, etc.) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        nombre = request.form.get('nombre')
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        conn = sqlite3.connect('base_de_datos.db')
        cursor = conn.cursor()
        
        if action == 'register':
            try:
                cursor.execute('INSERT INTO usuarios (nombre, usuario, password) VALUES (?, ?, ?)',
                               (nombre, usuario, password))
                conn.commit()
                cursor.execute('SELECT id, nombre FROM usuarios WHERE usuario = ?', (usuario,))
                user = cursor.fetchone()
                session['usuario_id'] = user[0]
                session['nombre'] = user[1]
                conn.close()
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                error = "El usuario ya existe. Intenta con otro."
                
        elif action == 'login':
            cursor.execute('SELECT id, nombre FROM usuarios WHERE usuario = ? AND password = ?', (usuario, password))
            user = cursor.fetchone()
            conn.close()
            if user:
                session['usuario_id'] = user[0]
                session['nombre'] = user[1]
                return redirect(url_for('dashboard'))
            else:
                error = "Usuario o contraseña incorrectos."
                
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, titulo, contenido, fecha, categoria FROM notas WHERE usuario_id = ? ORDER BY id DESC', (session['usuario_id'],))
    notas = cursor.fetchall()
    
    # Obtener usuarios para la sección de chat
    cursor.execute('SELECT id, nombre, usuario FROM usuarios WHERE id != ?', (session['usuario_id'],))
    otros_usuarios = cursor.fetchall()

    conn.close()
    
    return render_template('dashboard.html', nombre=session['nombre'], usuario_id=session['usuario_id'], notas=notas, otros_usuarios=otros_usuarios)

# ----------------- NOTAS -----------------

@app.route('/guardar_nota', methods=['POST'])
def guardar_nota():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    titulo = request.form.get('titulo')
    contenido = request.form.get('contenido')
    categoria = request.form.get('categoria', 'Personal')
    fecha_actual = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    
    if titulo and contenido:
        conn = sqlite3.connect('base_de_datos.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO notas (usuario_id, titulo, contenido, fecha, categoria) VALUES (?, ?, ?, ?, ?)',
                       (session['usuario_id'], titulo, contenido, fecha_actual, categoria))
        conn.commit()
        conn.close()
        
    return redirect(url_for('dashboard'))

@app.route('/editar_nota/<int:nota_id>', methods=['POST'])
def editar_nota(nota_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    titulo = request.form.get('titulo')
    contenido = request.form.get('contenido')
    categoria = request.form.get('categoria', 'Personal')
    fecha_actual = datetime.now().strftime("%d/%m/%Y %I:%M %p") + " (editado)"
    
    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE notas SET titulo = ?, contenido = ?, categoria = ?, fecha = ? WHERE id = ? AND usuario_id = ?',
                   (titulo, contenido, categoria, fecha_actual, nota_id, session['usuario_id']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/eliminar_nota/<int:nota_id>', methods=['POST'])
def eliminar_nota(nota_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notas WHERE id = ? AND usuario_id = ?', (nota_id, session['usuario_id']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/exportar_txt')
def exportar_txt():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT titulo, categoria, fecha, contenido FROM notas WHERE usuario_id = ? ORDER BY id DESC', (session['usuario_id'],))
    notas = cursor.fetchall()
    conn.close()

    lineas = [f"=== MIS NOTAS DE SENSUS_BLOCK - {session['nombre']} ===\n\n"]
    for nota in notas:
        lineas.append(f"📌 TÍTULO: {nota[0]}\n")
        lineas.append(f"🏷️ CATEGORÍA: {nota[1] or 'Personal'} | 📅 FECHA: {nota[2] or 'Sin fecha'}\n")
        lineas.append(f"----------------------------------------\n")
        lineas.append(f"{nota[3]}\n\n")
        lineas.append(f"========================================\n\n")

    contenido_txt = "".join(lineas)
    return Response(
        contenido_txt,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=mis_notas_sensus.txt"}
    )

@app.route('/obtener_frase/<estado>')
def obtener_frase(estado):
    lista_frases = FRASES.get(estado, ["¡Sigue adelante y rompiéndola hoy!"])
    
    # Obtener última frase usada en la sesión para no repetir la misma
    ultima_frase = session.get('ultima_frase')
    
    # Filtrar para evitar la misma frase consecutiva
    opciones = [f for f in lista_frases if f != ultima_frase]
    
    if not opciones:
        opciones = lista_frases
        
    frase_elegida = random.choice(opciones)
    session['ultima_frase'] = frase_elegida # Guardar en sesión
    
    return jsonify({'frase': frase_elegida})
# ----------------- RUTAS DE CHAT -----------------

@app.route('/api/crear_grupo', methods=['POST'])
def crear_grupo():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    nombre_grupo = data.get('nombre')
    miembros = data.get('miembros', []) # Lista de IDs de usuarios
    
    if not nombre_grupo or not miembros:
        return jsonify({'error': 'Nombre y miembros son requeridos'}), 400

    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().strftime("%d/%m %I:%M %p")
    cursor.execute('INSERT INTO grupos (nombre, creador_id, fecha) VALUES (?, ?, ?)',
                   (nombre_grupo, session['usuario_id'], fecha_actual))
    grupo_id = cursor.lastrowid
    
    # Agregar al creador al grupo
    cursor.execute('INSERT INTO miembros_grupo (grupo_id, usuario_id) VALUES (?, ?)', (grupo_id, session['usuario_id']))
    
    # Agregar miembros seleccionados
    for m_id in miembros:
        cursor.execute('INSERT INTO miembros_grupo (grupo_id, usuario_id) VALUES (?, ?)', (grupo_id, int(m_id)))
        
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok', 'grupo_id': grupo_id, 'nombre': nombre_grupo})

@app.route('/api/obtener_contactos')
def obtener_contactos():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    
    # Lista de usuarios
    cursor.execute('SELECT id, nombre, usuario FROM usuarios WHERE id != ?', (session['usuario_id'],))
    usuarios = [{'id': u[0], 'nombre': u[1], 'usuario': u[2]} for u in cursor.fetchall()]
    
    # Lista de grupos
    cursor.execute('''
        SELECT g.id, g.nombre 
        FROM grupos g 
        JOIN miembros_grupo mg ON g.id = mg.grupo_id 
        WHERE mg.usuario_id = ?
    ''', (session['usuario_id'],))
    grupos = [{'id': g[0], 'nombre': g[1]} for g in cursor.fetchall()]
    
    conn.close()
    return jsonify({'usuarios': usuarios, 'grupos': grupos})

@app.route('/api/mensajes/<tipo>/<int:target_id>')
def obtener_mensajes(tipo, target_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    conn = sqlite3.connect('base_de_datos.db')
    cursor = conn.cursor()
    
    if tipo == 'usuario':
        # Mensajes entre 2 personas
        cursor.execute('''
            SELECT m.id, m.emisor_id, u.nombre, m.contenido, m.fecha 
            FROM mensajes m
            JOIN usuarios u ON m.emisor_id = u.id
            WHERE (m.emisor_id = ? AND m.receptor_id = ?) 
               OR (m.emisor_id = ? AND m.receptor_id = ?)
            ORDER BY m.id ASC
        ''', (session['usuario_id'], target_id, target_id, session['usuario_id']))
    else:
        # Mensajes de un grupo
        cursor.execute('''
            SELECT m.id, m.emisor_id, u.nombre, m.contenido, m.fecha 
            FROM mensajes m
            JOIN usuarios u ON m.emisor_id = u.id
            WHERE m.grupo_id = ?
            ORDER BY m.id ASC
        ''', (target_id,))
        
    raw_mensajes = cursor.fetchall()
    conn.close()
    
    mensajes = []
    for m in raw_mensajes:
        mensajes.append({
            'id': m[0],
            'emisor_id': m[1],
            'emisor_nombre': m[2],
            'contenido': m[3],
            'fecha': m[4],
            'es_mío': m[1] == session['usuario_id']
        })
        
    return jsonify({'mensajes': mensajes})

@app.route('/api/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    data = request.get_json() or {}
    tipo = data.get('tipo') # 'usuario' o 'grupo'
    target_id = data.get('target_id')
    contenido = data.get('contenido', '').strip()
    fecha_actual = datetime.now().strftime("%I:%M %p")
    
    if not contenido or not target_id:
        return jsonify({'error': 'Mensaje vacío o destinatario inválido'}), 400
        
    conn = None
    try:
        conn = sqlite3.connect('base_de_datos.db', timeout=10) # Timeout evita bloqueos repentinos
        cursor = conn.cursor()
        
        if tipo == 'usuario':
            cursor.execute('''
                INSERT INTO mensajes (emisor_id, receptor_id, contenido, fecha) 
                VALUES (?, ?, ?, ?)
            ''', (session['usuario_id'], target_id, contenido, fecha_actual))
        else:
            cursor.execute('''
                INSERT INTO mensajes (emisor_id, grupo_id, contenido, fecha) 
                VALUES (?, ?, ?, ?)
            ''', (session['usuario_id'], target_id, contenido, fecha_actual))
            
        conn.commit()
        
        # Devolvemos tanto 'status' como 'success' para que cualquier JS lo reconozca
        return jsonify({
            'status': 'ok',
            'success': True,
            'mensaje': {
                'emisor_id': session['usuario_id'],
                'contenido': contenido,
                'fecha': fecha_actual
            }
        })
    except Exception as e:
        print("Error guardando mensaje:", e)
        return jsonify({'error': 'Error interno en el servidor'}), 500
    finally:
        if conn:
            conn.close() # GARANTIZA QUE NUNCA SE QUEDE ABIERTA LA CONEXIÓN

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)