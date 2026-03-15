import 'package:flutter/material.dart';
import 'package:ipo_automation/services/api_service.dart';
import 'package:ipo_automation/models/account.dart';
import 'add_account.dart';
import 'add_bank_screen.dart';
import 'bank_list_screen.dart';
import 'login_screen.dart';
import 'dashboard.dart';
import 'package:ipo_automation/models/bank_account.dart';
import 'package:shared_preferences/shared_preferences.dart';

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

          final allAccounts = snapshot.data ?? [];

          if (allAccounts.isNotEmpty) {
            // Automatically set the first account as primary for OTP relay if not set
            SharedPreferences.getInstance().then((prefs) {
              if (prefs.getString('primary_meroshare_user') == null) {
                prefs.setString('primary_meroshare_user', allAccounts.first.user);
              }
            });
          }

          if (allAccounts.isEmpty) {
            return _buildEmptyState("No accounts", "Tap + to add MeroShare account");
          }

          return RefreshIndicator(
            onRefresh: () async => setState(() {}),
            child: Column(
              children: [
                _buildRelayStatusHeader(),
                Expanded(
                  child: ListView.builder(
                    padding: EdgeInsets.only(bottom: 80),
                    itemCount: allAccounts.length,
                    itemBuilder: (context, index) => _buildAccountCard(allAccounts[index]),
                  ),
                ),
              ],
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
    return Column(
      children: [
        _buildRelayStatusHeader(),
        Expanded(
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.inbox, size: 80, color: Colors.grey),
                SizedBox(height: 16),
                Text(title, style: TextStyle(fontSize: 18, color: Colors.grey)),
                Text(sub, style: TextStyle(color: Colors.grey)),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRelayStatusHeader() {
    return FutureBuilder<SharedPreferences>(
      future: SharedPreferences.getInstance(),
      builder: (context, snapshot) {
        final prefs = snapshot.data;
        final primaryUser = prefs?.getString('primary_meroshare_user');
        final isReady = primaryUser != null;

        return Container(
          padding: EdgeInsets.all(16),
          color: Colors.deepPurple.withOpacity(0.05),
          child: Row(
            children: [
              Icon(
                isReady ? Icons.check_circle : Icons.warning_amber_rounded,
                color: isReady ? Colors.green : Colors.orange,
              ),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Relay Service: ${isReady ? 'Active' : 'Unconfigured'}",
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      isReady 
                        ? "Pushing OTPs for $primaryUser" 
                        : "Long-press an account below to activate",
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              ),
              if (isReady)
                ElevatedButton(
                  onPressed: () async {
                    try {
                      await api.relayOtp(primaryUser!, "999999");
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text("Test OTP (999999) sent! Check database."), backgroundColor: Colors.green),
                      );
                    } catch (e) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text("Test Failed: $e"), backgroundColor: Colors.red),
                      );
                    }
                  },
                  child: Text("Test"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.deepPurple,
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(horizontal: 12),
                  ),
                ),
            ],
          ),
        );
      },
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
        title: Row(
          children: [
            Expanded(
              child: Text(
                acc.user, 
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (acc.ownerName != null && acc.ownerName!.isNotEmpty)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.deepPurple.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  acc.ownerName!,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.deepPurple,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FutureBuilder<SharedPreferences>(
                future: SharedPreferences.getInstance(),
                builder: (context, snapshot) {
                  final isPrimary = snapshot.hasData && snapshot.data!.getString('primary_meroshare_user') == acc.user;
                  if (!isPrimary) return SizedBox.shrink();
                  return Container(
                    margin: EdgeInsets.only(bottom: 6),
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.vibration, size: 12, color: Colors.green),
                        SizedBox(width: 4),
                        Text("Active OTP Relay", style: TextStyle(color: Colors.green, fontSize: 10, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  );
                },
              ),
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
        onTap: () {
          // Normal tap could show details
        },
        onLongPress: () async {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('primary_meroshare_user', acc.user);
          setState(() {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text("Relay set to ${acc.user}"), backgroundColor: Colors.green),
            );
          });
        },
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
