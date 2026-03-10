import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/home.dart';
import 'screens/login_screen.dart';
import 'services/notification_service.dart';

import 'package:flutter/foundation.dart';

// Top-level background message handler
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  try {
    await Firebase.initializeApp();
  } catch (e) {
    print("Firebase background init failed: $e");
  }
  print("Handling a background message: ${message.messageId}");
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  try {
    await Firebase.initializeApp();
    // Set the background messaging handler early on
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  } catch (e) {
    print("Firebase initialization skipped or failed: $e");
    if (kIsWeb) {
      print("Note: Firebase Web requires explicit configuration in index.html or firebase_options.dart");
    }
  }

  final notificationService = NotificationService();
  await notificationService.initialize();
  
  final prefs = await SharedPreferences.getInstance();
  final token = prefs.getString('token');

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

