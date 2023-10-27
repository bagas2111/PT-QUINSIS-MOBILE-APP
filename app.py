from flask import Flask, request, jsonify
from flask_restful import Resource
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime
import hashlib
import base64
import pymysql.cursors
import base64
import hashlib

app = Flask(__name__)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','docx'}


conn = cursor = None

# Fungsi koneksi database
def openDb():
    global conn, cursor
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",  # Provide the password if applicable
        database="monitoring"
    )
    cursor = conn.cursor()

def closeDb():
    global conn, cursor
    if cursor:
        cursor.close()
    if conn:
        conn.close()

@app.route('/')
def index():
    return 'haloooo'

# Fungsi view index() untuk menampilkan data dari database sebagai API
@app.route('/bbb', methods=['GET'])
def api_bbb():   
    openDb()
    container = []
    sql = "SELECT * FROM barang"
    cursor.execute(sql)
    results = cursor.fetchall()

    for data in results:
        data = list(data)
        data[4] = base64.b64encode(data[4]).decode('utf-8')
        container.append(data)

    closeDb()
    return jsonify(container)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/login', methods=['POST'])
def login():
    openDb()
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username is None or password is None:
        closeDb()
        return jsonify({'error': 'Missing username or password'})

    hashed_password = hashlib.sha512(password.encode()).hexdigest()
    
    query = f"SELECT * FROM pegawai WHERE username='{username}' AND password='{hashed_password}'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    closeDb()
    
    if result:
        response = {
            'msg': 'DATA ADA',
            'level': result[2],  # Assuming 'level' is in the third column of the table
            'username': result[3],
            'id_pegawai': result[0],
            'nama': result[1],
        }
    else:
        response = {
            'msg': 'DATA TIDAK ADA'
        }
    
    return jsonify(response)


@app.route('/projects', methods=['GET'])
def get_projects():
    try:
        id_pegawai = request.args.get('id_pegawai')

        if id_pegawai is None:
            return jsonify({'error': 'Missing id_pegawai parameter'})

        id_pegawai = int(id_pegawai)

        openDb()

        id_project_query = """
            SELECT struktur.id_project, pegawai.nama
            FROM struktur
            INNER JOIN pegawai ON struktur.id_pegawai = pegawai.id_pegawai
            WHERE struktur.id_pegawai = %s
        """

        cursor.execute(id_project_query, (id_pegawai,))
        id_project_results = cursor.fetchall()

        projects = []

        for id_project_result in id_project_results:
            id_project = id_project_result[0]
            nama = id_project_result[1]  # Nama pegawai

            project_query = """
                SELECT project.id_project, project.nama_project, project.no_po, project.tgl_po, project.start_project, project.deadline, project.id_perusahaan, perusahaan.nama_perusahaan, project.id_vendor, project.selesai_project, project.status
                FROM project
                INNER JOIN perusahaan ON project.id_perusahaan = perusahaan.id_perusahaan
                WHERE project.id_project = %s
            """

            cursor.execute(project_query, (id_project,))
            project_result = cursor.fetchone()

            if project_result:
                project = {
                    'id_project': project_result[0],
                    'nama_project': project_result[1],
                    'no_po': project_result[2],
                    'tgl_po': project_result[3].strftime('%d %b %Y'),
                    'start_time': project_result[4].strftime('%d %b %Y'),
                    'deadline': project_result[5].strftime('%d %b %Y'),
                    'id_perusahaan': project_result[6],
                    'nama_perusahaan': project_result[7],  # Nama perusahaan
                    'id_vendor': project_result[8],
                    'nama_vendor': None,  # Nama vendor (akan diisi nanti)
                    'selesai_project': project_result[9],
                    'status': project_result[10],  # Add project status
                    'pegawai': nama,
                    'pegawai_terlibat': []
                }

                pegawai_terlibat_query = """
                    SELECT pegawai.nama
                    FROM struktur
                    INNER JOIN pegawai ON struktur.id_pegawai = pegawai.id_pegawai
                    WHERE struktur.id_project = %s
                """

                cursor.execute(pegawai_terlibat_query, (id_project,))
                pegawai_terlibat_results = cursor.fetchall()

                for pegawai_terlibat_result in pegawai_terlibat_results:
                    nama_terlibat = pegawai_terlibat_result[0]
                    project['pegawai_terlibat'].append(nama_terlibat)

                # Fetching vendor name based on id_vendor
                vendor_query = """
                    SELECT nama_vendor
                    FROM vendor
                    WHERE id_vendor = %s
                """

                cursor.execute(vendor_query, (project_result[8],))
                vendor_result = cursor.fetchone()
                if vendor_result:
                    project['nama_vendor'] = vendor_result[0]

                # Query untuk mendapatkan progres proyek
                progres_query = "SELECT * FROM tahapan WHERE ID_project = %s"
                cursor.execute(progres_query, (id_project,))
                progres_results = cursor.fetchall()

                progres_tahapan = []

                progres_hasil = 0  # Inisialisasi progres_hasil

                for progres_result in progres_results:
                    id_tahapan = progres_result[0]
                    detail_query = "SELECT COUNT(*) FROM detailtahapan WHERE id_tahapan = %s"
                    cursor.execute(detail_query, (id_tahapan,))
                    detail_count = cursor.fetchone()[0]

                    if progres_result[2] == 'selesai':
                        # Jika status tahapan adalah 'selesai', set progres menjadi 100
                        progress = 100
                    else:
                        # Query untuk mendapatkan status dari tabel detailtahapan
                        detail_status_query = "SELECT status FROM detailtahapan WHERE id_tahapan = %s"
                        cursor.execute(detail_status_query, (id_tahapan,))
                        detail_statuses = cursor.fetchall()

                        # Inisialisasi progres menjadi 0
                        progress = 0

                        if detail_count > 0:
                            # Menghitung progres hanya jika setidaknya ada satu detail
                            completed_count = 0

                            for detail_status in detail_statuses:
                                if detail_status[0] == 'selesai':
                                    completed_count += 1

                            if completed_count > 0:
                                progress = 100 * completed_count / detail_count

                    # Menambahkan progres ke progres_hasil
                    progres_hasil += progress

                    progres_tahapan.append(progress)

                # Menghitung rata-rata progres
                if len(progres_tahapan) > 0:
                    progres_hasil /= len(progres_tahapan)

                # Membatasi progres_hasil agar tidak melebihi 100
                progres_hasil = min(progres_hasil, 100)

                # Bulatkan nilai progres_hasil ke bawah (floor)
                progres_hasil = progres_hasil // 1

                project['progres_tahapan'] = progres_tahapan
                project['progres_hasil'] = progres_hasil


                projects.append(project)

        closeDb()

        if projects:
            return jsonify(projects)
        else:
            return "No projects found."

    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/namaperusahaan', methods=['GET'])
def get_nama_pegawai():
    try:
        id_pegawai = request.args.get('id_pegawai')

        if id_pegawai is None:
            return jsonify({'error': 'Missing id_pegawai parameter'})

        id_pegawai = int(id_pegawai)

        openDb()

        get_name_query = """
            SELECT nama
            FROM pegawai
            WHERE id_pegawai = %s
        """

        cursor.execute(get_name_query, (id_pegawai,))
        name_result = cursor.fetchone()

        closeDb()

        if name_result:
            return jsonify({'nama': name_result[0]})
        else:
            return jsonify({'error': 'Employee not found.'})

    except Exception as e:
        return jsonify({'error': str(e)})
    

@app.route('/editpassword', methods=['POST'])
def edit_password():
    try:
        id_pegawai = request.args.get('id_pegawai')
        
        if id_pegawai is None:
            return jsonify({'error': 'Missing id_pegawai parameter'})

        id_pegawai = int(id_pegawai)
        
        data = request.get_json()
        new_password = data.get('new_password')
        
        if new_password is None:
            return jsonify({'error': 'Missing new_password parameter'})

        openDb()
        
        hashed_password = hashlib.sha512(new_password.encode()).hexdigest()

        update_password_query = """
            UPDATE pegawai
            SET password = %s
            WHERE id_pegawai = %s
        """
        
        cursor.execute(update_password_query, (hashed_password, id_pegawai))
        conn.commit()

        closeDb()

        response = {'msg': 'Password updated successfully'}

    except Exception as e:
        conn.rollback()
        response = {'error': str(e)}

    return jsonify(response)



