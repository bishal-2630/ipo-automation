import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/foundation.dart';
import 'api_service.dart';
import 'dart:io' show Platform; // Use show Platform to be specific, or avoid if possible

class NotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final ApiService _api = ApiService();
  final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'high_importance_channel', // id
    'High Importance Notifications', // title
    description: 'This channel is used for important notifications.', // description
    importance: Importance.max,
  );

  Future<void> initialize() async {
    // 1. Request Permission
    NotificationSettings settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      if (!kIsWeb) {
        // 2. Setup Local Notifications for Foreground (Mobile only)
        const AndroidInitializationSettings initializationSettingsAndroid =
            AndroidInitializationSettings('@mipmap/ic_launcher');
        const InitializationSettings initializationSettings =
            InitializationSettings(android: initializationSettingsAndroid);
        
        await _localNotifications.initialize(initializationSettings);

        if (Platform.isAndroid) {
          await _localNotifications
              .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
              ?.createNotificationChannel(_channel);
        }
      }

      // 3. Register Token
      String? token = await _fcm.getToken();
      if (token != null) {
        String os = kIsWeb ? 'web' : Platform.operatingSystem;
        await _api.saveFcmToken(token, os);
      }

      FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
        String os = kIsWeb ? 'web' : Platform.operatingSystem;
        _api.saveFcmToken(newToken, os);
      });

      // 4. Listeners
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        if (kIsWeb) return; // Local notifications skip on web for now

        RemoteNotification? notification = message.notification;
        AndroidNotification? android = message.notification?.android;

        if (notification != null && android != null && Platform.isAndroid) {
          _localNotifications.show(
            notification.hashCode,
            notification.title,
            notification.body,
            NotificationDetails(
              android: AndroidNotificationDetails(
                _channel.id,
                _channel.name,
                channelDescription: _channel.description,
                icon: android.smallIcon,
              ),
            ),
          );
        }
      });
    }
  }
}
