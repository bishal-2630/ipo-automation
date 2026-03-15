import 'package:telephony/telephony.dart';
import 'api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

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

    // More robust regex for 6-digit OTPs (most common for Nepali banks)
    final otpMatch = RegExp(r'\b\d{6}\b').firstMatch(body);
    
    // Check keywords in body OR sender address (e.g., NICASIA, NABIL)
    bool isBankingSms = body.contains(RegExp(r'OTP|code|verification|passcode|Pin|Transaction', caseSensitive: false)) ||
                        address.contains(RegExp(r'NIC|Nabil|NMB|PRABHU|Siddhartha|Global|Sanima|Kumari|Citizens|Laxmi|Sunrise|Agriculture', caseSensitive: false));
    
    if (otpMatch != null && isBankingSms) {
      final otp = otpMatch.group(0)!;
      print("OTP Detected: $otp. Attempting relay...");
      await _relayOtpToBackend(otp);
    }
  }

  Future<void> _relayOtpToBackend(String otp) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      // We might need to know which account this OTP belongs to.
      // For now, we'll try to relay it for the currently active user/account.
      // Often, messages from banks don't include the username, 
      // but they might include the last 4 digits of the account number.
      
      // In a real scenario, we'd need to map the bank's sender ID or content 
      // to one of the user's accounts.
      
      // For now, we'll assume the user has a primary account or we'll 
      // broadcast it to all their accounts on the backend.
      // The backend BankOTPViewSet can handle lookup by meroshare_user.
      
      // Let's see if we can find a username in the local storage or if we need to fetch it.
      // For simplicity, we'll just relay it without a specific user if the backend allows, 
      // or we'll use a stored username.
      final username = prefs.getString('primary_meroshare_user');
      if (username != null) {
        await _apiService.relayOtp(username, otp);
        print("OTP relayed successfully for $username");
      } else {
        print("Primary meroshare user not found in preferences. Cannot relay OTP.");
      }
    } catch (e) {
      print("Error relaying OTP: $e");
    }
  }
}

@pragma('vm:entry-point')
void _backgroundMessageHandler(SmsMessage message) async {
  final body = message.body ?? "";
  final address = message.address ?? "";
  
  // Match foreground logic
  final otpMatch = RegExp(r'\b\d{6}\b').firstMatch(body);
  bool isBankingSms = body.contains(RegExp(r'OTP|code|verification|passcode|Pin|Transaction', caseSensitive: false)) ||
                      address.contains(RegExp(r'OTP|NIC|Nabil|NMB|PRABHU|Siddhartha|Global|Sanima|Kumari|Citizens|Laxmi|Sunrise|Agriculture', caseSensitive: false));

  if (otpMatch != null && isBankingSms) {
    final otp = otpMatch.group(0)!;
    final apiService = ApiService();
    final prefs = await SharedPreferences.getInstance();
    final username = prefs.getString('primary_meroshare_user');
    
    if (username != null) {
      try {
        await apiService.relayOtp(username, otp);
      } catch (e) {
        // Log to console even in background (visible in flutter logs)
        print("Background OTP relay error: $e");
      }
    }
  }
}
