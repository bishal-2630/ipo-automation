import 'package:flutter/material.dart';
import 'screens/dashboard.dart';

void main() => runApp(IPOApp());

class IPOApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IPO Automation',
      theme: ThemeData(primarySwatch: Colors.deepPurple, brightness: Brightness.dark),
      home: DashboardScreen(),
    );
  }
}
