import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/account.dart';

class AddBankScreen extends StatefulWidget {
  @override
  _AddBankScreenState createState() => _AddBankScreenState();
}

class _AddBankScreenState extends State<AddBankScreen> {
  final _formKey = GlobalKey<FormState>();
  final ApiService api = ApiService();

  String _selectedBank = 'nic_asia';
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  int? _selectedAccountId;

  List<Account> _accounts = [];
  bool _isLoading = false;

  final Map<String, String> _bankList = {
    'agriculture': 'Agriculture Development Bank Ltd.',
    'citizens': 'Citizens Bank International Ltd.',
    'everest': 'Everest Bank Ltd.',
    'global_ime': 'Global IME Bank Ltd.',
    'himalayan': 'Himalayan Bank Ltd.',
    'kumari': 'Kumari Bank Ltd.',
    'laxmi_sunrise': 'Laxmi Sunrise Bank Ltd.',
    'machhapuchchhre': 'Machhapuchchhre Bank Ltd.',
    'nabil': 'Nabil Bank Ltd.',
    'nepal_bank': 'Nepal Bank Ltd.',
    'nimb': 'Nepal Investment Mega Bank Ltd.',
    'sbi': 'Nepal SBI Bank Ltd.',
    'nic_asia': 'NIC Asia Bank Ltd.',
    'nmb': 'NMB Bank Ltd.',
    'prabhu': 'Prabhu Bank Ltd.',
    'prime': 'Prime Commercial Bank Ltd.',
    'rbb': 'Rastriya Banijya Bank Ltd.',
    'sanima': 'Sanima Bank Ltd.',
    'siddhartha': 'Siddhartha Bank Ltd.',
    'scb': 'Standard Chartered Bank Nepal Ltd.',
    'garima': 'Garima Bikas Bank Ltd.',
    'jyoti': 'Jyoti Bikas Bank Ltd.',
    'kamana': 'Kamana Sewa Bikas Bank Ltd.',
    'lumbini': 'Lumbini Bikas Bank Ltd.',
    'mahalaxmi': 'Mahalaxmi Bikas Bank Ltd.',
    'muktinath': 'Muktinath Bikas Bank Ltd.',
    'shangrila': 'Shangri-la Bikas Bank Ltd.',
    'shine_resunga': 'Shine Resunga Development Bank Ltd.',
  };

  @override
  void initState() {
    super.initState();
    _fetchAccounts();
  }

  Future<void> _fetchAccounts() async {
    try {
      final accounts = await api.getAccounts();
      setState(() {
        _accounts = accounts;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to load accounts for linking")),
      );
    }
  }

  void _submit() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      try {
        await api.addBankAccount({
          'bank': _selectedBank,
          'bank_username': _usernameController.text,
          'bank_password': _passwordController.text,
          'linked_account': _selectedAccountId,
        });
        Navigator.pop(context, true);
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error: $e")),
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
        title: Text("Add Bank Credentials"),
        backgroundColor: Colors.deepPurple,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                "Link your internet banking to check balance before applying for IPOs.",
                style: TextStyle(color: Colors.grey[400], fontSize: 14),
              ),
              SizedBox(height: 25),
              DropdownButtonFormField<String>(
                value: _selectedBank,
                decoration: InputDecoration(
                  labelText: "Select Bank",
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.account_balance),
                ),
                items: _bankList.entries.map((e) {
                  return DropdownMenuItem(value: e.key, child: Text(e.value));
                }).toList(),
                onChanged: (val) => setState(() => _selectedBank = val!),
              ),
              SizedBox(height: 20),
              TextFormField(
                controller: _usernameController,
                decoration: InputDecoration(
                  labelText: "E-Banking Username",
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.person),
                ),
                validator: (v) => v!.isEmpty ? "Required" : null,
              ),
              SizedBox(height: 20),
              TextFormField(
                controller: _passwordController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: "E-Banking Password",
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.lock),
                ),
                validator: (v) => v!.isEmpty ? "Required" : null,
              ),
              SizedBox(height: 20),
              DropdownButtonFormField<int?>(
                value: _selectedAccountId,
                decoration: InputDecoration(
                  labelText: "Link to MeroShare Account",
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.link),
                  helperText: "Critical for associating bank balance with user",
                ),
                items: [
                  DropdownMenuItem(value: null, child: Text("None")),
                  ..._accounts.map((a) {
                    return DropdownMenuItem(value: a.id, child: Text(a.user));
                  }).toList(),
                ],
                onChanged: (val) => setState(() => _selectedAccountId = val),
              ),
              SizedBox(height: 40),
              ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepPurple,
                  padding: EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                child: _isLoading 
                  ? CircularProgressIndicator(color: Colors.white)
                  : Text("Save Bank Details", style: TextStyle(fontSize: 16, color: Colors.white)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
