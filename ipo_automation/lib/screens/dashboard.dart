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
    return Scaffold(
      appBar: AppBar(title: Text("IPO Automation Status"), backgroundColor: Colors.deepPurple),
      body: FutureBuilder<List<Account>>(
        future: api.getAccounts(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) return Center(child: CircularProgressIndicator());
          if (snapshot.hasError) return Center(child: Text("Error: ${snapshot.error}"));

          return RefreshIndicator(
            onRefresh: () async => setState(() {}),
            child: ListView.builder(
              itemCount: snapshot.data!.length,
              itemBuilder: (context, index) {
                final acc = snapshot.data![index];
                return Card(
                  margin: EdgeInsets.all(8),
                  child: ListTile(
                    leading: Icon(Icons.account_circle, color: Colors.blue),
                    title: Text(acc.user, style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text("${acc.bank}\nLast Run: ${acc.lastApplied}"),
                    trailing: Icon(acc.isActive ? Icons.check_circle : Icons.pause_circle, 
                                   color: acc.isActive ? Colors.green : Colors.grey),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
