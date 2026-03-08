import 'package:flutter/material.dart';
import 'package:ipo_automation/services/api_service.dart';
import 'package:ipo_automation/models/account.dart';

class AddAccountScreen extends StatefulWidget {
  final Account? account;

  AddAccountScreen({this.account});

  @override
  _AddAccountScreenState createState() => _AddAccountScreenState();
}

class _AddAccountScreenState extends State<AddAccountScreen> {
  final _formKey = GlobalKey<FormState>();
  final ApiService api = ApiService();
  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _isActive = true;

  // Controllers for form fields
  final _userController = TextEditingController();
  final _passwordController = TextEditingController();
  final _dpController = TextEditingController();
  final _crnController = TextEditingController();
  final _pinController = TextEditingController();
  final _bankController = TextEditingController();
  final _boidController = TextEditingController();

  bool get isEditMode => widget.account != null;

  @override
  void initState() {
    super.initState();
    if (isEditMode) {
      final acc = widget.account!;
      _userController.text = acc.user;
      _dpController.text = acc.bank;
      _crnController.text = acc.crn;
      _pinController.text = acc.tPin;
      _bankController.text = acc.bank;
      _boidController.text = acc.boid;
      _isActive = acc.isActive;
    }
  }

  Future<void> _submitForm() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      try {
        final accountData = {
          'meroshare_user': _userController.text,
          'dp_name': _dpController.text,
          'crn': _crnController.text,
          'tpin': _pinController.text,
          'bank_name': _bankController.text,
          'boid': _boidController.text,
          'is_active': _isActive,
        };

        // Only include password if it's not empty
        if (_passwordController.text.isNotEmpty) {
          accountData['meroshare_pass'] = _passwordController.text;
        } else if (!isEditMode) {
          // If not in edit mode, password is required
          throw Exception("Password is required for new accounts");
        }

        if (isEditMode) {
          await api.updateAccount(widget.account!.id, accountData);
        } else {
          await api.addAccount(accountData);
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(isEditMode ? 'Account Updated Successfully!' : 'Account Added Successfully!'), 
            backgroundColor: Colors.green
          ),
        );
        Navigator.pop(context, true);
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
      appBar: AppBar(
        title: Text(isEditMode ? "Edit Account" : "Add New Account"),
        backgroundColor: Colors.deepPurple,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              _buildTextField(_userController, "MeroShare Username"),
              Padding(
                padding: const EdgeInsets.only(bottom: 16.0),
                child: TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: isEditMode ? "New Password (Optional)" : "MeroShare Password",
                    border: OutlineInputBorder(),
                    filled: true,
                    suffixIcon: IconButton(
                      icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                  validator: (v) {
                    if (!isEditMode && (v == null || v.isEmpty)) {
                      return "This field is required";
                    }
                    return null;
                  },
                ),
              ),
              _buildTextField(_dpController, "DP Name (e.g., GLOBAL IME BANK)"),
              _buildTextField(_boidController, "16-Digit BOID", keyboardType: TextInputType.number),
              _buildTextField(_crnController, "CRN Number"),
              _buildTextField(_pinController, "4-Digit PIN", keyboardType: TextInputType.number),
              _buildTextField(_bankController, "Bank Name"),
              SwitchListTile(
                title: Text("Active Account"),
                subtitle: Text("IPOs will only be applied for active accounts"),
                value: _isActive,
                onChanged: (val) => setState(() => _isActive = val),
              ),
              SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submitForm,
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.deepPurple),
                  child: _isLoading 
                      ? CircularProgressIndicator(color: Colors.white)
                      : Text(isEditMode ? "Update Account" : "Save Account", 
                             style: TextStyle(fontSize: 18, color: Colors.white)),
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
    _boidController.dispose();
    super.dispose();
  }
}
