import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/account.dart';
import 'add_account.dart';
import 'login_screen.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService api = ApiService();
  String? _latestNotification;

  @override
  void initState() {
    super.initState();
    _fetchLatestLog();
  }

  Future<void> _fetchLatestLog() async {
    try {
      final logs = await api.getLogs();
      if (logs.isNotEmpty) {
        final latest = logs.first;
        setState(() {
          _latestNotification = "📢 ${latest['account_name']}: ${latest['remarks']}";
        });
      }
    } catch (e) {
      print("Failed to fetch logs: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("IPO Automation", style: TextStyle(fontWeight: FontWeight.bold)), 
        backgroundColor: Colors.deepPurple,
        elevation: 0,
        actions: [
          PopupMenuButton<String>(
            icon: Icon(Icons.account_circle, size: 30),
            tooltip: 'User Profile',
            onSelected: (value) async {
              if (value == 'logout') {
                await api.logout();
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => LoginScreen()),
                );
              }
            },
            itemBuilder: (BuildContext context) => [
              PopupMenuItem(
                value: 'profile',
                child: Row(
                  children: [
                    Icon(Icons.person_outline, size: 20, color: Colors.grey),
                    SizedBox(width: 10),
                    Text("My Profile"),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, size: 20, color: Colors.redAccent),
                    SizedBox(width: 10),
                    Text("Logout", style: TextStyle(color: Colors.redAccent)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: FutureBuilder<List<Account>>(
        future: api.getAccounts(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text("Error: ${snapshot.error}", style: TextStyle(color: Colors.red)));
          }

          final accounts = snapshot.data ?? [];

          if (accounts.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                   Icon(Icons.inbox, size: 80, color: Colors.grey),
                   SizedBox(height: 16),
                   Text("No accounts added yet.", style: TextStyle(fontSize: 18, color: Colors.grey)),
                   Text("Tap + to add an account.", style: TextStyle(color: Colors.grey)),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              setState(() {});
              await _fetchLatestLog();
            },
            child: ListView.builder(
              padding: EdgeInsets.only(bottom: 80), // Space for bottom bar
              itemCount: accounts.length,
              itemBuilder: (context, index) {
                final acc = accounts[index];
                return _buildAccountCard(acc);
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => AddAccountScreen()),
          );
          if (result == true) {
            setState(() {}); // Refresh list if account was added
          }
        },
        icon: Icon(Icons.add),
        label: Text("Add Account"),
        backgroundColor: Colors.deepPurpleAccent,
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildAccountCard(Account acc) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: EdgeInsets.all(16),
        leading: CircleAvatar(
          backgroundColor: Colors.deepPurple.withOpacity(0.1),
          child: Icon(Icons.person, color: Colors.deepPurple),
        ),
        title: Text(acc.user, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.account_balance, size: 14, color: Colors.grey),
                  SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      acc.bank, 
                      style: TextStyle(color: Colors.grey[400]),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.history, size: 14, color: Colors.grey),
                  SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      "Last run: ${acc.lastApplied}", 
                      style: TextStyle(color: Colors.grey[400], fontSize: 12),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        trailing: Container(
          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: acc.isActive ? Colors.green.withOpacity(0.1) : Colors.grey.withOpacity(0.1),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            acc.isActive ? "ACTIVE" : "PAUSED",
            style: TextStyle(
              color: acc.isActive ? Colors.green : Colors.grey,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ),
      ),
    );
  }

  int _selectedIndex = 0;

  Widget _buildBottomNav() {
    return BottomNavigationBar(
      backgroundColor: Colors.black87,
      selectedItemColor: Colors.amber,
      unselectedItemColor: Colors.grey,
      currentIndex: _selectedIndex,
      onTap: (index) {
        setState(() {
          _selectedIndex = index;
        });
        if (index == 1 && _latestNotification != null) {
          // If they click notifications, show the latest log in a snackbar or dialog
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(_latestNotification!),
              backgroundColor: Colors.deepPurple,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      },
      items: [
        BottomNavigationBarItem(
          icon: Icon(Icons.account_balance_wallet),
          label: 'Accounts',
        ),
        BottomNavigationBarItem(
          icon: Stack(
            children: [
              Icon(Icons.notifications),
              if (_latestNotification != null)
                Positioned(
                  right: 0,
                  top: 0,
                  child: Container(
                    padding: EdgeInsets.all(2),
                    decoration: BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                    constraints: BoxConstraints(minWidth: 8, minHeight: 8),
                  ),
                ),
            ],
          ),
          label: 'Status',
        ),
      ],
    );
  }
}
