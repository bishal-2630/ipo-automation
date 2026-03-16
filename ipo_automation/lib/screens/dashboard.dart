import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/account.dart';
import 'add_account.dart';

class DashboardScreen extends StatefulWidget {
  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService api = ApiService();
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Account>>(
      future: api.getAccounts(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return Center(child: Text("Error: ${snapshot.error}", style: TextStyle(color: Colors.red)));

        List<Account> accounts = snapshot.data ?? [];

        if (accounts.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.people_outline, size: 60, color: Colors.grey),
                SizedBox(height: 16),
                Text("No accounts found", style: TextStyle(color: Colors.grey)),
              ],
            ),
          );
        }

        final filteredAccounts = _searchQuery.isEmpty
            ? accounts
            : accounts.where((acc) {
                final String user = acc.user.toLowerCase();
                final String owner = (acc.ownerName ?? '').toLowerCase();
                return user.contains(_searchQuery.toLowerCase()) || owner.contains(_searchQuery.toLowerCase());
              }).toList();

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  Icon(Icons.manage_accounts, color: Colors.deepPurple),
                  SizedBox(width: 10),
                  Text(
                    "Manage Accounts", 
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 4.0),
              child: TextField(
                controller: _searchController,
                onChanged: (value) {
                  setState(() {
                    _searchQuery = value;
                  });
                },
                decoration: InputDecoration(
                  hintText: "Search by username or owner...",
                  prefixIcon: Icon(Icons.search, color: Colors.deepPurple),
                  suffixIcon: _searchQuery.isNotEmpty 
                    ? IconButton(
                        icon: Icon(Icons.clear, color: Colors.grey),
                        onPressed: () {
                          _searchController.clear();
                          setState(() {
                            _searchQuery = '';
                          });
                        },
                      )
                    : null,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(15),
                    borderSide: BorderSide.none,
                  ),
                  filled: true,
                  fillColor: Colors.deepPurple.withOpacity(0.05),
                  contentPadding: EdgeInsets.symmetric(vertical: 0, horizontal: 16),
                ),
              ),
            ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async => setState(() {}),
                child: ListView.builder(
                  padding: EdgeInsets.only(top: 8, bottom: 80),
                  itemCount: filteredAccounts.length,
                  itemBuilder: (context, index) {
                    final acc = filteredAccounts[index];
                    
                    return Card(
                      margin: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: Colors.deepPurple.withOpacity(0.1),
                          child: Icon(Icons.person, color: Colors.deepPurple),
                        ),
                        title: Text(
                          acc.ownerName != null && acc.ownerName!.isNotEmpty 
                              ? acc.ownerName! 
                              : "No Owner Name",
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          "Username: ${acc.user}",
                          style: TextStyle(color: Colors.grey[400]),
                        ),
                        trailing: IconButton(
                          icon: Icon(Icons.edit, color: Colors.deepPurple),
                          onPressed: () async {
                            final result = await Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => AddAccountScreen(account: acc)),
                            );
                            if (result == true) setState(() {});
                          },
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}
