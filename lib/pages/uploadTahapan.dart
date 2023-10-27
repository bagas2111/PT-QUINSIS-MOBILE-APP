// import 'package:flutter/material.dart';
// import 'package:http/http.dart' as http;
// import 'dart:convert';
// import 'package:intl/intl.dart';
// import 'package:file_picker/file_picker.dart';
// import 'dart:io';
// import './detail.dart';

// class ProjectDetailPage extends StatefulWidget {
//   final int projectId;
//   final String namaProject;

//   ProjectDetailPage({required this.projectId, required this.namaProject});

//   @override
//   _ProjectDetailPageState createState() => _ProjectDetailPageState();
// }

// class _ProjectDetailPageState extends State<ProjectDetailPage> {
//   List<Phase> phases = [];

//   void _navigateToDetailPage(int idTahapan) {
//     Navigator.push(
//       context,
//       MaterialPageRoute(
//         builder: (context) => DetailTahapanPage(idTahapan: idTahapan),
//       ),
//     );
//   }

//   @override
//   void initState() {
//     super.initState();
//     fetchPhases();
//   }

//   void refreshPage() {
//     fetchPhases(); // Atau perbarui data lain yang diperlukan
//   }

//   Future<void> fetchPhases() async {
//     try {
//       final response = await http.get(
//         Uri.parse(
//           'http://192.168.11.60:5000/tahapan?ID_project=${widget.projectId}',
//         ),
//       );

//       if (response.statusCode == 200) {
//         final List<dynamic> data = jsonDecode(response.body);
//         setState(() {
//           phases = data.map((item) => Phase.fromJson(item)).toList();
//         });
//       } else {
//         throw Exception('Failed to load phases');
//       }
//     } catch (e) {
//       print('Error fetching phases: $e');
//     }
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: appBar(context),
//       body: Padding(
//         padding: EdgeInsets.all(20.0),
//         child: Column(
//           crossAxisAlignment: CrossAxisAlignment.start,
//           children: [
//             Text(
//               'Project Phases',
//               style: TextStyle(
//                 fontSize: 16,
//                 color: Colors.black,
//                 fontWeight: FontWeight.bold,
//               ),
//             ),
//             SizedBox(height: 20),
//             Expanded(
//               child: ListView.builder(
//                 itemCount: phases.length,
//                 itemBuilder: (context, index) {
//                   final phase = phases[index];
//                   return GestureDetector(
//                     onTap: () {
//                       _navigateToDetailPage(phase.idTahapan);
//                     },
//                     child: Container(
//                       margin: EdgeInsets.only(bottom: 10),
//                       padding: EdgeInsets.all(10),
//                       decoration: BoxDecoration(
//                         border: Border.all(color: Colors.grey),
//                         borderRadius: BorderRadius.circular(20),
//                       ),
//                       child: Row(
//                         mainAxisAlignment: MainAxisAlignment.spaceBetween,
//                         children: [
//                           Column(
//                             crossAxisAlignment: CrossAxisAlignment.start,
//                             children: [
//                               Text(
//                                 phase.namaTahapan.toUpperCase(),
//                                 style: TextStyle(fontWeight: FontWeight.bold),
//                               ),
//                               SizedBox(height: 8),
//                               Text('status: ${phase.status}'),
//                               SizedBox(height: 15),
//                               RichText(
//                                 text: TextSpan(
//                                   children: [
//                                     TextSpan(
//                                       text: 'Deadline: ',
//                                       style: TextStyle(
//                                         color: Colors.black,
//                                       ),
//                                     ),
//                                     TextSpan(
//                                       text: phase.deadline,
//                                       style: TextStyle(
//                                         color: Colors.red,
//                                       ),
//                                     ),
//                                   ],
//                                 ),
//                               ),
//                             ],
//                           ),
//                           Column(
//                             mainAxisAlignment: MainAxisAlignment.center,
//                             crossAxisAlignment: CrossAxisAlignment.center,
//                             children: [
//                               ElevatedButton(
//                                 onPressed: () {
//                                   showDialog(
//                                     context: context,
//                                     builder: (BuildContext context) {
//                                       return SmallerAlertDialog(
//                                           idTahapan: phase.idTahapan,
//                                           namaTahapan: phase.namaTahapan,
//                                           refreshCallback: refreshPage);
//                                     },
//                                   );
//                                 },
//                                 child: Text("Upload Tugas"),
//                               ),
//                               Visibility(
//                                 visible: phase.hasil != null &&
//                                     phase.hasil.isNotEmpty,
//                                 child: ElevatedButton(
//                                   onPressed: () async {
//                                     try {
//                                       final String filename = phase.hasil;
//                                       if (filename.isNotEmpty) {
//                                         final response = await http.get(
//                                           Uri.parse(
//                                               'http://192.168.11.60:8080/admin/download/$filename'),
//                                         );
//                                         if (response.statusCode == 200) {
//                                           final String savePath =
//                                               '/storage/emulated/0/Download/$filename';
//                                           final File file = File(savePath);
//                                           await file
//                                               .writeAsBytes(response.bodyBytes);
//                                           ScaffoldMessenger.of(context)
//                                               .showSnackBar(
//                                             SnackBar(
//                                               content: Text(
//                                                   'File downloaded to Downloads folder'),
//                                             ),
//                                           );
//                                         } else {
//                                           print('File download failed');
//                                         }
//                                       } else {
//                                         print('Unable to retrieve filename');
//                                       }
//                                     } catch (e) {
//                                       print('Error: $e');
//                                     }
//                                   },
//                                   child: Text('Download hasil'),
//                                 ),
//                               ),
//                             ],
//                           ),
//                         ],
//                       ),
//                     ),
//                   );
//                 },
//               ),
//             ),
//           ],
//         ),
//       ),
//     );
//   }

