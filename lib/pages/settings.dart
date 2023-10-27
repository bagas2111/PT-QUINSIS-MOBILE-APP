import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:http/http.dart' as http;
import './home.dart';
import '../storage_utils.dart';
import 'package:app_attendance/main.dart';

class Settings extends StatefulWidget {
  final String idPegawai;

  Settings({required this.idPegawai});

  @override
  _SettingsState createState() => _SettingsState();
}

class _SettingsState extends State<Settings> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passController = TextEditingController();
  final _namePerusahaanController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchName();
  }

  Future<void> _fetchName() async {
    try {
      final response = await http.get(
        Uri.parse(
            'http://dev.quinsis.co.id/flask/api/namaperusahaan?id_pegawai=${widget.idPegawai}'),
      );

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        final name = responseData['nama'];
        _nameController.text = name;
        final username = responseData['username'];
        _usernameController.text = username;
        final perusahaan = responseData['nama_perusahaan'];
        _namePerusahaanController.text = perusahaan;
      } else {
        print('Failed to fetch name from the API');
      }
    } catch (e) {
      print('Error fetching data: $e');
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _usernameController.dispose();
    _passController.dispose();
    _namePerusahaanController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'User Settings',
      home: UserSettings(
        formKey: _formKey,
        nameController: _nameController,
        usernameController: _usernameController,
        passController: _passController,
        namePerusahaanController: _namePerusahaanController,
        onEditPasswordPressed: () {
          showEditPasswordPopup(context, widget.idPegawai);
        },
      ),
    );
  }
}

class UserSettings extends StatelessWidget {
  final GlobalKey<FormState> formKey;
  final TextEditingController nameController;
  final TextEditingController usernameController;

  final TextEditingController passController;
  final VoidCallback onEditPasswordPressed;
  final TextEditingController namePerusahaanController;

  UserSettings({
    required this.formKey,
    required this.nameController,
    required this.usernameController,
    required this.passController,
    required this.onEditPasswordPressed,
    required this.namePerusahaanController,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      bottomNavigationBar: bottomNavigationBar(context),
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        key: formKey,
        child: Column(
          children: [
            SizedBox(
              height: 200,
            ),
            TextField(
              controller: usernameController,
              readOnly: true,
              enabled: false,
              decoration: InputDecoration(
                labelText: 'Username:',
                suffixIcon: Padding(
                  padding: const EdgeInsetsDirectional.only(
                    end: 12.0,
                  ),
                  child: SvgPicture.asset(
                    'assets/icons/user-svgrepo-com.svg',
                    width: 10,
                    height: 10,
                  ),
                ),
              ),
            ),
            SizedBox(
              height: 20,
            ),
            TextField(
              controller: nameController,
              readOnly: true,
              enabled: false,
              decoration: InputDecoration(
                labelText: 'Name:',
                suffixIcon: Padding(
                  padding: const EdgeInsetsDirectional.only(
                    end: 12.0,
                  ),
                  child: SvgPicture.asset(
                    'assets/icons/user-svgrepo-com.svg',
                    width: 10,
                    height: 10,
                  ),
                ),
              ),
            ),
            SizedBox(
              height: 20,
            ),
            InkWell(
              onTap: onEditPasswordPressed,
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: 'Password:',
                  suffixIcon: Padding(
                    padding: const EdgeInsetsDirectional.only(
                      end: 12.0,
                    ),
                    child: SvgPicture.asset(
                      'assets/icons/password-minimalistic-svgrepo-com.svg',
                      width: 10,
                      height: 10,
                    ),
                  ),
                ),
                child: Text(
                  '********', // Display masked or hidden password
                  style: TextStyle(color: Colors.grey), // Customize the style
                ),
              ),
            ),
            SizedBox(
              height: 20,
            ),
            SizedBox(
              height: 20,
            ),
            Center(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  GestureDetector(
                    onTap: () {
                      showLogoutConfirmationDialog(context);
                    },
                    child: Column(
                      children: <Widget>[
                        Text(
                          'LOGOUT',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ), // Tambahkan jarak antara teks dan tombol
                      ],
                    ),
                  ),
                  GestureDetector(
                    onTap: () {
                      showLogoutConfirmationDialog(context);
                    },
                    child: SvgPicture.asset(
                      'assets/icons/log-out-svgrepo-com.svg',
                      height: 30,
                      width: 30,
                    ),
                  ),
                ],
              ),
            )
          ],
        ),
      ),
    );
  }
}

