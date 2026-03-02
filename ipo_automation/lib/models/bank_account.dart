class BankAccount {
  final int id;
  final String bank;
  final String bankDisplay;
  final String bankUsername;
  final int? linkedAccountId;
  final String createdAt;

  BankAccount({
    required this.id,
    required this.bank,
    required this.bankDisplay,
    required this.bankUsername,
    this.linkedAccountId,
    required this.createdAt,
  });

  factory BankAccount.fromJson(Map<String, dynamic> json) {
    return BankAccount(
      id: json['id'],
      bank: json['bank'],
      bankDisplay: json['bank_display'],
      bankUsername: json['bank_username'],
      linkedAccountId: json['linked_account'],
      createdAt: json['created_at'],
    );
  }
}