//   AppBar appBar(BuildContext context) {
//     return AppBar(
//       title: Text(
//         '${widget.namaProject}',
//         style: TextStyle(
//           color: Colors.black,
//           fontSize: 18,
//           fontWeight: FontWeight.bold,
//         ),
//       ),
//       backgroundColor: Colors.white,
//       elevation: 0.0,
//       centerTitle: true,
//       leading: IconButton(
//         icon: Icon(Icons.arrow_back, color: Colors.black),
//         onPressed: () {
//           Navigator.pop(context);
//         },
//       ),
//     );
//   }
// }

// class Phase {
//   final int idTahapan;
//   final String namaTahapan;
//   final String status;
//   final int idProject;
//   final String deadline;
//   final String hasil;

//   Phase({
//     required this.idTahapan,
//     required this.namaTahapan,
//     required this.status,
//     required this.idProject,
//     required this.deadline,
//     required this.hasil,
//   });

//   factory Phase.fromJson(Map<String, dynamic> json) {
//     return Phase(
//       idTahapan: json['id_tahapan'] ?? 0,
//       namaTahapan: json['nama_tahapan'] ?? "",
//       status: json['status'] ?? "",
//       idProject: json['ID_project'] ?? 0,
//       deadline: json['Deadline'] ?? "",
//       hasil: json['hasil_tahapan'] ?? "",
//     );
//   }
// }

// class UploadTahapanPage extends StatefulWidget {
//   final int idTahapan;
//   final String namaTahapan;

//   final Function() refreshCallback;

//   UploadTahapanPage({
//     required this.idTahapan,
//     required this.refreshCallback,
//     required this.namaTahapan,
//   });

//   @override
//   _UploadTahapanPageState createState() => _UploadTahapanPageState();
// }

// class _UploadTahapanPageState extends State<UploadTahapanPage> {
//   TextEditingController dateController = TextEditingController();
//   String? filePath;

//   Future<void> _pickFile() async {
//     FilePickerResult? result = await FilePicker.platform.pickFiles();

//     if (result != null) {
//       setState(() {
//         filePath = result.files.single.path;
//       });
//     }
//   }

