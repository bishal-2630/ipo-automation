import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AddAccountScreen extends StatefulWidget {
  @override
  _AddAccountScreenState createState() => _AddAccountScreenState();
}

class _AddAccountScreenState extends State<AddAccountScreen> {
  final _formKey = GlobalKey<FormState>();
  final ApiService api = ApiService();
  bool _isLoading = false;

  // Controllers for form fields
  final _userController = TextEditingController();
  final _passwordController = TextEditingController();
  final _dpController = TextEditingController();
  final _crnController = TextEditingController();
  final _pinController = TextEditingController();
  final _bankController = TextEditingController();

  Future<void> _submitForm() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      try {
        final accountData = {
          'meroshare_user': _userController.text,
          'meroshare_pass': _passwordController.text, // Match Django field name
          'dp_name': _dpController.text,
          'crn': _crnController.text,
          'tpin': _pinController.text, // Match Django field name
          'bank_name': _bankController.text,
          'kitta': 10,
        };

        await api.addAccount(accountData);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Account Added Successfully!'), backgroundColor: Colors.green),
        );
        Navigator.pop(context, true); // Return true to signal refresh needed
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      } finally {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Add New Account")),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              _buildTextField(_userController, "MeroShare Username"),
              _buildTextField(_passwordController, "Password", obscureText: true),
              _buildTextField(_dpController, "DP Name (e.g., GLOBAL IME BANK)"),
              _buildTextField(_crnController, "CRN Number"),
              _buildTextField(_pinController, "4-Digit PIN", keyboardType: TextInputType.number),
              _buildTextField(_bankController, "Bank Name"),
              SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submitForm,
                  child: _isLoading 
                      ? CircularProgressIndicator(color: Colors.white)
                      : Text("Save Account", style: TextStyle(fontSize: 18)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String label, {bool obscureText = false, TextInputType? keyboardType, bool required = true}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: TextFormField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        decoration: InputDecoration(
          labelText: label,
          border: OutlineInputBorder(),
          filled: true,
        ),
        validator: (value) {
          if (required && (value == null || value.isEmpty)) {
            return 'This field is required';
          }
          return null;
        },
      ),
    );
  }

  @override
  void dispose() {
    _userController.dispose();
    _passwordController.dispose();
    _dpController.dispose();
    _crnController.dispose();
    _pinController.dispose();
    _bankController.dispose();
    super.dispose();
  }
}
