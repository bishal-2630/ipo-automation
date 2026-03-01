import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/account.dart';

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000/api'; // Use 10.0.2.2 for Emulator

  Future<List<Account>> getAccounts() async {
    final response = await http.get(Uri.parse('$baseUrl/accounts/'));
    if (response.statusCode == 200) {
      List jsonResponse = json.decode(response.body);
      return jsonResponse.map((data) => Account.fromJson(data)).toList();
    } else {
      throw Exception('Failed to load accounts');
    }
  }

  Future<List<dynamic>> getLogs() async {
    final response = await http.get(Uri.parse('$baseUrl/logs/'));
    return json.decode(response.body);
  }
}
