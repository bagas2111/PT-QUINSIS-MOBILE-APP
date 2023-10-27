import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:sn_progress_dialog/sn_progress_dialog.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as path;

class DetailTahapanPage extends StatefulWidget {
  final int idTahapan;
  final String namaTahapan;

  DetailTahapanPage({
    required this.idTahapan,
    required this.namaTahapan,
  });

  @override
  _DetailTahapanPageState createState() => _DetailTahapanPageState();
}

class _DetailTahapanPageState extends State<DetailTahapanPage> {
  List<DetailTask> detailTasks = [];

  @override
  void initState() {
    super.initState();
    fetchDetailTasks();
  }

  Future<void> fetchDetailTasks() async {
    try {
      final response = await http.get(
        Uri.parse(
          'http://dev.quinsis.co.id/flask/api/detail?ID_tahapan=${widget.idTahapan}',
        ),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        setState(() {
          detailTasks = data.map((item) => DetailTask.fromJson(item)).toList();
        });
      } else {
        throw Exception('Failed to load detail tasks');
      }
    } catch (e) {
      print('Error fetching detail tasks: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar(context),
      body: Padding(
        padding: EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Detail Tasks',
              style: TextStyle(
                fontSize: 16,
                color: Colors.black,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 20),
            Expanded(
              child: ListView.builder(
                itemCount: detailTasks.length,
                itemBuilder: (context, index) {
                  final task = detailTasks[index];
                  return GestureDetector(
                    onTap: () {
                      _showDetailTahapanDialog(context, task);
                    },
                    child: Container(
                      margin: EdgeInsets.only(bottom: 10),
                      padding: EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            task.namaTugas.toUpperCase(),
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                          SizedBox(height: 8),
                          Text(task.descTugas),
                          SizedBox(height: 8),
                          Text(task.status),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showDetailTahapanDialog(BuildContext context, DetailTask task) {
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
            child: DetailTugasPage(
              task: task,
              onFileUploadSuccess: () {
                fetchDetailTasks();
                Navigator.pop(context);
              },
            ),
          ),
        );
      },
    );
  }

  AppBar appBar(BuildContext context) {
    return AppBar(
      title: Text(
        widget.namaTahapan,
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
        icon: Icon(Icons.arrow_back, color: Colors.black),
        onPressed: () {
          Navigator.pop(context);
        },
      ),
    );
  }
}

class DetailTugasPage extends StatelessWidget {
  final DetailTask task;
  final VoidCallback onFileUploadSuccess;

  DetailTugasPage({
    required this.task,
    required this.onFileUploadSuccess,
  });

  Future<String> getFileName(int idDetail) async {
    try {
      final response = await http.get(
        Uri.parse(
            'http://dev.quinsis.co.id/flask/api/hasilTugas?id_detail=$idDetail'),
      );

      if (response.statusCode == 200) {
        return response.body;
      } else {
        throw Exception('Failed to get filename');
      }
    } catch (e) {
      print('Error getting filename: $e');
      return '';
    }
  }

  void _showErrorDialog(BuildContext context) {
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
                  "ERROR",
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 30,
                  ),
                ),
                SizedBox(height: 10),
                Text(
                  "DATA GAGAL DIKIRIM!!!",
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

  void _showErrorDialogD(BuildContext context) {
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
                  "ERROR",
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 30,
                  ),
                ),
                SizedBox(height: 10),
                Text(
                  "DATA GAGAL DIDOWNLOAD",
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
      appBar: appBar(context),
      body: Padding(
        padding: EdgeInsets.all(10.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  task.namaTugas.toUpperCase(),
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            SizedBox(height: 20),
            Text(task.descTugas),
            SizedBox(height: 20),
            Text(task.status),
            SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: () async {
                    try {
                      FilePickerResult? result =
                          await FilePicker.platform.pickFiles();

                      if (result != null) {
                        File file = File(result.files.single.path!);

                        String filename = path.basename(file.path);

                        var request = http.MultipartRequest(
                          'POST',
                          Uri.parse(
                              'http://dev.quinsis.co.id/dashboard/uploadFile'),
                        );

                        request.files.add(
                          await http.MultipartFile.fromPath(
                            'file',
                            file.path,
                            filename: filename,
                          ),
                        );

                        request.fields['id_detail'] = task.idDetail.toString();

                        var response = await request.send();

                        if (response.statusCode == 200) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('File uploaded successfully'),
                            ),
                          );

                          onFileUploadSuccess();
                        } else {
                          print('File upload failed');
                          _showErrorDialog(context);
                        }
                      } else {
                        print('No file selected');
                      }
                    } catch (e) {
                      print('Error: $e');
                    }
                  },
                  child: Text("Upload Tugas"),
                ),
                Visibility(
                  visible: task.status != "belum selesai",
                  child: ElevatedButton(
                    onPressed: () async {
                      try {
                        final String filename =
                            await getFileName(task.idDetail);

                        if (filename.isNotEmpty) {
                          final response = await http.get(
                            Uri.parse(
                                'http://dev.quinsis.co.id/admin/download/$filename'),
                          );

                          if (response.statusCode == 200) {
                            final String savePath =
                                '/storage/emulated/0/Download/$filename';
                            final File file = File(savePath);

                            await file.writeAsBytes(response.bodyBytes);

                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content:
                                    Text('File downloaded to Downloads folder'),
                              ),
                            );
                            onFileUploadSuccess();
                          } else {
                            print('File download failed');
                            _showErrorDialogD(context);
                          }
                        } else {
                          print('Unable to retrieve filename');
                        }
                      } catch (e) {
                        print('Error: $e');
                      }
                    },
                    child: Text("Download File"),
                  ),
                )
              ],
            ),
          ],
        ),
      ),
    );
  }

  AppBar appBar(BuildContext context) {
    return AppBar(
      title: Text(
        task.namaTugas.toUpperCase(),
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
}

class DetailTask {
  final int idDetail;
  final int idTahapan;
  final String namaTugas;
  final String descTugas;
  final String status;

  DetailTask({
    required this.idDetail,
    required this.idTahapan,
    required this.namaTugas,
    required this.descTugas,
    required this.status,
  });

  factory DetailTask.fromJson(Map<String, dynamic> json) {
    return DetailTask(
      idDetail: json['id_detail'],
      idTahapan: json['id_tahapan'],
      namaTugas: json['nama_tugas'],
      descTugas: json['desc_tugas'],
      status: json['status'],
    );
  }
}
