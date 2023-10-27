import 'package:shared_preferences/shared_preferences.dart';

Future<void> saveUserData(String idPegawai) async {
  SharedPreferences prefs = await SharedPreferences.getInstance();
  await prefs.setString('id_pegawai', idPegawai);
}

Future<String?> getUserData() async {
  SharedPreferences prefs = await SharedPreferences.getInstance();
  return prefs.getString('id_pegawai');
}

Future<void> removeUserData() async {
  SharedPreferences prefs = await SharedPreferences.getInstance();
  await prefs.remove('id_pegawai');
}