@app.route('/uploadphoto', methods=['POST'])
def upload_photo():
    openDb()

    data = request.get_json()
    id_pegawai = data.get('id_pegawai')
    image_data = data.get('image')
    location = data.get('location')  # Get the location data

    if id_pegawai is None or image_data is None or location is None:
        closeDb()
        return jsonify({'error': 'Missing id_pegawai, image, or location'})

    try:
        image_blob = base64.b64decode(image_data)

        # Insert the image data and location into the database
        insert_query = "INSERT INTO absensi (id_pegawai, absensi_masuk, absensi_keluar, Lokasi_absen_masuk) VALUES (%s, %s, CURRENT_TIMESTAMP, %s)"
        cursor.execute(insert_query, (id_pegawai, image_blob, location))
        conn.commit()

        response = {'msg': 'Photo uploaded and attendance recorded successfully'}
    except Exception as e:
        conn.rollback()
        response = {'error': str(e)}

    closeDb()

    return jsonify(response)

@app.route('/tahapan', methods=['GET'])
def get_phases():
    try:
        id_project = request.args.get('ID_project')

        if id_project is None:
            return jsonify({'error': 'Missing ID_project parameter'})

        id_project = int(id_project)

        openDb()

        phases_query = "SELECT * FROM tahapan WHERE ID_project = %s"

        cursor.execute(phases_query, (id_project,))
        phases_results = cursor.fetchall()

        phases = []

        for phase_result in phases_results:
            phase = {
                'id_tahapan': phase_result[0],
                'nama_tahapan': phase_result[1],
                'status': phase_result[2],
                'id_project': phase_result[3],
                'start_date': phase_result[4].strftime('%Y-%m-%d'),
                'Deadline': phase_result[5].strftime('%Y-%m-%d'),
                'hasil_tahapan': phase_result[6],
                'tgl_actual': phase_result[7],
                'tgl_tugas': phase_result[8]
            }

            phases.append(phase)

        closeDb()

        if phases:
            return jsonify(phases)
        else:
            return "No phases found."

    except Exception as e:
        return jsonify({'error': str(e)})



@app.route('/detail', methods=['GET'])
def get_detail():
    try:
        id_tahapan = request.args.get('ID_tahapan')

        if id_tahapan is None:
            return jsonify({'error': 'Missing ID_tahapan parameter'})

        id_tahapan = int(id_tahapan)

        openDb()

        phases_query = """
            SELECT id_tahapan, nama_tugas, desc_tugas, id_detailtahapan, status, deadline
            FROM detailtahapan
            WHERE ID_tahapan = %s
        """

        cursor.execute(phases_query, (id_tahapan,))
        phases_results = cursor.fetchall()

        phases = []

        total_phases = len(phases_results)
        if total_phases == 0:
            closeDb()
            return "No phases found."

        # Calculate progress based on the number of phases
        progress = [100 // total_phases] * total_phases
        progress[-1] += 100 % total_phases  # Distribute the remainder

        for i, phase_result in enumerate(phases_results):
            phase = {
                'id_tahapan': phase_result[0],
                'nama_tugas': phase_result[1],
                'desc_tugas': phase_result[2],
                'id_detail': phase_result[3],
                'status': phase_result[4],
                'deadline': phase_result[5].strftime('%Y-%m-%d'),
                'progres': progress[i]
            }

            phases.append(phase)

        closeDb()

        return jsonify(phases)

    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/hasil_tugas', methods=['POST'])
def upload_task_file():
    try:
        openDb()

        id_detail = request.args.get('ID_detail')

        if id_detail is None:
            return jsonify({'error': 'Missing ID_detail parameter'})

        id_detail = int(id_detail)

        # Check if the POST request has a file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']

        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        if file and allowed_file(file.filename):
            # Generate a unique filename for the uploaded file
            filename = secure_filename(file.filename)
            unique_filename = f'{id_detail}_{int(time.time())}_{filename}'

            # Specify the directory where you want to save the uploaded files
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, unique_filename)

            # Save the uploaded file to the server
            file.save(file_path)

            # Update the database with the file name
            update_query = "UPDATE detailtahapan SET hasil_tugas = %s WHERE id_detailtahapan = %s"
            cursor.execute(update_query, (unique_filename, id_detail))
            conn.commit()

            # Return a success response
            return jsonify({'message': 'File uploaded successfully', 'file_path': file_path})

        else:
            return jsonify({'error': 'Invalid file format'})

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        closeDb()

