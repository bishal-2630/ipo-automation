import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/account.dart';

class ApiService {
  static const String baseUrl = 'https://bishal26-ipo-automation.hf.space/api';

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }

  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token);
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
  }

  Future<bool> register(String username, String password, String email, String firstName, String lastName) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'username': username, 
        'password': password,
        'email': email,
        'first_name': firstName,
        'last_name': lastName,
      }),
    );
    if (response.statusCode == 201) {
      final data = json.decode(response.body);
      await saveToken(data['token']);
      return true;
    }
    return false;
  }

  Future<bool> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'username': username, 'password': password}),
    );
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      await saveToken(data['token']);
      return true;
    }
    return false;
  }

  Future<List<Account>> getAccounts() async {
    final token = await getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/accounts/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (response.statusCode == 200) {
      List jsonResponse = json.decode(response.body);
      return jsonResponse.map((data) => Account.fromJson(data)).toList();
    } else {
      throw Exception('Failed to load accounts');
    }
  }

  Future<List<dynamic>> getLogs() async {
    final token = await getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/logs/'),
      headers: {'Authorization': 'Token $token'},
    );
    return json.decode(response.body);
  }

  Future<void> addAccount(Map<String, dynamic> accountData) async {
    final token = await getToken();
    final response = await http.post(
      Uri.parse('$baseUrl/accounts/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token' // Attach token here
      },
      body: json.encode(accountData),
    );
    if (response.statusCode != 201) {
      throw Exception('Failed to add account: ${response.body}');
    }
  }
}
