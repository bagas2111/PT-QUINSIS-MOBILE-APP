import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'dart:typed_data'; // Import the typed_data library for Uint8List
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:image/image.dart' as img;
import 'package:permission_handler/permission_handler.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geolocator_android/geolocator_android.dart';
import 'package:geolocator_apple/geolocator_apple.dart';
import 'package:detect_fake_location/detect_fake_location.dart';

class CameraScreen extends StatefulWidget {
  final String idPegawai;
  File? _image;

  CameraScreen({required this.idPegawai});

  @override
  _CameraScreenState createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  File? _image;

  Future<void> _pickImage(ImageSource source) async {
    final pickedFile = await ImagePicker().pickImage(source: source);

    setState(() {
      if (pickedFile != null) {
        _image = File(pickedFile.path);
      }
    });
  }

  Future<void> _uploadImage() async {
    if (_image == null) return;

    final rawImage = img.decodeImage(_image!.readAsBytesSync())!;

    final double targetWidth = 800;
    final double scaleFactor = targetWidth / rawImage.width;
    final int targetHeight = (rawImage.height * scaleFactor).round();
    bool isFakeLocation = await DetectFakeLocation().detectFakeLocation();

    final resizedImage = img.copyResize(rawImage,
        width: targetWidth.toInt(), height: targetHeight);

    Uint8List compressedImage;
    int quality = 100;

    while (true) {
      compressedImage = img.encodeJpg(resizedImage, quality: quality);
      if (compressedImage.length <= 50 * 1024 || quality <= 10) {
        break;
      }
      quality -= 10;
    }
    var status = await Permission.location.request();
    if (status.isDenied) {
      // Handle denied permission
      return;
    }
    final position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.best,
    );

    String base64Image = base64Encode(compressedImage);
    double latitude = position.latitude;
    double longitude = position.longitude;

    String location = '$latitude, $longitude';
    if (await DetectFakeLocation().detectFakeLocation()) {
      // Handle the case of a detected fake location
      showDialog(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: Text("Fake Location Detected"),
            content: Text("Your current location appears to be fake."),
            actions: <Widget>[
              TextButton(
                child: Text("OK"),
                onPressed: () {
                  Navigator.of(context).pop();
                },
              ),
            ],
          );
        },
      );
      return;
    }

    final response = await http.post(
      Uri.parse('http://192.168.1.14:5000/uploadphoto'),
      body: jsonEncode({
        'id_pegawai': widget.idPegawai,
        'image': base64Image,
        'location': location, // Add the location data
      }),
      headers: {'Content-Type': 'application/json'},
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Camera'),
      ),
      body: Column(
        children: [
          _image != null
              ? Image.file(
                  _image!,
                  height: 200,
                )
              : Container(),
          ElevatedButton(
            onPressed: () => _pickImage(ImageSource.camera),
            child: Text('Ambil Foto'),
          ),
          ElevatedButton(
            onPressed: _uploadImage,
            child: Text('Unggah Foto'),
          ),
        ],
      ),
    );
  }
}
