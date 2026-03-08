import 'package:flutter/material.dart';
import 'package:ipo_automation/services/api_service.dart';
import 'package:ipo_automation/models/account.dart';
import 'add_account.dart';
import 'add_bank_screen.dart';
import 'bank_list_screen.dart';
import 'login_screen.dart';
import 'dashboard.dart';
import 'package:ipo_automation/models/bank_account.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService api = ApiService();
  String? _latestNotification;
  int _unreadCount = 0;

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
          _latestNotification = "📢 ${latest['account_user']}: ${latest['status']}";
          _unreadCount = logs.where((l) => l['is_read'] == false).length;
        });
      }
    } catch (e) {
      print("Failed to fetch logs: $e");
    }
  }

  int _selectedIndex = 0;

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
      body: RefreshIndicator(
        onRefresh: () async {
          setState(() {});
          await _fetchLatestLog();
        },
        child: IndexedStack(
          index: _selectedIndex,
          children: [
            _buildAccountsTab(),
            BankListScreen(),
            DashboardScreen(),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildAccountsTab() {
    return Scaffold(
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
            return _buildEmptyState("No accounts", "Tap + to add MeroShare account");
          }

          return RefreshIndicator(
            onRefresh: () async => setState(() {}),
            child: ListView.builder(
              padding: EdgeInsets.only(bottom: 80),
              itemCount: accounts.length,
              itemBuilder: (context, index) => _buildAccountCard(accounts[index]),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        heroTag: 'add_account',
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => AddAccountScreen()),
          );
          if (result == true) setState(() {});
        },
        child: Icon(Icons.add),
        backgroundColor: Colors.deepPurple,
      ),
    );
  }

  Widget _buildEmptyState(String title, String sub) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox, size: 80, color: Colors.grey),
          SizedBox(height: 16),
          Text(title, style: TextStyle(fontSize: 18, color: Colors.grey)),
          Text(sub, style: TextStyle(color: Colors.grey)),
        ],
      ),
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
                  Icon(Icons.fingerprint, size: 14, color: Colors.grey),
                  SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      "BOID: ${acc.boid}", 
                      style: TextStyle(color: Colors.grey[400], fontSize: 13),
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
  }

  Widget _buildBottomNav() {
    return BottomNavigationBar(
      backgroundColor: Colors.black87,
      selectedItemColor: Colors.amber,
      unselectedItemColor: Colors.grey,
      currentIndex: _selectedIndex,
      type: BottomNavigationBarType.fixed,
      onTap: (index) {
        setState(() {
          _selectedIndex = index;
          if (index == 2) {
            _unreadCount = 0;
            api.markLogsAsRead();
          }
        });
      },
      items: [
        BottomNavigationBarItem(icon: Icon(Icons.wallet), label: 'Accounts'),
        BottomNavigationBarItem(icon: Icon(Icons.account_balance), label: 'Banks'),
        BottomNavigationBarItem(
          icon: Stack(
            children: [
              Icon(Icons.notifications),
              if (_unreadCount > 0)
                Positioned(
                  right: 0,
                  top: 0,
                  child: Container(
                    padding: EdgeInsets.all(2),
                    decoration: BoxDecoration(
                      color: Colors.red,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    constraints: BoxConstraints(minWidth: 16, minHeight: 16),
                    child: Text(
                      '$_unreadCount',
                      style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
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
