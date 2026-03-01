import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'home.dart';
import 'auth_screen.dart';


class AuthScreen extends StatefulWidget {
  @override
  _AuthScreenState createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool isLogin = true;
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final ApiService api = ApiService();
  bool isLoading = false;

  void submit() async {
    setState(() => isLoading = true);
    bool success = false;
    try {
      if (isLogin) {
        success = await api.login(_usernameController.text, _passwordController.text);
      } else {
        success = await api.register(_usernameController.text, _passwordController.text);
      }

      if (success) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => HomeScreen()));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Authentication failed.")));
      }
    } catch (e) {
       ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(isLogin ? "Login" : "Register")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(controller: _usernameController, decoration: InputDecoration(labelText: "Username")),
            SizedBox(height: 10),
            TextField(controller: _passwordController, decoration: InputDecoration(labelText: "Password"), obscureText: true),
            SizedBox(height: 20),
            isLoading
                ? CircularProgressIndicator()
                : ElevatedButton(onPressed: submit, child: Text(isLogin ? "Login" : "Register")),
            TextButton(
              onPressed: () => setState(() => isLogin = !isLogin),
              child: Text(isLogin ? "Don't have an account? Register" : "Already have an account? Login"),
            )
          ],
        ),
      ),
    );
  }
}
