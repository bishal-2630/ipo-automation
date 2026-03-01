import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/home.dart';
import 'screens/login_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final token = prefs.getString('token'); // Check if a token exists

  runApp(IPOApp(isLoggedIn: token != null));
}

class IPOApp extends StatelessWidget {
  final bool isLoggedIn;
  
  IPOApp({required this.isLoggedIn});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IPO Automation',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(primarySwatch: Colors.deepPurple, brightness: Brightness.dark),
      // If logged in, go to Home; else go to LoginScreen
      home: isLoggedIn ? HomeScreen() : LoginScreen(),
    );
  }
}

