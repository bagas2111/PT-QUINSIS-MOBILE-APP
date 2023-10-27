import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import './settings.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import './tahapan.dart';

class Home extends StatefulWidget {
  final String idPegawai;
  final String? namaUser;

  Home({required this.idPegawai, this.namaUser});

  @override
  _HomeState createState() => _HomeState();
}

class _HomeState extends State<Home> {
  late String currentTime = '';
  int totalProjects = 0;

  @override
  void initState() {
    super.initState();
    _startClock();
  }

  void _startClock() {
    Timer.periodic(Duration(seconds: 1), (timer) {
      _updateTime();
    });
  }

  void _updateTime() {
    setState(() {
      currentTime = DateFormat('HH:mm').format(DateTime.now());
    });
  }

  void updateTotalProjects(int count) {
    setState(() {
      totalProjects = count;
    });
  }

  @override
  Widget build(BuildContext context) {
    var now = DateTime.now();
    var date = DateFormat('EEE, d MMM').format(now);
    return Scaffold(
      bottomNavigationBar: bottomNavigationBar(context),
      backgroundColor: Colors.white,
      body: Padding(
        padding: EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 20,
            ),
            Center(
              child: Text(
                'Welcome, ${widget.namaUser}',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.black,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            SizedBox(height: 20),
            Container(
              height: 90,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20.0),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Color(0xFF315AA8),
                    Color.fromRGBO(285, 115, 212, 0.46),
                  ],
                  stops: [0.0, 1.0],
                  transform: GradientRotation(-90),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Card(
                      shape: RoundedRectangleBorder(
                        side: BorderSide(
                          color: Colors.grey,
                        ),
                        borderRadius: BorderRadius.circular(20.0),
                      ),
                      color:
                          Colors.transparent, // Set card color to transparent
                      child: Padding(
                        padding:
                            EdgeInsets.symmetric(horizontal: 15, vertical: 15),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '$currentTime',
                                  style: TextStyle(
                                    fontSize: 32,
                                    color: Colors
                                        .white, // Change text color to white
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                Text(
                                  '$date',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors
                                        .white, // Change text color to white
                                  ),
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  'Total Projects: $totalProjects',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors
                                        .white, // Change text color to white
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(height: 20),
            Text(
              'Project',
              style: TextStyle(
                fontSize: 16,
                color: Colors.black,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(
              height: 423.42,
              child: ProjectListPage(
                idPegawai: widget.idPegawai,
                updateTotalProjects: updateTotalProjects,
              ),
            ),
          ],
        ),
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
      currentIndex: 0, // Set the current index based on the selected tab
      onTap: (int index) {
        if (index == 1) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => Settings(idPegawai: widget.idPegawai),
            ),
          );
        }
      },
    );
  }
}

class ProjectListPage extends StatefulWidget {
  final String idPegawai;
  final Function(int) updateTotalProjects;

  ProjectListPage({
    required this.idPegawai,
    required this.updateTotalProjects,
  });

  @override
  _ProjectListPageState createState() => _ProjectListPageState();
}

class _ProjectListPageState extends State<ProjectListPage> {
  List<Project> projects = [];
  bool isProjectListEmpty = false;

  void _navigateToDetailPage(int projectId, String namaProject) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ProjectDetailPage(
          projectId: projectId,
          namaProject:
              namaProject, // Mengirimkan nama_project ke ProjectDetailPage
        ),
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    fetchProjects();
  }

  Future<void> fetchProjects() async {
    final response = await http.get(
      Uri.parse(
        'http://dev.quinsis.co.id/flask/api/projects?id_pegawai=${widget.idPegawai}',
      ),
    );

    if (response.statusCode == 200) {
      final String responseBody = response.body;
      print('Response Body: $responseBody');

      try {
        final List<dynamic> data = jsonDecode(responseBody);
        setState(() {
          projects = data.map((item) => Project.fromJson(item)).toList();
          widget.updateTotalProjects(projects.length);
          isProjectListEmpty = projects.isEmpty;
        });
      } catch (e) {
        print('JSON Decoding Error: $e');
        // Handle the error or show a message to the user as needed.
      }
    } else {
      throw Exception('Failed to load projects');
    }
  }

  @override
  Widget build(BuildContext context) {
    return isProjectListEmpty
        ? Center(
            child: Text(
              'No projects found',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          )
        : ListView.builder(
            shrinkWrap: true,
            itemCount: projects.length,
            itemBuilder: (context, index) {
              final project = projects[index];
              return GestureDetector(
                onTap: () {
                  _navigateToDetailPage(project.idProject, project.namaProject);
                },
                child: Container(
                  margin: EdgeInsets.only(bottom: 10),
                  padding: EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        flex: 5,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(project.namaProject,
                                style: TextStyle(fontWeight: FontWeight.bold)),
                            SizedBox(height: 5),
                            Text('NO PO: ${project.jenisProject}'),
                            SizedBox(height: 5),
                            Row(
                              children: [
                                Text('Tanggal Target:'),
                                SizedBox(width: 5),
                                Text('${project.tglTarget}'),
                              ],
                            ),
                            SizedBox(height: 5),
                            Text(
                                'Pegawai Terlibat: ${project.namaPegawaiList.join(', ')}'),
                          ],
                        ),
                      ),
                      Expanded(
                        child: Text('${project.status}'),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
  }
}

class Project {
  final int idProject;
  final String namaProject;
  final List<String> namaPegawaiList;
  final String jenisProject;
  final String tglTarget;
  final String status;
  final int? idPerusahaan;

  Project({
    required this.idProject,
    required this.namaProject,
    required this.jenisProject,
    required this.tglTarget,
    required this.status,
    required this.namaPegawaiList,
    this.idPerusahaan,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      idProject: json['id_project'],
      namaProject: json['nama_project'],
      status: json['status'],
      jenisProject: json['no_po'].toString(), // Convert to String
      tglTarget: json['deadline'].toString(), // Convert to String
      namaPegawaiList: json['pegawai_terlibat'] != null
          ? List<String>.from(json['pegawai_terlibat'])
          : [],
      idPerusahaan: json['id_perusahaan'] as int?,
    );
  }
}
