class Account {
  final int id;
  final String user;
  final String bank;
  final String lastApplied;
  final String? email;
  final bool isActive;

  Account({
    required this.id,
    required this.user,
    required this.bank,
    required this.lastApplied,
    this.email,
    required this.isActive,
  });

  factory Account.fromJson(Map<String, dynamic> json) {
    return Account(
      id: json['id'],
      user: json['meroshare_user'],
      bank: json['bank_name'],
      lastApplied: json['last_applied'] ?? 'Never',
      email: json['email'],
      isActive: json['is_active'],
    );
  }
}
