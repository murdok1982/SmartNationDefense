import 'dart:convert';
import 'package:crypto/crypto.dart';

enum MeshMessageType {
  intelUpdate,
  fieldReport,
  alert,
  locationBeacon,
  opord,
  duressSignal,
}

extension MeshMessageTypeExtension on MeshMessageType {
  String get value {
    return name[0].toLowerCase() + name.substring(1);
  }

  static MeshMessageType fromString(String s) {
    return MeshMessageType.values.firstWhere(
      (e) => e.name.toLowerCase() == s.toLowerCase(),
      orElse: () => MeshMessageType.intelUpdate,
    );
  }
}

String _canonicalize(dynamic value) {
  if (value is Map) {
    final keys = value.keys.map((k) => k.toString()).toList()..sort();
    final entries = keys.map((k) => '${jsonEncode(k)}:${_canonicalize(value[k])}').join(',');
    return '{$entries}';
  }
  if (value is List) {
    return '[${value.map(_canonicalize).join(',')}]';
  }
  return jsonEncode(value);
}

class MeshSigner {
  MeshSigner(String psk) : _key = utf8.encode(psk);

  final List<int> _key;

  String _digest(String data) => Hmac(sha256, _key).convert(utf8.encode(data)).toString();

  Map<String, dynamic> _signableJson(MeshMessage message) {
    final json = message.toJson()..remove('signature');
    return json;
  }

  String sign(MeshMessage message) => _digest(_canonicalize(_signableJson(message)));

  bool verify(MeshMessage message) {
    if (message.signature.isEmpty) return false;
    final expected = sign(message);
    return _constantTimeEquals(expected, message.signature);
  }

  String signHandshake(String endpointId, int timestamp) => _digest('handshake:$endpointId:$timestamp');

  bool verifyHandshake(String endpointId, int timestamp, String hmac) {
    final expected = signHandshake(endpointId, timestamp);
    return hmac.isNotEmpty && _constantTimeEquals(expected, hmac);
  }

  bool _constantTimeEquals(String a, String b) {
    final ba = utf8.encode(a);
    final bb = utf8.encode(b);
    if (ba.length != bb.length) return false;
    var diff = 0;
    for (var i = 0; i < ba.length; i++) {
      diff |= ba[i] ^ bb[i];
    }
    return diff == 0;
  }
}

class MeshMessage {
  final MeshMessageType type;
  final Map<String, dynamic> payload;
  final String senderId;
  final int timestamp;
  final int ttl;
  final String signature;
  final String? relayPath;

  const MeshMessage({
    required this.type,
    required this.payload,
    required this.senderId,
    required this.timestamp,
    this.ttl = 3,
    this.signature = '',
    this.relayPath,
  });

  Map<String, dynamic> toJson() => {
        'type': type.value,
        'payload': payload,
        'senderId': senderId,
        'timestamp': timestamp,
        'ttl': ttl,
        'signature': signature,
        if (relayPath != null) 'relayPath': relayPath,
      };

  factory MeshMessage.fromJson(Map<String, dynamic> json) => MeshMessage(
        type: MeshMessageTypeExtension.fromString(json['type'] as String),
        payload: Map<String, dynamic>.from(json['payload'] as Map),
        senderId: json['senderId'] as String,
        timestamp: json['timestamp'] as int,
        ttl: json['ttl'] as int? ?? 3,
        signature: json['signature'] as String? ?? '',
        relayPath: json['relayPath'] as String?,
      );

  MeshMessage copyWith({
    MeshMessageType? type,
    Map<String, dynamic>? payload,
    String? senderId,
    int? timestamp,
    int? ttl,
    String? signature,
    String? relayPath,
  }) {
    return MeshMessage(
      type: type ?? this.type,
      payload: payload ?? this.payload,
      senderId: senderId ?? this.senderId,
      timestamp: timestamp ?? this.timestamp,
      ttl: ttl ?? this.ttl,
      signature: signature ?? this.signature,
      relayPath: relayPath ?? this.relayPath,
    );
  }
}

class MeshRouter {
  final Map<String, List<MeshMessage>> _messageStore = {};
  final Set<String> _seenMessages = {};

  void store(String nodeId, MeshMessage message) {
    final msgId = '${message.senderId}_${message.timestamp}_${message.type.value}';
    if (_seenMessages.contains(msgId)) return;
    _seenMessages.add(msgId);
    _messageStore.putIfAbsent(nodeId, () => []).add(message);

    if (_messageStore.length > 1000) {
      final oldest = _messageStore.keys.first;
      _messageStore[oldest]?.removeAt(0);
      if (_messageStore[oldest]?.isEmpty ?? true) {
        _messageStore.remove(oldest);
      }
    }
  }

  List<MeshMessage> getMessagesForRelay(String nodeId) {
    final messages = _messageStore[nodeId];
    if (messages == null) return [];
    return messages.where((m) => m.ttl > 0).toList();
  }

  void clear() {
    _messageStore.clear();
    _seenMessages.clear();
  }
}
