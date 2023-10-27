import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '/pages/home.dart';
import 'package:shared_preferences/shared_preferences.dart';
import './storage_utils.dart';
// Import the storage functions

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<SharedPreferences>(
      future: SharedPreferences.getInstance(),
      builder: (context, snapshot) {
        final idPegawai = snapshot.data?.getString('id_pegawai');
        final namaUser = snapshot.data?.getString('nama');

        if (idPegawai != null) {
          return MaterialApp(
            debugShowCheckedModeBanner: false,
            home: Home(
              idPegawai: idPegawai,
              namaUser: namaUser,
            ),
          );
        } else {
          return MaterialApp(
            debugShowCheckedModeBanner: false,
            home: Login(),
          );
        }
      },
    );
  }
}

class Login extends StatefulWidget {
  @override
  _LoginState createState() => _LoginState();
}

class _LoginState extends State<Login> {
  String msgError = "";
  TextEditingController _username = TextEditingController();
  TextEditingController _password = TextEditingController();

  Future<void> getApi(
      BuildContext context, String username, String password) async {
    final response = await http.post(
      Uri.parse('http://dev.quinsis.co.id/flask/api/login'), // Update the URL
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "username": username,
        "password": password,
      }),
    );

    print('Response Status Code: ${response.statusCode}');
    print('Response Body: ${response.body}');

    final data = jsonDecode(response.body);

    if (response.statusCode == 200 && data['msg'] == 'DATA ADA') {
      SharedPreferences prefs = await SharedPreferences.getInstance();

      prefs.setString('id_pegawai', data['id_pegawai'].toString());
      prefs.setString('nama', data['nama'].toString());

      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (context) => Home(
            idPegawai: data['id_pegawai'].toString(),
            namaUser: data['nama'].toString(),
          ),
        ),
      );
    } else {
      _showErrorDialog();
    }
  }

  void _showErrorDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20.0),
          ),
          child: Container(
            padding: EdgeInsets.all(20.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  "Error",
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 30,
                  ),
                ),
                SizedBox(height: 10),
                Text(
                  "Username or password is incorrect.",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 15,
                  ),
                ),
                SizedBox(height: 20),
                TextButton(
                  child: Text("Close"),
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(10.0),
        child: SafeArea(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextFormField(
                controller: _username,
                decoration: InputDecoration(
                  labelText: "username",
                  border: OutlineInputBorder(),
                  suffixIcon: Icon(Icons.person_outline),
                ),
              ),
              SizedBox(
                height: 15,
              ),
              TextFormField(
                controller: _password,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: "Password",
                  border: OutlineInputBorder(),
                  suffixIcon: Icon(Icons.lock),
                ),
              ),
              SizedBox(
                height: 45,
              ),
              OutlinedButton.icon(
                onPressed: () {
                  getApi(context, _username.text, _password.text);
                },
                icon: Icon(
                  Icons.login,
                  size: 18,
                ),
                label: Text("Login"),
              )
            ],
          ),
        ),
      ),
    );
  }
}
