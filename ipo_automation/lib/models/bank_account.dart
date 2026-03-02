class BankAccount {
  final int id;
  final String bank;
  final String bankDisplay;
  final String phoneNumber;
  final int? linkedAccountId;
  final String createdAt;

  BankAccount({
    required this.id,
    required this.bank,
    required this.bankDisplay,
    required this.phoneNumber,
    this.linkedAccountId,
    required this.createdAt,
  });

  factory BankAccount.fromJson(Map<String, dynamic> json) {
    return BankAccount(
      id: json['id'],
      bank: json['bank'],
      bankDisplay: json['bank_display'],
      phoneNumber: json['phone_number'],
      linkedAccountId: json['linked_account'],
      createdAt: json['created_at'],
    );
  }
}
