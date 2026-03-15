class Account {
  final int id;
  final String user;
  final String bank;
  final String dpName;
  final String lastApplied;
  final bool isActive;
  final String crn;
  final String tPin;
  final String boid;
  final String? ownerName;

  Account({
    required this.id,
    required this.user,
    required this.bank,
    required this.dpName,
    required this.lastApplied,
    required this.isActive,
    required this.crn,
    required this.tPin,
    required this.boid,
    this.ownerName,
  });

  factory Account.fromJson(Map<String, dynamic> json) {
    return Account(
      id: json['id'],
      user: json['meroshare_user'],
      bank: json['bank_name'],
      dpName: json['dp_name'] ?? '',
      lastApplied: json['last_applied'] ?? 'Never',
      isActive: json['is_active'],
      crn: json['crn'] ?? '',
      tPin: json['tpin'] ?? '',
      boid: json['boid'] ?? '',
      ownerName: json['owner_name'],
    );
  }
}