void showEditPasswordPopup(BuildContext context, String idPegawai) {
  showDialog(
    context: context,
    builder: (BuildContext context) {
      return Dialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12.0),
        ),
        child: Container(
          constraints: BoxConstraints(maxWidth: 300, maxHeight: 300),
          padding: EdgeInsets.all(10), // Set padding as required
          child: EditPasswordPage(idPegawai: idPegawai),
        ),
      );
    },
  );
}

Future<void> showLogoutConfirmationDialog(BuildContext context) async {
  return showDialog<void>(
    context: context,
    builder: (BuildContext context) {
      return AlertDialog(
        title: Text('Logout'),
        content: Text('Are you sure you want to logout?'),
        actions: <Widget>[
          TextButton(
            child: Text('Cancel'),
            onPressed: () {
              Navigator.of(context).pop(); // Close the dialog
            },
          ),
          TextButton(
            child: Text('Logout'),
            onPressed: () async {
              Navigator.of(context).pop(); // Close the dialog
              removeUserData(); // Logout: Remove stored data
              Navigator.pushReplacement(
                // Navigate back to login page
                context,
                MaterialPageRoute(builder: (context) => Login()),
              );
            },
          ),
        ],
      );
    },
  );
}

class EditPasswordPage extends StatefulWidget {
  final String idPegawai;

  EditPasswordPage({required this.idPegawai});

  @override
  _EditPasswordPageState createState() => _EditPasswordPageState();
}

class _EditPasswordPageState extends State<EditPasswordPage> {
  final TextEditingController _newPasswordController = TextEditingController();

  Future<void> _updatePassword() async {
    final url = Uri.parse(
        'http://dev.quinsis.co.id/flask/api/editpassword?id_pegawai=${widget.idPegawai}');
    final requestBody = {
      "new_password": _newPasswordController.text,
    };

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode(requestBody),
      );

      if (response.statusCode == 200) {
        // Password updated successfully
        // You can implement further actions here, such as showing a success message.
        Navigator.pop(context);
      } else {
        // Password update failed
        // You can implement further error handling here, such as showing an error message.
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Failed to update password. Please try again.'),
        ));
      }
    } catch (e) {
      print('Error updating password: $e');
      // Handle error
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar(context),
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        child: Column(
          children: [
            TextField(
              controller: _newPasswordController,
              decoration: InputDecoration(
                labelText: 'New Password:',
                suffixIcon: Padding(
                  padding: const EdgeInsetsDirectional.only(
                    end: 12.0,
                  ),
                  child: SvgPicture.asset(
                    'assets/icons/password-minimalistic-svgrepo-com.svg',
                    width: 10,
                    height: 10,
                  ),
                ),
              ),
            ),
            SizedBox(
              height: 10,
            ),
            ElevatedButton(
              onPressed: _updatePassword,
              child: Text('Save Password'),
            ),
            SizedBox(
              height: 20,
            ),
          ],
        ),
      ),
    );
  }
}

AppBar appBar(BuildContext context) {
  return AppBar(
    title: Text(
      'Edit Password',
      style: TextStyle(
        color: Colors.black,
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
    ),
    backgroundColor: Colors.white,
    elevation: 0.0,
    centerTitle: true,
    leading: IconButton(
      icon: Icon(Icons.close, color: Colors.black),
      onPressed: () {
        Navigator.pop(context);
      },
    ),
  );
}

BottomNavigationBar bottomNavigationBar(BuildContext context) {
  return BottomNavigationBar(
    backgroundColor: Colors.white,
    items: const <BottomNavigationBarItem>[
      BottomNavigationBarItem(
        icon: Icon(Icons.home),
        label: 'Home',
      ),
      BottomNavigationBarItem(
        icon: Icon(Icons.account_circle),
        label: 'Profile',
      ),
    ],
    selectedItemColor: Colors.blue, // Customize the selected item color
    unselectedItemColor: Colors.grey, // Customize the unselected item color
    currentIndex: 1, // Set the current index based on the selected tab
    onTap: (int index) {
      if (index == 0) {
        Navigator.of(context, rootNavigator: true).pop(context);
      }
    },
  );
}







// Future<void> logout() async {
//   final sharedPreferences = await SharedPreferences.getInstance();
//   sharedPreferences.remove('authToken');
//   // Navigate back to the Login screen
//   Navigator.of(context).pushReplacement(
//     MaterialPageRoute(builder: (context) => Login()),
//   );
// }