@app.route('/tugasDrive', methods=['POST'])
def update_task_drive():
    try:
        openDb()

        id_detail = request.args.get('ID_detail')

        if id_detail is None:
            return jsonify({'error': 'Missing ID_detail parameter'})

        id_detail = int(id_detail)

        data = request.get_json()
        hasil_tugas = data.get('hasil_tugas')

        if hasil_tugas is None:
            return jsonify({'error': 'Missing hasil_tugas parameter'})

        # Mendapatkan waktu saat ini
        waktu_sekarang = datetime.now().strftime('%Y-%m-%d')

        # Update database dengan hasil_tugas, status, dan waktu_sekarang
        update_query = "UPDATE detailtahapan SET hasil_tugas = %s, status = 'selesai', hari_pengumpulan = %s WHERE id_detailtahapan = %s"
        cursor.execute(update_query, (hasil_tugas, waktu_sekarang, id_detail))
        conn.commit()

        # Mengembalikan respons sukses
        return jsonify({'message': 'Data updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        closeDb()
@app.route('/hasilTugas', methods=['GET'])
def get_hasil_tugas():
    try:
        id_detail = request.args.get('id_detail')

        if id_detail is None:
            return jsonify({'error': 'Missing id_detail parameter'})

        id_detail = int(id_detail)

        openDb()  # Buka koneksi ke database

        get_result_query = """
            SELECT hasil_tugas
            FROM detailtahapan
            WHERE id_detailtahapan = %s
        """

        cursor = conn.cursor()
        cursor.execute(get_result_query, (id_detail,))
        result = cursor.fetchone()

        cursor.close()
        closeDb()  # Tutup koneksi ke database

        if result:
            return result[0] if result[0] is not None else jsonify({'result': None})

        else:
            return jsonify({'error': 'Data not found.'})

    except Exception as e:
        return jsonify({'error': str(e)})


# Endpoint to receive and store data in the database
@app.route('/add_perusahaan', methods=['POST'])
def add_perusahaan():
    openDb()
    
    data = request.get_json()
    nama_perusahaan = data.get('nama')
    jenis_perusahaan = data.get('jenis')
    alamat_perusahaan = data.get('alamat')
    contact = data.get('phone')
    
    if not (nama_perusahaan and jenis_perusahaan and alamat_perusahaan and contact):
        closeDb()
        return jsonify({'error': 'Missing data'})

    try:
        # Check if the company with the same name already exists
        query_check = "SELECT * FROM perusahaan WHERE nama_perusahaan = %s"
        cursor.execute(query_check, (nama_perusahaan,))
        existing_company = cursor.fetchone()
        
        if existing_company:
            closeDb()
            return jsonify({'message': 'Nama perusahaan sudah ada'})

        # Insert the data into the 'perusahaan' table
        query_insert = "INSERT INTO perusahaan (nama_perusahaan, jenis_perusahaan, alamat_perusahaan, contact) VALUES (%s, %s, %s, %s)"
        cursor.execute(query_insert, (nama_perusahaan, jenis_perusahaan, alamat_perusahaan, contact))
        conn.commit()
        
        closeDb()
        
        response = {
            'message': 'Data added successfully',
            'nama_perusahaan': nama_perusahaan,
            'jenis_perusahaan': jenis_perusahaan,
            'alamat_perusahaan': alamat_perusahaan,
            'contact': contact
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/perusahaan', methods=['GET'])
def get_perusahaan():
    openDb()

    try:
        # Select all data from the 'perusahaan' table
        query = "SELECT * FROM perusahaan"
        cursor.execute(query)
        results = cursor.fetchall()

        # Prepare the data for JSON response
        perusahaan_list = []
        for row in results:
            perusahaan_data = {
                'id': row[0],
                'nama_perusahaan': row[1],
                'jenis_perusahaan': row[2],
                'alamat_perusahaan': row[3],
                'contact': row[4]
            }
            perusahaan_list.append(perusahaan_data)

        closeDb()

        return jsonify(perusahaan_list)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

@app.route('/edit_perusahaan/<int:id_perusahaan>', methods=['POST'])
def edit_perusahaan(id_perusahaan):
    openDb()

    data = request.get_json()
    nama_perusahaan = data.get('nama')
    jenis_perusahaan = data.get('jenis')
    alamat_perusahaan = data.get('alamat')
    contact = data.get('phone')

    if not (nama_perusahaan and jenis_perusahaan and alamat_perusahaan and contact):
        closeDb()
        return jsonify({'error': 'Missing data'})

    try:
        # Check if the company with the given id_perusahaan exists
        query_check = "SELECT * FROM perusahaan WHERE id_perusahaan = %s"
        cursor.execute(query_check, (id_perusahaan,))
        existing_company = cursor.fetchone()

        if not existing_company:
            closeDb()
            return jsonify({'error': 'Perusahaan not found'})

        # Update the data in the 'perusahaan' table
        query_update = "UPDATE perusahaan SET nama_perusahaan = %s, jenis_perusahaan = %s, alamat_perusahaan = %s, contact = %s WHERE id_perusahaan = %s"
        cursor.execute(query_update, (nama_perusahaan, jenis_perusahaan, alamat_perusahaan, contact, id_perusahaan))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data updated successfully',
            'id_perusahaan': id_perusahaan,
            'nama_perusahaan': nama_perusahaan,
            'jenis_perusahaan': jenis_perusahaan,
            'alamat_perusahaan': alamat_perusahaan,
            'contact': contact
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/perusahaan/<int:id_perusahaan>', methods=['GET'])
def get_perusahaan_id(id_perusahaan):
    openDb()

    try:
        # Select all data from the 'perusahaan' table
        query = "SELECT * FROM perusahaan WHERE id_perusahaan= %s"
        cursor.execute(query, (id_perusahaan,))
        results = cursor.fetchall()

        # Prepare the data for JSON response
        perusahaan_list = []
        for row in results:
            perusahaan_data = {
                'id': row[0],
                'nama_perusahaan': row[1],
                'jenis_perusahaan': row[2],
                'alamat_perusahaan': row[3],
                'contact': row[4]
            }
            perusahaan_list.append(perusahaan_data)

        closeDb()

        return jsonify(perusahaan_list)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    

@app.route('/hapus_perusahaan/<int:id_perusahaan>', methods=['DELETE'])
def delete_perusahaan(id_perusahaan):
    openDb()

    try:
        # Check if the company with the given id_perusahaan exists
        query_check = "SELECT * FROM perusahaan WHERE id_perusahaan = %s"
        cursor.execute(query_check, (id_perusahaan,))
        existing_company = cursor.fetchone()

        if not existing_company:
            closeDb()
            return jsonify({'error': 'Perusahaan not found'})

        # Delete the company with the specified ID
        query_delete = "DELETE FROM perusahaan WHERE id_perusahaan = %s"
        cursor.execute(query_delete, (id_perusahaan,))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data deleted successfully',
            'id_perusahaan': id_perusahaan
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
    
@app.route('/pegawai', methods=['GET'])
def get_pegawai():
    try:
        openDb()

        # Select data from the 'pegawai' table
        query = "SELECT * FROM pegawai"
        cursor.execute(query)
        results = cursor.fetchall()

        # Prepare the data for JSON response
        pegawai_list = []
        for row in results:
            pegawai_data = {
                'id': row[0],
                'nama': row[1],
                'struktur': row[2],
                'username': row[3],
                'password': row[4]
            }
            pegawai_list.append(pegawai_data)

        closeDb()

        return jsonify(pegawai_list)
    except Exception as e:
        return jsonify({'error': str(e)}) 
@app.route('/tambahPegawai', methods=['POST'])
def tambah_pegawai():
    try:
        openDb()

        data = request.get_json()
        nama = data.get('nama', None)
        struktur = data.get('struktur', None)
        username = data.get('username', None)
        password = data.get('password', None)

        # Periksa apakah setidaknya satu data yang diberikan
        if not (nama or struktur or username):
            closeDb()
            return jsonify({'error': 'No valid data provided'})

        # Hash password menggunakan sha512 jika password ada
        hashed_password = None
        if password:
            hashed_password = hashlib.sha512(password.encode()).hexdigest()

        # Periksa apakah data dengan username atau nama yang sama sudah ada di database
        query_check = "SELECT * FROM pegawai WHERE username = %s OR nama = %s"
        cursor.execute(query_check, (username, nama))
        existing_data = cursor.fetchone()

        if existing_data:
            closeDb()
            return jsonify({'error': 'Data with the same username or name already exists'})

        # Insert data ke dalam tabel 'pegawai' hanya jika ada data yang diberikan
        if nama or struktur or username:
            # Periksa apakah password diberikan, jika tidak, set nilai kolom password ke NULL
            if hashed_password is not None:
                query_insert = "INSERT INTO pegawai (nama, struktur, username, password) VALUES (%s, %s, %s, %s)"
                cursor.execute(query_insert, (nama, struktur, username, hashed_password))
            else:
                query_insert = "INSERT INTO pegawai (nama, struktur, username) VALUES (%s, %s, %s)"
                cursor.execute(query_insert, (nama, struktur, username))

            conn.commit()

            closeDb()

            response = {
                'message': 'Pegawai added successfully',
                'nama': nama,
                'struktur': struktur,
                'username': username
            }
            return jsonify(response)
        else:
            closeDb()
            return jsonify({'error': 'No valid data provided'})
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

    
@app.route('/hapus_pegawai/<int:id_pegawai>', methods=['DELETE'])
def delete_pegawai(id_pegawai):
    openDb()

    try:
        # Check if the company with the given id_pegawai exists
        query_check = "SELECT * FROM pegawai WHERE id_pegawai = %s"
        cursor.execute(query_check, (id_pegawai,))
        existing_company = cursor.fetchone()

        if not existing_company:
            closeDb()
            return jsonify({'error': 'pegawai not found'})

        # Delete the company with the specified ID
        query_delete = "DELETE FROM pegawai WHERE id_pegawai = %s"
        cursor.execute(query_delete, (id_pegawai,))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data deleted successfully',
            'id_pegawai': id_pegawai
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

@app.route('/pegawai/<int:id_pegawai>', methods=['GET', 'POST'])
def edit_pegawai(id_pegawai):
    if request.method == 'POST':
        # Update the data of the pegawai by ID
        try:
            openDb()

            data = request.get_json()
            nama = data.get('nama', None)
            struktur = data.get('struktur', None)
            username = data.get('username', None)
            password = data.get('password', None)

            # Check if the pegawai with the given ID exists
            query_check = "SELECT * FROM pegawai WHERE id_pegawai = %s"
            cursor.execute(query_check, (id_pegawai,))
            existing_pegawai = cursor.fetchone()

            if not existing_pegawai:
                closeDb()
                return jsonify({'error': 'Pegawai not found'})

            # Update the data in the 'pegawai' table
            update_query = "UPDATE pegawai SET "
            update_values = []

            if nama:
                update_query += "nama = %s, "
                update_values.append(nama)
            if struktur:
                update_query += "struktur = %s, "
                update_values.append(struktur)
            if username:
                update_query += "username = %s, "
                update_values.append(username)
            if password:
                hashed_password = hashlib.sha512(password.encode()).hexdigest()
                update_query += "password = %s, "
                update_values.append(hashed_password)

            # Remove the trailing comma and space
            update_query = update_query.rstrip(', ')

            update_query += " WHERE id_pegawai = %s"
            update_values.append(id_pegawai)

            cursor.execute(update_query, tuple(update_values))
            conn.commit()

            closeDb()

            response = {
                'message': 'Pegawai data updated successfully',
                'id_pegawai': id_pegawai
            }
            return jsonify(response)

        except Exception as e:
            closeDb()
            return jsonify({'error': str(e)})
        

@app.route('/pegawain/<int:id_pegawai>', methods=['GET'])
def get_pegawai_id(id_pegawai):
    openDb()

    try:
        # Select all data from the 'pegawai' table
        query = "SELECT * FROM pegawai WHERE id_pegawai= %s"
        cursor.execute(query, (id_pegawai,))
        results = cursor.fetchall()

        # Prepare the data for JSON response
        perusahaan_list = []
        for row in results:
            perusahaan_data = {
                'id': row[0],
                'nama': row[1],
                'struktur': row[2],
                'username': row[3],
                'password': row[4],
            }
            perusahaan_list.append(perusahaan_data)

        closeDb()

        return jsonify(perusahaan_list)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
@app.route('/admin/project/sebelum-progres', methods=['GET'])
def get_all_projects():
    try:
        openDb()

        # Select specific columns from the 'project' table
        project_query = "SELECT p.id_project, p.no_po, p.tgl_po, p.nama_project, p.ID_perusahaan, p.ID_Vendor, p.start_project, p.deadline, p.status, p.selesai_project, perusahaan.nama_perusahaan, vendor.nama_vendor FROM project p LEFT JOIN perusahaan ON p.ID_perusahaan = perusahaan.ID_perusahaan LEFT JOIN vendor ON p.ID_Vendor = vendor.ID_Vendor"
        cursor.execute(project_query)
        projects = cursor.fetchall()

        # Prepare the data for JSON response
        projects_list = []
        for project_row in projects:
            project_data = {
                'id_project': project_row[0],
                'no_po': project_row[1],
                'tgl_po': project_row[2].strftime('%Y-%m-%d'),
                'nama_project': project_row[3],
                'ID_perusahaan': project_row[4],
                'ID_Vendor': project_row[5],
                'start_project': project_row[6].strftime('%Y-%m-%d'),
                'deadline': project_row[7].strftime('%Y-%m-%d'),
                'status': project_row[8],
                'selesai_project': project_row[9],
                'anggota': "",  # Inisialisasi anggota sebagai string kosong
                'nama_perusahaan': project_row[10],  # Nama perusahaan
                'nama_vendor': project_row[11]  # Nama perusahaan
            }

            # Query to get members working on this project
            struktur_query = "SELECT id_pegawai FROM struktur WHERE id_project = %s"
            cursor.execute(struktur_query, (project_row[0],))
            anggota_ids = cursor.fetchall()

            anggota_list = []
            for anggota_id in anggota_ids:
                # Query to get the name of the member
                pegawai_query = "SELECT nama FROM pegawai WHERE id_pegawai = %s"
                cursor.execute(pegawai_query, (anggota_id[0],))
                anggota_nama = cursor.fetchone()
                if anggota_nama:
                    anggota_list.append(anggota_nama[0])

            # Join anggota_list menjadi string dengan koma sebagai pemisah
            project_data['anggota'] = ", ".join(anggota_list)

            projects_list.append(project_data)

        closeDb()

        return jsonify(projects_list)

    except Exception as e:
        # Handle exception
        return jsonify({'error': str(e)})


@app.route('/tambahproject', methods=['POST'])
def tambah_project():
    try:
        openDb()

        data = request.get_json()
        no_po = data.get('no_po', None)
        tgl_po = data.get('tgl_po', None)
        nama_project = data.get('nama_project', None)
        id_perusahaan = data.get('id_perusahaan', None)
        id_vendor = data.get('id_vendor', None)
        start_project = data.get('start_project', None)
        deadline = data.get('deadline', None)

        # Periksa apakah setidaknya ada data yang valid yang diberikan
        if not (no_po and tgl_po and nama_project and id_perusahaan and id_vendor and start_project and deadline):
            closeDb()
            return jsonify({'error': 'Missing or invalid data'})

        # Konversi tanggal dari string ke objek datetime
        tgl_po_datetime = datetime.strptime(tgl_po, '%Y-%m-%d')
        start_project_datetime = datetime.strptime(start_project, '%Y-%m-%d')
        deadline_datetime = datetime.strptime(deadline, '%Y-%m-%d')


        # Insert data ke dalam tabel 'project'
        insert_query = "INSERT INTO project (no_po, tgl_po, nama_project, id_perusahaan, id_vendor, start_project, deadline, status) VALUES (%s, %s, %s, %s, %s, %s, %s, 'belum selesai')"
        cursor.execute(insert_query, (no_po, tgl_po_datetime, nama_project, id_perusahaan, id_vendor, start_project_datetime, deadline_datetime))
        conn.commit()

        closeDb()

        response = {
            'message': 'Project added successfully',
            'no_po': no_po,
            'tgl_po': tgl_po_datetime.strftime('%Y-%m-%d'),
            'nama_project': nama_project,
            'id_perusahaan': id_perusahaan,
            'id_vendor': id_vendor,
            'start_project': start_project_datetime.strftime('%Y-%m-%d'),
            'deadline': deadline_datetime.strftime('%Y-%m-%d'),
            'status': 'belum-selesai'
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

    
@app.route('/tambahTahapan/<int:id_project>', methods=['POST'])
def tambah_tahapan(id_project):
    try:
        openDb()

        data = request.get_json()
        nama_tahapan = data.get('nama_tahapan', None)
        start_project = data.get('start_project', None)
        deadline = data.get('deadline', None)

        # Periksa apakah setidaknya ada data yang valid yang diberikan
        if not (nama_tahapan and start_project and deadline):
            closeDb()
            return jsonify({'error': 'Missing or invalid data'})

        # Konversi tanggal dan waktu menjadi objek datetime
        start_project_date = datetime.strptime(start_project, '%Y-%m-%d')
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')

        # Insert data ke dalam tabel 'tahapan'
        insert_query = "INSERT INTO tahapan (nama_tahapan, status, ID_project, start_date, deadline) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (nama_tahapan, 'belum selesai', id_project, start_project_date, deadline_date))
        conn.commit()

        closeDb()

        response = {
            'message': 'Tahapan added successfully',
            'nama_tahapan': nama_tahapan,
            'status': 'belum selesai',
            'ID_project': id_project,
            'start_project': start_project_date.strftime('%Y-%m-%d'),
            'deadline': deadline_date.strftime('%Y-%m-%d')
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/hapus_tahapan/<int:id_tahapan>', methods=['DELETE'])
def delete_tahapan(id_tahapan):
    openDb()

    try:
        # Check if the company with the given id_tahapan exists
        query_check = "SELECT * FROM tahapan WHERE id_tahapan = %s"
        cursor.execute(query_check, (id_tahapan,))
        existing_company = cursor.fetchone()

        if not existing_company:
            closeDb()
            return jsonify({'error': 'tahapan not found'})

        # Delete the company with the specified ID
        query_delete = "DELETE FROM tahapan WHERE id_tahapan = %s"
        cursor.execute(query_delete, (id_tahapan,))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data deleted successfully',
            'id_tahapan': id_tahapan
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})


@app.route('/tahapan_id/<int:id_tahapan>', methods=['GET'])
def get_tahapan_by_id(id_tahapan):
    try:
        openDb()

        query = """
            SELECT *
            FROM tahapan
            WHERE id_tahapan = %s
        """

        cursor.execute(query, (id_tahapan,))
        result = cursor.fetchone()

        closeDb()

        if result:
            tahapan_data = {
                'id_tahapan': result[0],
                'nama_tahapan': result[1],
                'deadline': result[4].strftime('%Y-%m-%d %H:%M'),
                'end_time': result[4].strftime('%H:%M'),
                'end_date': result[4].strftime('%Y-%m-%d'),

                # Add more columns as needed
            }
            return jsonify(tahapan_data)
        else:
            return "No data found for the specified id_tahapan."

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/editTahapan/<int:id_tahapan>', methods=['POST'])
def edit_tahapan(id_tahapan):
    try:
        openDb()

        data = request.get_json()
        nama_tahapan = data.get('nama_tahapan', None)
        start_project = data.get('start_project', None)
        deadline = data.get('deadline', None)

        # Periksa apakah setidaknya satu data yang diberikan
        if not (nama_tahapan or start_project or deadline):
            closeDb()
            return jsonify({'error': 'No valid data provided'})

        # Format tanggal sesuai dengan format datetime
        if start_project:
            start_project = datetime.strptime(start_project, "%Y-%m-%d")
        if deadline:
            deadline = datetime.strptime(deadline, "%Y-%m-%d")

        # Update data dalam tabel 'tahapan'
        query_update = "UPDATE tahapan SET nama_tahapan = %s, start_date = %s, deadline = %s WHERE id_tahapan = %s"
        cursor.execute(query_update, (nama_tahapan, start_project, deadline, id_tahapan))
        conn.commit()

        closeDb()

        response = {
            'message': 'Tahapan updated successfully',
            'id_tahapan': id_tahapan,
            'nama_tahapan': nama_tahapan,
            'start_project': start_project.strftime('%Y-%m-%d') if start_project else None,
            'deadline': deadline.strftime('%Y-%m-%d') if deadline else None
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})


@app.route('/tambahdetail/<int:id_tahapan>', methods=['POST'])
def tambah_detail(id_tahapan):
    try:
        openDb()

        data = request.get_json()
        nama_tugas = data.get('nama_tugas', None)
        desc_tugas = data.get('desc_tugas', None)
        end_date = data.get('end_date', None)

        # Check if at least valid data is provided
        if not (nama_tugas and desc_tugas and end_date):
            closeDb()
            return jsonify({'error': 'Missing or invalid data'})

        # Combine date and time into a single datetime object
        deadline = datetime.strptime(end_date, '%Y-%m-%d')

        # Insert data into the 'detailtahapan' table
        insert_query = "INSERT INTO detailtahapan (ID_tahapan, nama_tugas, desc_tugas, deadline, status) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (id_tahapan, nama_tugas, desc_tugas, deadline, 'belum selesai'))
        conn.commit()

        closeDb()

        response = {
            'message': 'Detail added successfully',
            'ID_tahapan': id_tahapan,
            'nama_tugas': nama_tugas,
            'desc_tugas': desc_tugas,
            'deadline': deadline.strftime('%Y-%m-%d'),
            'status': 'belum selesai'
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

@app.route('/hapus_detail/<int:id_detailtahapan>', methods=['DELETE'])
def delete_detail(id_detailtahapan):
    openDb()

    try:
        # Check if the company with the given id_detailtahapan exists
        query_check = "SELECT * FROM detailtahapan WHERE id_detailtahapan = %s"
        cursor.execute(query_check, (id_detailtahapan,))
        existing_company = cursor.fetchone()

        if not existing_company:
            closeDb()
            return jsonify({'error': 'detail not found'})

        # Delete the company with the specified ID
        query_delete = "DELETE FROM detailtahapan WHERE id_detailtahapan = %s"
        cursor.execute(query_delete, (id_detailtahapan,))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data deleted successfully',
            'id_detailtahapan': id_detailtahapan
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/detail_id/<int:id_detailtahapan>', methods=['GET'])
def get_detail_by_id(id_detailtahapan):
    try:
        openDb()

        query = """
            SELECT *
            FROM detailtahapan
            WHERE id_detailtahapan = %s
        """

        cursor.execute(query, (id_detailtahapan,))
        result = cursor.fetchone()

        closeDb()

        if result:
            tahapan_data = {
                'id_detail': result[0],
                'id_tahapan': result[1],
                'nama_tugas': result[2],
                'desc_tugas': result[3],
                'status': result[4],
                'deadline': result[5],  # Assuming it's already in the correct format
                'end_time': result[5].strftime('%H:%M'),
                'end_date': result[5].strftime('%Y-%m-%d'),
                'hasil_tugas': result[6],
                'hari_pengumpulan': result[7],  # Assuming it's already in the correct format

                # Add more columns as needed
            }
            return jsonify(tahapan_data)
        else:
            return "No data found for the specified id_tahapan."

    except Exception as e:
        return jsonify({'error': str(e)})

    
@app.route('/editDetail/<int:id_detailtahapan>', methods=['POST'])
def edit_detail(id_detailtahapan):
    try:
        openDb()

        data = request.get_json()
        nama_tugas = data.get('nama_tugas')
        desc_tugas = data.get('desc_tugas')
        end_date = data.get('end_date')

        if nama_tugas is None or desc_tugas is None or end_date is None:
            return jsonify({'error': 'Missing parameters'})

        # Combine end_date and end_time to create a datetime object
        deadline = datetime.strptime(f'{end_date}', '%Y-%m-%d')

        # Update the database with the new values
        update_query = """
            UPDATE detailtahapan
            SET nama_tugas = %s, desc_tugas = %s, deadline = %s
            WHERE id_detailtahapan = %s
        """

        cursor.execute(update_query, (nama_tugas, desc_tugas, deadline, id_detailtahapan))
        conn.commit()

        # Return a success response
        return jsonify({'message': 'Detail updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        closeDb()

@app.route('/admin/project_id/<int:id_project>', methods=['GET'])
def get_project_by_id(id_project):
    try:
        openDb()

        # Query to retrieve the project data by id_project
        project_query = "SELECT id_project, no_po, tgl_po, nama_project, ID_perusahaan, ID_Vendor, start_project, deadline, status, selesai_project FROM project WHERE id_project = %s"
        cursor.execute(project_query, (id_project,))
        project_data = cursor.fetchone()

        if not project_data:
            closeDb()
            return jsonify({'error': 'Project not found'})

        # Prepare the data for JSON response
        project_info = {
            'id_project': project_data[0],
            'no_po': project_data[1],
            'tgl_po': project_data[2].strftime('%Y-%m-%d'),  # Format tanggal sesuai dengan elemen input tanggal
            'nama_project': project_data[3],
            'ID_perusahaan': project_data[4],
            'ID_Vendor': project_data[5],
            'start_project': project_data[6].strftime('%Y-%m-%d'),
            'deadline': project_data[7].strftime('%Y-%m-%d'),
            'status': project_data[8],
            'selesai_project': project_data[9]
        }

        closeDb()

        return jsonify(project_info)

    except Exception as e:
        # Handle exception
        return jsonify({'error': str(e)})



@app.route('/editproject/<int:id_project>', methods=['POST'])
def edit_project(id_project):
    try:
        openDb()

        data = request.get_json()

        # Ekstrak data dari permintaan JSON
        no_po = data.get('no_po')
        tgl_po = data.get('tgl_po')
        nama_project = data.get('nama_project')
        id_perusahaan = data.get('id_perusahaan')
        id_vendor = data.get('id_vendor')
        start_project = data.get('start_project')
        deadline = data.get('deadline')

        # Periksa apakah setidaknya ada data yang valid yang diberikan
        if not (no_po and tgl_po and nama_project and start_project and deadline):
            closeDb()
            return jsonify({'error': 'Missing or invalid data'})

        # Gabungkan tanggal awal dan akhir dalam satu objek datetime
        tgl_po_datetime = datetime.strptime(tgl_po, '%Y-%m-%d')
        start_project_datetime = datetime.strptime(start_project, '%Y-%m-%d')
        deadline_datetime = datetime.strptime(deadline, '%Y-%m-%d')

        # Periksa apakah proyek dengan id_project yang diberikan ada
        query_check = "SELECT * FROM project WHERE id_project = %s"
        cursor.execute(query_check, (id_project,))
        existing_project = cursor.fetchone()

        if not existing_project:
            closeDb()
            return jsonify({'error': 'Project not found'})

        # Update data proyek yang ada
        update_query = "UPDATE project SET no_po = %s, tgl_po = %s, nama_project = %s, start_project = %s, deadline = %s"
        query_params = (no_po, tgl_po_datetime, nama_project, start_project_datetime, deadline_datetime)

        # Hanya perbarui id_perusahaan dan id_vendor jika mereka diberikan dalam permintaan JSON
        if id_perusahaan is not None and id_perusahaan != "null":
            update_query += ", id_perusahaan = %s"
            query_params += (id_perusahaan,)

        if id_vendor is not None and id_vendor != "null":
            update_query += ", id_vendor = %s"
            query_params += (id_vendor,)

        update_query += " WHERE id_project = %s"
        query_params += (id_project,)

        cursor.execute(update_query, query_params)

        conn.commit()

        closeDb()

        response = {
            'message': 'Project updated successfully',
            'id_project': id_project,
            'no_po': no_po,
            'tgl_po': tgl_po,
            'nama_project': nama_project,
            'start_project': start_project,
            'deadline': deadline,
            'id_perusahaan': id_perusahaan,
            'id_vendor': id_vendor
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})


@app.route('/hapusproject/<int:id_project>', methods=['DELETE'])
def delete_project(id_project):
    try:
        openDb()

        # Periksa apakah proyek dengan id_project yang diberikan ada
        query_check = "SELECT * FROM project WHERE id_project = %s"
        cursor.execute(query_check, (id_project,))
        existing_project = cursor.fetchone()

        if not existing_project:
            closeDb()
            return jsonify({'error': 'Project not found'})

        # Hapus proyek dengan ID yang diberikan
        delete_query = "DELETE FROM project WHERE id_project = %s"
        cursor.execute(delete_query, (id_project,))
        conn.commit()

        closeDb()

        response = {
            'message': 'Project deleted successfully',
            'id_project': id_project
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/addStruktur/<int:id_project>', methods=['POST'])
def add_struktur(id_project):
    try:
        openDb()
        
        # Dapatkan data pegawai dan nama_struktur dari permintaan
        data = request.get_json()
        id_pegawai = data.get('id_pegawai')
        nama_struktur = data.get('nama_struktur')
        
        if id_pegawai is None:
            closeDb()
            return jsonify({'error': 'Missing id_pegawai parameter'})
        
        if nama_struktur is None:
            closeDb()
            return jsonify({'error': 'Missing nama_struktur parameter'})

        pegawai_exists = False  # Menyimpan apakah ada setidaknya satu pegawai yang sudah ada dalam proyek

        # Loop melalui daftar pegawai dan tambahkan mereka ke tabel struktur
        for pegawai_id in id_pegawai:
            # Periksa apakah pegawai dengan ID tersebut sudah ada dalam proyek
            check_query = "SELECT * FROM struktur WHERE id_pegawai = %s AND id_project = %s"
            cursor.execute(check_query, (pegawai_id, id_project))
            struktur_exists = cursor.fetchone()

            if struktur_exists:
                # Pegawai sudah ada dalam proyek, tandai bahwa ada pegawai yang sudah ada
                pegawai_exists = True
            else:
                # Periksa apakah pegawai dengan ID tersebut ada dalam database pegawai
                check_query = "SELECT * FROM pegawai WHERE id_pegawai = %s"
                cursor.execute(check_query, (pegawai_id,))
                pegawai_exists_in_db = cursor.fetchone()

                if pegawai_exists_in_db:
                    # Tambahkan data struktur ke database dengan nama_struktur
                    insert_query = "INSERT INTO struktur (id_pegawai, id_project, nama_struktur) VALUES (%s, %s, %s)"
                    cursor.execute(insert_query, (pegawai_id, id_project, nama_struktur))
                    conn.commit()
                else:
                    # Pegawai dengan ID tersebut tidak ditemukan
                    closeDb()
                    return jsonify({'error': f'Pegawai dengan ID {pegawai_id} tidak ditemukan'})

        closeDb()

        if pegawai_exists:
            # Jika setidaknya satu pegawai sudah ada dalam proyek, kirim pesan kesalahan
            return jsonify({'message': 'Salah satu pegawai sudah ada dalam proyek'})
        
        response = {
            'message': 'Data struktur added successfully',
            'id_project': id_project,
            'id_pegawai': id_pegawai,
            'nama_struktur': nama_struktur
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

    
@app.route('/struktur/<int:id_project>', methods=['GET'])
def get_struktur_id(id_project):
    openDb()

    try:
        # Select data from the 'struktur' table and join it with the 'pegawai' table
        query = """
            SELECT struktur.id_pegawai, pegawai.nama,pegawai.username, struktur.nama_struktur
            FROM struktur
            INNER JOIN pegawai ON struktur.id_pegawai = pegawai.id_pegawai
            WHERE struktur.id_project = %s
        """
        cursor.execute(query, (id_project,))
        results = cursor.fetchall()

        # Prepare the data for JSON response
        struktur_list = []
        for row in results:
            struktur_data = {
                'id_pegawai': row[0],
                'nama_pegawai': row[1],        # Menambahkan nama pegawai ke respons
                'username': row[2],
                'nama_struktur': row[3] 
            }
            struktur_list.append(struktur_data)

        closeDb()

        return jsonify(struktur_list)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})


@app.route('/editProfile/<int:id_pegawai>', methods=['POST'])
def edit_profile(id_pegawai):
    try:
        openDb()

        data = request.get_json()
        username = data.get('username', None)
        nama = data.get('nama', None)
        password = data.get('password', None)

        # Periksa apakah setidaknya satu data yang diberikan
        if not (username or nama or password):
            closeDb()
            return jsonify({'error': 'No valid data provided'})

        # Hash password menggunakan sha512 jika password ada
        hashed_password = None
        if password:
            hashed_password = hashlib.sha512(password.encode()).hexdigest()

        # Update data di tabel 'pegawai' hanya jika ada data yang diberikan
        update_query = "UPDATE pegawai SET "
        update_values = []

        if username:
            update_query += "username = %s, "
            update_values.append(username)
        if nama:
            update_query += "nama = %s, "
            update_values.append(nama)
        if hashed_password is not None:
            update_query += "password = %s, "
            update_values.append(hashed_password)

        # Hapus koma ekstra di akhir query
        update_query = update_query.rstrip(', ')

        # Tambahkan WHERE clause untuk membatasi pembaruan hanya untuk ID pegawai yang sesuai
        update_query += " WHERE id_pegawai = %s"
        update_values.append(id_pegawai)

        cursor.execute(update_query, tuple(update_values))
        conn.commit()

        closeDb()

        response = {
            'message': 'Profil pegawai updated successfully',
            'id_pegawai': id_pegawai
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/detail/admin', methods=['GET'])
def get_detail_asasa():
    try:
        openDb()

        # Select data from the 'detail' table
        query = "SELECT * FROM detailtahapan"
        cursor.execute(query)
        results = cursor.fetchall()

        # Prepare the data for JSON response
        detail_list = []
        for row in results:
            detail_data = {
                'id_detail': row[0],
                'id_tahapan': row[1],
                'nama_tugas': row[2],
                'desc_tugas': row[3],
                'status': row[4]
            }
            detail_list.append(detail_data)

        closeDb()

        return jsonify(detail_list)
    except Exception as e:
        return jsonify({'error': str(e)}) 
@app.route('/tahapan/admin', methods=['GET'])
def get_tahapan_asasa():
    try:
        openDb()

        # Select data from the 'detail' table
        query = "SELECT * FROM tahapan"
        cursor.execute(query)
        results = cursor.fetchall()

        # Prepare the data for JSON response
        detail_list = []
        for row in results:
            detail_data = {
                'id_project': row[3],
                'id_tahapan':row[0],
                'nama':  row[1],
                'tanggal_target': row[5],
                'status': row[2]
            }
            detail_list.append(detail_data)

        closeDb()

        return jsonify(detail_list)
    except Exception as e:
        return jsonify({'error': str(e)}) 

@app.route('/tahapan/selesai/admin/<int:id_tahapan>', methods=['POST'])
def set_tahapan_selesai(id_tahapan):
    try:
        openDb()

        # Periksa apakah tahapan dengan id_tahapan tertentu ada
        query_check = "SELECT * FROM tahapan WHERE id_tahapan = %s"
        cursor.execute(query_check, (id_tahapan,))
        existing_tahapan = cursor.fetchone()

        if not existing_tahapan:
            closeDb()
            return jsonify({'error': 'Tahapan not found'})

        data = request.get_json()
        status = data.get('status')

        if not status:
            closeDb()
            return jsonify({'error': 'Missing status parameter'})

        # Update status tahapan ke 'selesai' di database
        update_query = "UPDATE tahapan SET status = %s WHERE id_tahapan = %s"
        cursor.execute(update_query, (status, id_tahapan))
        conn.commit()

        closeDb()

        response = {
            'message': 'Tahapan updated successfully',
            'id_tahapan': id_tahapan,
            'status': status
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
@app.route('/project/selesai/admin/<int:id_project>', methods=['POST'])
def set_Project_selesai(id_project):
    try:
        openDb()

        # Periksa apakah tahapan dengan id_project tertentu ada
        query_check = "SELECT * FROM project WHERE id_project = %s"
        cursor.execute(query_check, (id_project,))
        existing_project = cursor.fetchone()

        if not existing_project:
            closeDb()
            return jsonify({'error': 'project not found'})

        data = request.get_json()
        status = data.get('status')

        if not status:
            closeDb()
            return jsonify({'error': 'Missing status parameter'})

        if status != 'selesai':
            selesai_date = None
        else:
            selesai_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update status project ke 'selesai' di database
        update_query = "UPDATE project SET status = %s, selesai_project = %s WHERE id_project = %s"
        cursor.execute(update_query, (status, selesai_date, id_project))
        conn.commit()

        closeDb()

        response = {
            'message': 'project updated successfully',
            'id_project': id_project,
            'status': status,
            'selesai_project': selesai_date
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
@app.route('/struktur/<int:id_pegawai>/<int:id_project>', methods=['DELETE'])
def delete_struktur(id_pegawai, id_project):
    try:
        openDb()

        # Periksa apakah data dengan id_pegawai dan id_project ada di tabel 'struktur'
        query_check = "SELECT * FROM struktur WHERE id_pegawai = %s AND id_project = %s"
        cursor.execute(query_check, (id_pegawai, id_project))
        existing_data = cursor.fetchall()

        if not existing_data:
            closeDb()
            return jsonify({'message': 'Data not found'})

        # Hapus data dari tabel 'struktur' berdasarkan id_pegawai dan id_project
        query_delete = "DELETE FROM struktur WHERE id_pegawai = %s AND id_project = %s"
        cursor.execute(query_delete, (id_pegawai, id_project))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data deleted successfully',
            'id_pegawai': id_pegawai,
            'id_project': id_project
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
@app.route('/edit_struktur/<int:id_pegawai>/<int:id_project>', methods=['POST'])
def edit_struktur(id_pegawai, id_project):
    try:
        openDb()

        # Periksa apakah data dengan id_pegawai dan id_project ada di tabel 'struktur'
        query_check = "SELECT * FROM struktur WHERE id_pegawai = %s AND id_project = %s"
        cursor.execute(query_check, (id_pegawai, id_project))
        existing_data = cursor.fetchone()

        if not existing_data:
            closeDb()
            return jsonify({'message': 'Data not found'})

        data = request.get_json()
        new_id_pegawai = data.get('new_id_pegawai')
        new_nama_struktur = data.get('new_nama_struktur')

        # Periksa apakah new_id_pegawai adalah None atau memiliki nilai "null"
        if new_id_pegawai is None or new_id_pegawai == "null":
            new_id_pegawai = None

        # Periksa apakah new_nama_struktur adalah None atau memiliki nilai "null"
        if new_nama_struktur is None or new_nama_struktur == "null":
            new_nama_struktur = None

        # Periksa apakah ada data yang akan diperbarui
        if new_id_pegawai is None and new_nama_struktur is None:
            closeDb()
            return jsonify({'message': 'No data to update'})

        # Buat query untuk mengupdate kolom id_pegawai dan/atau nama_struktur
        update_query = "UPDATE struktur SET "
        update_values = []

        if new_id_pegawai is not None:
            update_query += "id_pegawai = %s, "
            update_values.append(new_id_pegawai)

        if new_nama_struktur is not None:
            update_query += "nama_struktur = %s, "
            update_values.append(new_nama_struktur)

        # Hapus koma terakhir dan tambahkan WHERE clause
        update_query = update_query.rstrip(', ')
        update_query += " WHERE id_pegawai = %s AND id_project = %s"
        update_values.extend([id_pegawai, id_project])

        cursor.execute(update_query, tuple(update_values))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data updated successfully',
            'id_pegawai': id_pegawai,
            'id_project': id_project
        }
        return jsonify(response)

    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    openDb()
    
    data = request.get_json()
    nama_vendor = data.get('nama')
    jenis_vendor = data.get('jenis')
    alamat_vendor = data.get('alamat')
    contact = data.get('phone')
    
    if not (nama_vendor and jenis_vendor and alamat_vendor and contact):
        closeDb()
        return jsonify({'error': 'Missing data'})

    try:
        # Check if the company with the same name already exists
        query_check = "SELECT * FROM vendor WHERE nama_vendor = %s"
        cursor.execute(query_check, (nama_vendor,))
        existing_company = cursor.fetchone()
        
        if existing_company:
            closeDb()
            return jsonify({'message': 'Nama vendor sudah ada'})

        # Insert the data into the 'vendor' table
        query_insert = "INSERT INTO vendor (nama_vendor, jenis_vendor, alamat_vendor, contact) VALUES (%s, %s, %s, %s)"
        cursor.execute(query_insert, (nama_vendor, jenis_vendor, alamat_vendor, contact))
        conn.commit()
        
        closeDb()
        
        response = {
            'message': 'Data added successfully',
            'nama_vendor': nama_vendor,
            'jenis_vendor': jenis_vendor,
            'alamat_vendor': alamat_vendor,
            'contact': contact
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/vendor', methods=['GET'])
def get_vendor():
    openDb()

    try:
        # Select all data from the 'vendor' table
        query = "SELECT * FROM vendor"
        cursor.execute(query)
        results = cursor.fetchall()

        # Prepare the data for JSON response
        vendor_list = []
        for row in results:
            vendor_data = {
                'id': row[0],
                'nama_vendor': row[1],
                'jenis_vendor': row[2],
                'alamat_vendor': row[3],
                'contact': row[4]
            }
            vendor_list.append(vendor_data)

        closeDb()

        return jsonify(vendor_list)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

@app.route('/edit_vendor/<int:id_vendor>', methods=['POST'])
def edit_vendor(id_vendor):
    openDb()

    data = request.get_json()
    nama_vendor = data.get('nama')
    jenis_vendor = data.get('jenis')
    alamat_vendor = data.get('alamat')
    contact = data.get('phone')

    if not (nama_vendor and jenis_vendor and alamat_vendor and contact):
        closeDb()
        return jsonify({'error': 'Missing data'})

    try:
        # Check if the company with the given id_vendor exists
        query_check = "SELECT * FROM vendor WHERE id_vendor = %s"
        cursor.execute(query_check, (id_vendor,))
        existing_company = cursor.fetchone()

        if not existing_company:
            closeDb()
            return jsonify({'error': 'vendor not found'})

        # Update the data in the 'vendor' table
        query_update = "UPDATE vendor SET nama_vendor = %s, jenis_vendor = %s, alamat_vendor = %s, contact = %s WHERE id_vendor = %s"
        cursor.execute(query_update, (nama_vendor, jenis_vendor, alamat_vendor, contact, id_vendor))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data updated successfully',
            'id_vendor': id_vendor,
            'nama_vendor': nama_vendor,
            'jenis_vendor': jenis_vendor,
            'alamat_vendor': alamat_vendor,
            'contact': contact
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    
@app.route('/vendor/<int:id_vendor>', methods=['GET'])
def get_vendor_id(id_vendor):
    openDb()

    try:
        # Select all data from the 'vendor' table
        query = "SELECT * FROM vendor WHERE id_vendor= %s"
        cursor.execute(query, (id_vendor,))
        results = cursor.fetchall()

        # Prepare the data for JSON response
        vendor_list = []
        for row in results:
            vendor_data = {
                'id': row[0],
                'nama_vendor': row[1],
                'jenis_vendor': row[2],
                'alamat_vendor': row[3],
                'contact': row[4]
            }
            vendor_list.append(vendor_data)

        closeDb()

        return jsonify(vendor_list)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    

@app.route('/hapus_vendor/<int:id_vendor>', methods=['DELETE'])
def delete_vendor(id_vendor):
    openDb()

    try:
        # Check if the company with the given id_vendor exists
        query_check = "SELECT * FROM vendor WHERE id_vendor = %s"
        cursor.execute(query_check, (id_vendor,))
        existing_company = cursor.fetchone()

        if not existing_company:
            closeDb()
            return jsonify({'error': 'vendor not found'})

        # Delete the company with the specified ID
        query_delete = "DELETE FROM vendor WHERE id_vendor = %s"
        cursor.execute(query_delete, (id_vendor,))
        conn.commit()

        closeDb()

        response = {
            'message': 'Data deleted successfully',
            'id_vendor': id_vendor
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})

@app.route('/tugasDriveTahapan', methods=['POST'])
def update_task_drive_tahapan():
    try:
        openDb()

        id_tahapan = request.args.get('id_tahapan')

        if id_tahapan is None:
            return jsonify({'error': 'Missing id_tahapan parameter'})

        id_tahapan = int(id_tahapan)

        data = request.get_json()
        hasil_tugas = data.get('hasil_tugas')
        tgl_actual = data.get('tgl_actual')

        if hasil_tugas is None:
            return jsonify({'error': 'Missing hasil_tugas parameter'})

        # Mendapatkan waktu saat ini
        waktu_sekarang = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Using datetime.now() instead of datetime.now()

        # Update database dengan hasil_tugas, status, dan waktu_sekarang
        update_query = "UPDATE tahapan SET hasil_tahapan = %s, tgl_actual = %s, status = 'selesai', tgl_tugas = %s WHERE id_tahapan = %s"
        cursor.execute(update_query, (hasil_tugas, tgl_actual, waktu_sekarang, id_tahapan))
        conn.commit()

        # Mengembalikan respons sukses
        return jsonify({'message': 'Data updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        closeDb()
@app.route('/datadash/<int:id_pegawai>', methods=['GET'])
def get_project_details(id_pegawai):
    try:
        openDb()

        id_project_query = """
            SELECT id_project
            FROM struktur
            WHERE id_pegawai = %s
        """

        cursor.execute(id_project_query, (id_pegawai,))
        id_project_results = cursor.fetchall()

        projects = []

        for id_project_result in id_project_results:
            id_project = id_project_result[0]

            project_query = """
                SELECT p.id_project, p.nama_project, p.id_perusahaan, pr.nama_perusahaan, pr.alamat_perusahaan, pr.contact as contact_perusahaan, 
                p.id_vendor, v.nama_vendor, v.alamat_vendor, v.contact as contact_vendor
                FROM project p
                INNER JOIN perusahaan pr ON p.id_perusahaan = pr.id_perusahaan
                LEFT JOIN vendor v ON p.id_vendor = v.id_vendor
                WHERE p.id_project = %s
            """

            cursor.execute(project_query, (id_project,))
            project_result = cursor.fetchone()

            if project_result:
                project = {
                    'id_project': project_result[0],
                    'nama_project': project_result[1],
                    'id_perusahaan': project_result[2],
                    'nama_perusahaan': project_result[3],
                    'alamat_perusahaan': project_result[4],
                    'contact_perusahaan': project_result[5],
                    'id_vendor': project_result[6],
                    'nama_vendor': project_result[7],
                    'alamat_vendor': project_result[8],
                    'contact_vendor': project_result[9]
                }
                projects.append(project)

        closeDb()

        return jsonify(projects)

    except Exception as e:
        return jsonify({'error': str(e)})
@app.route('/addStruktur1/<int:id_project>', methods=['POST'])
def add_struktur1(id_project):
    try:
        openDb()
        
        # Dapatkan data pegawai dan nama_struktur dari permintaan
        data = request.get_json()
        id_pegawai = data.get('id_pegawai')
        nama_struktur = data.get('nama_struktur')
        
        if id_pegawai is None:
            closeDb()
            return jsonify({'error': 'Missing id_pegawai parameter'})
        
        if nama_struktur is None:
            closeDb()
            return jsonify({'error': 'Missing nama_struktur parameter'})

        pegawai_exists = False  # Menyimpan apakah ada setidaknya satu pegawai yang sudah ada dalam proyek

        # Loop melalui daftar pegawai dan tambahkan mereka ke tabel struktur
        for pegawai_id in id_pegawai:
            # Periksa apakah pegawai dengan ID tersebut sudah ada dalam proyek
            check_query = "SELECT * FROM struktur WHERE id_pegawai = %s AND id_project = %s"
            cursor.execute(check_query, (pegawai_id, id_project))
            struktur_exists = cursor.fetchone()

            if struktur_exists:
                # Pegawai sudah ada dalam proyek, tandai bahwa ada pegawai yang sudah ada
                pegawai_exists = True
            else:
                # Periksa apakah pegawai dengan ID tersebut ada dalam database pegawai
                check_query = "SELECT * FROM pegawai WHERE id_pegawai = %s"
                cursor.execute(check_query, (pegawai_id,))
                pegawai_exists_in_db = cursor.fetchone()

                if pegawai_exists_in_db:
                    # Tambahkan data struktur ke database dengan nama_struktur
                    insert_query = "INSERT INTO struktur (id_pegawai, id_project, nama_struktur) VALUES (%s, %s, %s)"
                    cursor.execute(insert_query, (pegawai_id, id_project, nama_struktur))
                    conn.commit()
                else:
                    # Pegawai dengan ID tersebut tidak ditemukan
                    closeDb()
                    return jsonify({'error': f'Pegawai dengan ID {pegawai_id} tidak ditemukan'})

        closeDb()

        if pegawai_exists:
            # Jika setidaknya satu pegawai sudah ada dalam proyek, kirim pesan kesalahan
            return jsonify({'message': 'Salah satu pegawai sudah ada dalam proyek'})
        
        response = {
            'message': 'Data struktur added successfully',
            'id_project': id_project,
            'id_pegawai': id_pegawai,
            'nama_struktur': nama_struktur
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})
    

@app.route('/tahapancoba', methods=['GET'])
def get_phasess():
    try:
        id_project = request.args.get('ID_project')

        if id_project is None:
            return jsonify({'error': 'Missing ID_project parameter'})

        id_project = int(id_project)

        openDb()

        phases_query = "SELECT * FROM tahapan WHERE ID_project = %s"

        cursor.execute(phases_query, (id_project,))
        phases_results = cursor.fetchall()

        phases = []

        for phase_result in phases_results:
            id_tahapan = phase_result[0]
            detail_query = "SELECT COUNT(*) FROM detailtahapan WHERE id_tahapan = %s"
            cursor.execute(detail_query, (id_tahapan,))
            detail_count = cursor.fetchone()[0]

            phase = {
                'id_tahapan': id_tahapan,
                'nama_tahapan': phase_result[1],
                'status': phase_result[2],
                'id_project': phase_result[3],
                'start_date': phase_result[4].strftime('%Y-%m-%d'),
                'Deadline': phase_result[5].strftime('%Y-%m-%d'),
                'hasil_tahapan': phase_result[6],
                'tgl_actual': phase_result[7],
                'tgl_tugas': phase_result[8],
                'detail_count': detail_count
            }

            if phase_result[2] == 'selesai':
                # Jika status tahapan adalah 'selesai', set progres menjadi 100
                progress = 100
            else:
                # Query untuk mendapatkan status dari tabel detailtahapan
                detail_status_query = "SELECT status FROM detailtahapan WHERE id_tahapan = %s"
                cursor.execute(detail_status_query, (id_tahapan,))
                detail_statuses = cursor.fetchall()

                # Inisialisasi progres menjadi 0
                progress = 0

                if detail_count > 0:
                    # Menghitung progres hanya jika setidaknya ada satu detail
                    completed_count = 0

                    for detail_status in detail_statuses:
                        if detail_status[0] == 'selesai':
                            completed_count += 1

                    if completed_count > 0:
                        progress = 100 * completed_count / detail_count

            phase['progres'] = progress

            phases.append(phase)

        closeDb()

        if phases:
            return jsonify(phases)
        else:
            return "No phases found."

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/admin/project', methods=['GET'])
def get_all_projectss():
    try:
        openDb()

        # Query untuk mendapatkan semua proyek beserta nama perusahaan dan nama vendor
        projects_query = """
        SELECT
            p.id_project,
            p.no_po,
            p.tgl_po,
            p.ID_perusahaan,
            pr.nama_perusahaan,
            p.nama_project,
            p.ID_Vendor,
            v.nama_vendor,
            p.start_project,
            p.deadline,
            p.status,
            p.selesai_project
        FROM project p
        LEFT JOIN perusahaan pr ON p.ID_perusahaan = pr.id_perusahaan
        LEFT JOIN vendor v ON p.ID_Vendor = v.id_vendor
        """
        cursor.execute(projects_query)
        project_results = cursor.fetchall()

        all_projects = []

        for project_result in project_results:
            id_project = project_result[0]
            no_po = project_result[1]
            tgl_po = project_result[2]
            ID_perusahaan = project_result[3]
            nama_perusahaan = project_result[4]
            nama_project = project_result[5]
            ID_Vendor = project_result[6]
            nama_vendor = project_result[7]
            start_project = project_result[8]
            deadline = project_result[9]
            status = project_result[10]
            selesai_project = project_result[11]

            # Query untuk mendapatkan anggota proyek dari tabel struktur
            anggota_query = "SELECT id_pegawai FROM struktur WHERE id_project = %s"
            cursor.execute(anggota_query, (id_project,))
            anggota_results = cursor.fetchall()

            anggota_list = []

            for anggota_result in anggota_results:
                id_pegawai = anggota_result[0]

                # Query untuk mendapatkan nama anggota dari tabel pegawai
                nama_pegawai_query = "SELECT nama FROM pegawai WHERE id_pegawai = %s"
                cursor.execute(nama_pegawai_query, (id_pegawai,))
                nama_pegawai = cursor.fetchone()

                if nama_pegawai:
                    anggota_list.append(nama_pegawai[0])

            # Menggabungkan anggota_list menjadi satu string dengan koma sebagai pemisah
            anggota_str = ", ".join(anggota_list)

            # Query untuk mendapatkan progres proyek
            progres_query = "SELECT * FROM tahapan WHERE ID_project = %s"
            cursor.execute(progres_query, (id_project,))
            progres_results = cursor.fetchall()

            progres_tahapan = []

            progres_hasil = 0  # Inisialisasi progres_hasil

            for progres_result in progres_results:
                id_tahapan = progres_result[0]
                detail_query = "SELECT COUNT(*) FROM detailtahapan WHERE id_tahapan = %s"
                cursor.execute(detail_query, (id_tahapan,))
                detail_count = cursor.fetchone()[0]

                if progres_result[2] == 'selesai':
                    # Jika status tahapan adalah 'selesai', set progres menjadi 100
                    progress = 100
                else:
                    # Query untuk mendapatkan status dari tabel detailtahapan
                    detail_status_query = "SELECT status FROM detailtahapan WHERE id_tahapan = %s"
                    cursor.execute(detail_status_query, (id_tahapan,))
                    detail_statuses = cursor.fetchall()

                    # Inisialisasi progres menjadi 0
                    progress = 0

                    if detail_count > 0:
                        # Menghitung progres hanya jika setidaknya ada satu detail
                        completed_count = 0

                        for detail_status in detail_statuses:
                            if detail_status[0] == 'selesai':
                                completed_count += 1

                        if completed_count > 0:
                            progress = 100 * completed_count / detail_count

                # Menambahkan progres ke progres_hasil
                progres_hasil += progress

                progres_tahapan.append(progress)

            # Menghitung rata-rata progres
            if len(progres_tahapan) > 0:
                    progres_hasil /= len(progres_tahapan)

            # Membatasi progres_hasil agar tidak melebihi 100
            progres_hasil = min(progres_hasil, 100)
            progres_hasil = progres_hasil // 1


            # Data proyek
            project_data = {
                'id_project': id_project,
                'no_po': no_po,
                'tgl_po': tgl_po,
                'ID_perusahaan': ID_perusahaan,
                'nama_perusahaan': nama_perusahaan,
                'nama_project': nama_project,
                'ID_Vendor': ID_Vendor,
                'nama_vendor': nama_vendor,
                'start_project': start_project,
                'deadline': deadline,
                'status': status,
                'selesai_project': selesai_project,
                'anggota': anggota_str,
                'progres_tahapan': progres_tahapan,
                'progres_hasil': progres_hasil,
            }

            all_projects.append(project_data)

        closeDb()

        return jsonify(all_projects)

    except Exception as e:
        return jsonify({'error': str(e)})



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