//   Future<void> _submitData() async {
//     if (filePath == null || dateController.text.isEmpty) {
//       // Handle validation or show an error message.
//       return;
//     }

//     final url = Uri.parse("http://192.168.11.60:8080/admin/uploadFile");
//     final request = http.MultipartRequest("POST", url);
//     request.fields['id_tahapan'] = widget.idTahapan.toString();
//     request.fields['tgl_actual'] = dateController.text;

//     final file = await http.MultipartFile.fromPath(
//         'file', filePath!); // Use ! to assert non-nullability
//     request.files.add(file);

//     try {
//       final response = await request.send();
//       if (response.statusCode == 200) {
//         // Handle a successful response (if needed).
//         print("Upload successful");

//         // Tambahkan pembaruan untuk merefresh halaman
//         Navigator.pop(context); // Tutup dialog
//         ScaffoldMessenger.of(context).showSnackBar(
//           SnackBar(
//             content: Text('File uploaded successfully'),
//           ),
//         );
//         widget.refreshCallback(); // Panggil callback untuk merefresh halaman

//         // Lakukan pembaruan halaman, contohnya dengan memanggil fetch data kembali
//         // atau menggunakan pendekatan lain sesuai dengan kebutuhan Anda.
//       } else {
//         // Handle an error response (if needed).
//         print("Upload failed with status code ${response.statusCode}");
//       }
//     } catch (e) {
//       // Handle network or other errors.
//       print("Error: $e");
//     }
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Container(
//       width: 300,
//       padding: const EdgeInsets.all(20),
//       child: Column(
//         mainAxisSize: MainAxisSize.min,
//         crossAxisAlignment: CrossAxisAlignment.start,
//         children: [
//           Text("ID Tahapan: ${widget.idTahapan}"),
//           TextField(
//             controller: dateController,
//             decoration: const InputDecoration(
//               icon: Icon(Icons.calendar_today),
//               labelText: "Enter Date",
//             ),
//             readOnly: true,
//             onTap: () async {
//               DateTime? pickedDate = await showDatePicker(
//                 context: context,
//                 initialDate: DateTime.now(),
//                 firstDate: DateTime(2000),
//                 lastDate: DateTime(2101),
//               );

//               if (pickedDate != null) {
//                 String formattedDate =
//                     DateFormat('yyyy-MM-dd').format(pickedDate);
//                 setState(() {
//                   dateController.text = formattedDate;
//                 });
//               } else {
//                 print("Date is not selected");
//               }
//             },
//           ),
//           Container(
//             width: double.infinity,
//             child: ElevatedButton(
//               onPressed: () => _pickFile(),
//               child: Text("tambah File dokumen"),
//             ),
//           ),
//           if (filePath != null) Text("File Path: $filePath"),
//           Row(
//             children: [
//               Container(
//                 width: 125.0,
//                 child: ElevatedButton(
//                   onPressed: () => _submitData(),
//                   child: Text("Submit"),
//                 ),
//               ),
//               SizedBox(width: 10.0), // Menambahkan spasi sebesar 10.0

//               Container(
//                 width: 125.0,
//                 child: ElevatedButton(
//                   onPressed: () {
//                     Navigator.of(context).pop();
//                   },
//                   child: Text('Cancel'),
//                 ),
//               ),
//             ],
//           )
//         ],
//       ),
//     );
//   }
// }

// class SmallerAlertDialog extends StatelessWidget {
//   final int idTahapan;
//   final String namaTahapan;

//   final Function() refreshCallback;

//   SmallerAlertDialog(
//       {required this.idTahapan,
//       required this.namaTahapan,
//       required this.refreshCallback});

//   @override
//   Widget build(BuildContext context) {
//     return Dialog(
//       shape: RoundedRectangleBorder(
//         borderRadius: BorderRadius.circular(12.0),
//       ),
//       child: UploadTahapanPage(
//           idTahapan: idTahapan,
//           namaTahapan: namaTahapan,
//           refreshCallback: refreshCallback),
//     );
//   }
// }
