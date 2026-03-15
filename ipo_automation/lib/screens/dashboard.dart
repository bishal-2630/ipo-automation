import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

class DashboardScreen extends StatefulWidget {
  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService api = ApiService();
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();
  List<String> _localLogs = [];
  bool _showLocalLogs = false;

  Future<void> _loadLocalLogs() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _localLogs = prefs.getStringList('relay_debug_logs') ?? [];
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<dynamic>>(
      future: api.getLogs(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return Center(child: Text("Error: ${snapshot.error}"));

        List<dynamic> allLogs = snapshot.data ?? [];

        if (allLogs.isEmpty) {
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

        final filteredLogs = _searchQuery.isEmpty
            ? allLogs
            : allLogs.where((l) {
                final String owner = (l['owner_name'] ?? '').toString().toLowerCase();
                return owner.contains(_searchQuery.toLowerCase());
              }).toList();

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text("App Relay Events", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                  TextButton.icon(
                    onPressed: () {
                      setState(() => _showLocalLogs = !_showLocalLogs);
                      if (_showLocalLogs) _loadLocalLogs();
                    },
                    icon: Icon(_showLocalLogs ? Icons.visibility_off : Icons.visibility, size: 16, color: Colors.deepPurple),
                    label: Text(_showLocalLogs ? "Hide Logs" : "Show Logs", style: TextStyle(fontSize: 12, color: Colors.deepPurple)),
                  ),
                ],
              ),
            ),
            if (_showLocalLogs)
              Container(
                height: 120,
                width: double.infinity,
                margin: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black26,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white10),
                ),
                child: _localLogs.isEmpty 
                  ? Center(child: Text("No background relay events logged yet", style: TextStyle(color: Colors.grey, fontSize: 11)))
                  : ListView.builder(
                      shrinkWrap: true,
                      itemCount: _localLogs.length,
                      itemBuilder: (context, i) => Padding(
                        padding: const EdgeInsets.only(bottom: 4.0),
                        child: Text(
                          _localLogs[i], 
                          style: TextStyle(fontFamily: 'monospace', fontSize: 10, color: Colors.greenAccent),
                        ),
                      ),
                    ),
              ),
            Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: TextField(
                controller: _searchController,
                onChanged: (value) {
                  setState(() {
                    _searchQuery = value;
                  });
                },
                decoration: InputDecoration(
                  hintText: "Filter by owner (e.g., Mom, Dad)...",
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
                  itemCount: filteredLogs.length,
                  itemBuilder: (context, index) {
                    final log = filteredLogs[index];
                    final isSuccess = log['status'] == 'Triggered' || log['status'] == 'Success';
                    
                    return Dismissible(
                      key: Key(log['id'].toString()),
                      direction: DismissDirection.endToStart,
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: EdgeInsets.symmetric(horizontal: 20),
                        color: Colors.redAccent,
                        child: Icon(Icons.delete, color: Colors.white),
                      ),
                      onDismissed: (direction) async {
                        try {
                          await api.deleteLog(log['id']);
                          setState(() {
                            allLogs.removeWhere((l) => l['id'] == log['id']);
                          });
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text("Notification deleted"), duration: Duration(seconds: 2)),
                          );
                        } catch (e) {
                          setState(() {}); // Refresh to restore item if delete failed
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text("Delete failed: $e"), backgroundColor: Colors.red),
                          );
                        }
                      },
                      child: Card(
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
                          title: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  "${log['company_name']}",
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              if (log['owner_name'] != null && log['owner_name'].toString().isNotEmpty)
                                Container(
                                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.deepPurple.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    log['owner_name'].toString(),
                                    style: TextStyle(
                                      fontSize: 10,
                                      color: Colors.deepPurple,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text("Account: ${log['account_user']}"),
                                  if (log['is_read'] == false) ...[
                                    SizedBox(width: 8),
                                    Container(
                                      width: 8,
                                      height: 8,
                                      decoration: BoxDecoration(color: Colors.blue, shape: BoxShape.circle),
                                    ),
                                  ],
                                ],
                              ),
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

  String _formatTime(String? timestamp) {
    if (timestamp == null) return "";
    try {
      final dt = DateTime.parse(timestamp).toLocal();
      final monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      final month = monthNames[dt.month - 1];
      final day = dt.day;
      
      final hour = dt.hour > 12 ? dt.hour - 12 : (dt.hour == 0 ? 12 : dt.hour);
      final ampm = dt.hour >= 12 ? "PM" : "AM";
      final minute = dt.minute.toString().padLeft(2, '0');
      
      return "$month $day, $hour:$minute $ampm";
    } catch (e) {
      return "";
    }
  }
}
