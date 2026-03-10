import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/foundation.dart';
import 'api_service.dart';

class NotificationService {
  FirebaseMessaging? _fcm;
  final ApiService _api = ApiService();
  final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'high_importance_channel', // id
    'High Importance Notifications', // title
    description: 'This channel is used for important notifications.', // description
    importance: Importance.max,
  );

  Future<void> initialize() async {
    try {
      _fcm = FirebaseMessaging.instance;
    } catch (e) {
      print("Could not get FirebaseMessaging instance: $e");
      return;
    }

    final fcm = _fcm;
    if (fcm == null) return;

    // 1. Request Permission
    NotificationSettings settings = await fcm.requestPermission(
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

        if (defaultTargetPlatform == TargetPlatform.android) {
          await _localNotifications
              .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
              ?.createNotificationChannel(_channel);
        }
      }

      String? token = await fcm.getToken();
      if (token != null) {
        String os = kIsWeb ? 'web' : defaultTargetPlatform.name;
        await _api.saveFcmToken(token, os);
      }

      FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
        String os = kIsWeb ? 'web' : defaultTargetPlatform.name;
        _api.saveFcmToken(newToken, os);
      });

      // 4. Listeners
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        if (kIsWeb) return; // Local notifications skip on web for now

        RemoteNotification? notification = message.notification;
        AndroidNotification? android = message.notification?.android;

        if (notification != null && android != null && defaultTargetPlatform == TargetPlatform.android) {
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
