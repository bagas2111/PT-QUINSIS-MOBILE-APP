from flask import Flask, request, jsonify
import pymysql.cursors, os
import base64
import hashlib

application = Flask(__name__)

conn = cursor = None

# Fungsi koneksi database
def openDb():
    global conn, cursor
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",  # Provide the password if applicable
        database="Haidar"
    )
    cursor = conn.cursor()

def closeDb():
    global conn, cursor
    if cursor:
        cursor.close()
    if conn:
        conn.close()

@application.route('/login', methods=['POST'])
def login():
    openDb()
    
    data = request.get_json()
    nama_user = data.get('nama_user')
    password = data.get('password')
    
    if nama_user is None or password is None:
        closeDb()
        return jsonify({'error': 'Missing nama_user or password'})

    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    query = f"SELECT * FROM user WHERE nama_user='{nama_user}' AND password='{hashed_password}'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    if result:
        id_pegawai = result[3]
        
        # Fetch tipe_pegawai from pegawai table using id_pegawai
        query_pegawai = f"SELECT tipe_pegawai,nama_pegawai FROM pegawai WHERE id_pegawai='{id_pegawai}'"
        cursor.execute(query_pegawai)
        pegawai_result = cursor.fetchone()
        
        if pegawai_result:
            tipe_pegawai = pegawai_result[0]
            nama_pegawai = pegawai_result[1]
        else:
            tipe_pegawai = "Unknown"  # Default value if tipe_pegawai is not found
        
        response = {
            'msg': 'DATA ADA',
            'nama_user': nama_pegawai,
            'id_pegawai': id_pegawai,
            'tipe_pegawai': tipe_pegawai
        }
    else:
        response = {
            'msg': 'DATA TIDAK ADA'
        }
    
    closeDb()
    
    return jsonify(response)


@application.route('/namaperusahaan', methods=['GET'])
def get_nama_perusahaan():
    try:
        id_pegawai = request.args.get('id_pegawai')

        if id_pegawai is None:
            return jsonify({'error': 'Missing id_pegawai parameter'})

        id_pegawai = int(id_pegawai)

        openDb()

        get_perusahaan_query = """
            SELECT pr.nama_perusahaan, pg.nama_pegawai
            FROM pegawai pg
            JOIN perusahaan pr ON pg.id_perusahaan = pr.id_perusahaan
            WHERE pg.id_pegawai = %s
        """

        cursor.execute(get_perusahaan_query, (id_pegawai,))
        perusahaan_result = cursor.fetchone()

        closeDb()

        if perusahaan_result:
            return jsonify({
                'nama_perusahaan': perusahaan_result[0],
                'nama':perusahaan_result[1]

                            })
        else:
            return jsonify({'error': 'Employee not found or company not found.'})

    except Exception as e:
        return jsonify({'error': str(e)})


@application.route('/editpassword', methods=['POST'])
def edit_password():
    openDb()
    
    id_pegawai = request.args.get('id_pegawai')
    new_password = request.json.get('new_password')
    
    if id_pegawai is None or new_password is None:
        closeDb()
        return jsonify({'error': 'Missing id_pegawai or new_password'})

    hashed_password = hashlib.md5(new_password.encode()).hexdigest()
    
    update_query = f"UPDATE user SET password = '{hashed_password}' WHERE id_pegawai = {id_pegawai}"
    
    try:
        cursor.execute(update_query)
        conn.commit()
        response = {'msg': 'Password updated successfully'}
    except Exception as e:
        conn.rollback()
        response = {'error': str(e)}
    
    closeDb()
    
    return jsonify(response)


@application.route('/uploadphoto', methods=['POST'])
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


if __name__ == '__main__':
    application.run(debug=True)


# # flask run -h IP
# contoh: flask run -h 192.168.1.14


@application.route('/addStruktur/<int:id_project>', methods=['POST'])
def add_struktur(id_project):
    try:
        openDb()
        
        # Dapatkan data pegawai dari permintaan
        data = request.get_json()
        id_pegawai = data.get('id_pegawai')
        
        if id_pegawai is None:
            closeDb()
            return jsonify({'error': 'Missing id_pegawai parameter'})

        # Loop melalui daftar pegawai dan tambahkan mereka ke tabel struktur
        for pegawai_id in id_pegawai:
            # Periksa apakah pegawai dengan ID tersebut ada dalam database
            check_query = "SELECT * FROM pegawai WHERE id_pegawai = %s"
            cursor.execute(check_query, (pegawai_id,))
            pegawai_exists = cursor.fetchone()

            if pegawai_exists:
                # Tambahkan data struktur ke database
                insert_query = "INSERT INTO struktur (id_pegawai, id_project) VALUES (%s, %s)"
                cursor.execute(insert_query, (pegawai_id, id_project))
                conn.commit()
            else:
                # Pegawai dengan ID tersebut tidak ditemukan
                closeDb()
                return jsonify({'error': f'Pegawai dengan ID {pegawai_id} tidak ditemukan'})

        closeDb()
        
        response = {
            'message': 'Data struktur added successfully',
            'id_project': id_project,
            'id_pegawai': id_pegawai
        }
        return jsonify(response)
    except Exception as e:
        closeDb()
        return jsonify({'error': str(e)})