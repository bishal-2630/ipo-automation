import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/account.dart';

class DashboardScreen extends StatefulWidget {
  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService api = ApiService();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<dynamic>>(
      future: api.getLogs(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return Center(child: Text("Error: ${snapshot.error}"));

        final logs = snapshot.data ?? [];

        if (logs.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.notifications_none, size: 60, color: Colors.grey),
                SizedBox(height: 16),
                Text("No notifications yet", style: TextStyle(color: Colors.grey)),
              ],
            ),
          );
        }

        return RefreshIndicator(
          onRefresh: () async => setState(() {}),
          child: ListView.builder(
            itemCount: logs.length,
            itemBuilder: (context, index) {
              final log = logs[index];
              final isSuccess = log['status'] == 'Triggered' || log['status'] == 'Success';
              
              return Card(
                margin: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: isSuccess ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                    child: Icon(
                      isSuccess ? Icons.check : Icons.error_outline,
                      color: isSuccess ? Colors.green : Colors.red,
                    ),
                  ),
                  title: Text(
                    "${log['company_name']}",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("Account: ${log['account_user']}"),
                      Text(
                        "${log['remark']}",
                        style: TextStyle(fontSize: 12, color: Colors.grey[400]),
                      ),
                    ],
                  ),
                  trailing: Text(
                    _formatTime(log['timestamp']),
                    style: TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }

  String _formatTime(String? timestamp) {
    if (timestamp == null) return "";
    try {
      final dt = DateTime.parse(timestamp).toLocal();
      return "${dt.hour}:${dt.minute.toString().padLeft(2, '0')}";
    } catch (e) {
      return "";
    }
  }
}
