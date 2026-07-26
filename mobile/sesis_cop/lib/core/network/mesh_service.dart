import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:nearby_connections/nearby_connections.dart';

import '../constants.dart';
import '../storage/offline_queue.dart';
import 'mesh_protocol.dart';

enum MeshConnectionState { disconnected, discovering, advertising, connected }

class MeshService {
  static final MeshService _instance = MeshService._();
  factory MeshService() => _instance;
  MeshService._();

  final Nearby _nearby = Nearby();
  final OfflineQueue _offlineQueue = OfflineQueue();
  final MeshRouter _router = MeshRouter();

  final StreamController<MeshMessage> _messageController = StreamController<MeshMessage>.broadcast();
  final ValueNotifier<MeshConnectionState> connectionState = ValueNotifier(MeshConnectionState.disconnected);
  final ValueNotifier<int> peerCount = ValueNotifier(0);

  final Set<String> _authenticatedPeers = {};
  final Set<String> _pendingPeers = {};
  final Set<String> _forwardedMessages = {};

  MeshSigner? _signer;
  String _localId = '';

  Stream<MeshMessage> get messages => _messageController.stream;
  String get endpointId => _localId;
  bool get isConfigured => AppConstants.meshPsk.isNotEmpty;

  Future<bool> initialize() async {
    if (!isConfigured) {
      debugPrint('MeshService: MESH_PSK no configurada (--dart-define=MESH_PSK=...); la malla no arranca.');
      return false;
    }
    _signer = MeshSigner(AppConstants.meshPsk);
    _localId = 'SESIS-${Random.secure().nextInt(1 << 32).toRadixString(16).padLeft(8, '0')}';
    return true;
  }

  Future<void> startAdvertising() async {
    if (_signer == null) return;
    try {
      await _nearby.startAdvertising(
        _localId,
        Strategy.P2P_CLUSTER,
        onConnectionInitiated: _onConnectionInitiated,
        onConnectionResult: _onConnectionResult,
        onDisconnected: _onDisconnected,
        serviceId: AppConstants.defaultMeshServiceId,
      );
      connectionState.value = MeshConnectionState.advertising;
    } catch (e) {
      debugPrint('Advertising failed: $e');
    }
  }

  Future<void> startDiscovery() async {
    if (_signer == null) return;
    try {
      await _nearby.startDiscovery(
        _localId,
        Strategy.P2P_CLUSTER,
        onEndpointFound: _onEndpointDiscovered,
        onEndpointLost: _onEndpointLost,
        serviceId: AppConstants.defaultMeshServiceId,
      );
      connectionState.value = MeshConnectionState.discovering;
    } catch (e) {
      debugPrint('Discovery failed: $e');
    }
  }

  Future<void> sendMessage(MeshMessage message) async {
    final signer = _signer;
    if (signer == null) return;
    final signed = message.signature.isEmpty ? message.copyWith(signature: signer.sign(message)) : message;
    if (_authenticatedPeers.isEmpty) {
      await _offlineQueue.enqueue(signed);
      return;
    }
    final bytes = utf8.encode(jsonEncode(signed.toJson()));
    var delivered = false;
    for (final endpoint in _authenticatedPeers) {
      try {
        await _nearby.sendBytesPayload(endpoint, Uint8List.fromList(bytes));
        delivered = true;
      } catch (e) {
        debugPrint('Send failed to $endpoint: $e');
      }
    }
    if (!delivered) {
      await _offlineQueue.enqueue(signed);
    }
  }

  Future<void> flushQueue() async {
    if (_authenticatedPeers.isEmpty) return;
    final pending = await _offlineQueue.pending();
    for (final item in pending) {
      try {
        final bytes = utf8.encode(jsonEncode(item.message.toJson()));
        for (final endpoint in _authenticatedPeers) {
          await _nearby.sendBytesPayload(endpoint, Uint8List.fromList(bytes));
        }
        await _offlineQueue.remove(item.id);
      } catch (e) {
        debugPrint('Flush failed for queued message ${item.id}: $e');
        return;
      }
    }
  }

  Future<void> disconnect() async {
    try {
      await _nearby.stopAdvertising();
      await _nearby.stopDiscovery();
      await _nearby.stopAllEndpoints();
      _authenticatedPeers.clear();
      _pendingPeers.clear();
      peerCount.value = 0;
      connectionState.value = MeshConnectionState.disconnected;
    } catch (e) {
      debugPrint('Disconnect error: $e');
    }
  }

  void _onEndpointDiscovered(String endpointId, String name, String serviceId) {
    _nearby
        .requestConnection(
          _localId,
          endpointId,
          onConnectionInitiated: _onConnectionInitiated,
          onConnectionResult: _onConnectionResult,
          onDisconnected: _onDisconnected,
        )
        .catchError((e) {
      debugPrint('Connection request failed: $e');
      return false;
    });
  }

  void _onEndpointLost(String? endpointId) {
    if (endpointId == null) return;
    _authenticatedPeers.remove(endpointId);
    _pendingPeers.remove(endpointId);
    peerCount.value = _authenticatedPeers.length;
  }

  void _onConnectionInitiated(String endpointId, ConnectionInfo info) {
    _pendingPeers.add(endpointId);
    _nearby
        .acceptConnection(
          endpointId,
          onPayLoadRecieved: _onPayload,
          onPayloadTransferUpdate: (id, update) {},
        )
        .catchError((e) {
      debugPrint('Accept failed: $e');
      _pendingPeers.remove(endpointId);
      return false;
    });
  }

  void _onConnectionResult(String endpointId, Status status) {
    if (status == Status.CONNECTED) {
      _sendHandshake(endpointId);
    } else {
      _pendingPeers.remove(endpointId);
    }
  }

  Future<void> _sendHandshake(String endpointId) async {
    final signer = _signer;
    if (signer == null) return;
    final ts = DateTime.now().millisecondsSinceEpoch;
    final handshake = jsonEncode({
      'handshake': true,
      'id': _localId,
      'ts': ts,
      'hmac': signer.signHandshake(_localId, ts),
    });
    try {
      await _nearby.sendBytesPayload(endpointId, Uint8List.fromList(utf8.encode(handshake)));
    } catch (e) {
      debugPrint('Handshake send failed to $endpointId: $e');
    }
  }

  void _onDisconnected(String endpointId) {
    _authenticatedPeers.remove(endpointId);
    _pendingPeers.remove(endpointId);
    peerCount.value = _authenticatedPeers.length;
    if (_authenticatedPeers.isEmpty && connectionState.value == MeshConnectionState.connected) {
      connectionState.value = MeshConnectionState.disconnected;
    }
  }

  bool _withinTolerance(int timestamp) {
    final now = DateTime.now().millisecondsSinceEpoch;
    final tolerance = AppConstants.meshTimestampToleranceSeconds * 1000;
    return (now - timestamp).abs() <= tolerance;
  }

  void _onPayload(String endpointId, Payload payload) {
    final signer = _signer;
    if (signer == null) return;
    final bytes = payload.bytes;
    if (bytes == null) return;

    Map<String, dynamic> json;
    try {
      json = jsonDecode(utf8.decode(bytes)) as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Payload decode error from $endpointId: $e');
      return;
    }

    if (json['handshake'] == true) {
      _handleHandshake(endpointId, json, signer);
      return;
    }

    if (!_authenticatedPeers.contains(endpointId)) {
      debugPrint('Descartado payload de peer no autenticado: $endpointId');
      return;
    }

    try {
      final message = MeshMessage.fromJson(json);
      if (!_withinTolerance(message.timestamp)) {
        debugPrint('Descartado mensaje fuera de ventana temporal (replay?): ${message.senderId}');
        return;
      }
      if (!signer.verify(message)) {
        debugPrint('Descartado mensaje con firma invalida de ${message.senderId}');
        return;
      }
      _messageController.add(message);
      _router.store(endpointId, message);
      _forwardMessage(message);
    } catch (e) {
      debugPrint('Payload processing error: $e');
    }
  }

  void _handleHandshake(String endpointId, Map<String, dynamic> json, MeshSigner signer) {
    final id = json['id'] as String?;
    final ts = json['ts'] as int?;
    final hmac = json['hmac'] as String?;
    if (id == null || ts == null || hmac == null) {
      debugPrint('Handshake malformado de $endpointId');
      return;
    }
    if (!_withinTolerance(ts)) {
      debugPrint('Handshake fuera de ventana temporal de $endpointId');
      return;
    }
    if (!signer.verifyHandshake(id, ts, hmac)) {
      debugPrint('Handshake con HMAC invalido de $endpointId');
      return;
    }
    _pendingPeers.remove(endpointId);
    if (_authenticatedPeers.add(endpointId)) {
      peerCount.value = _authenticatedPeers.length;
      connectionState.value = MeshConnectionState.connected;
      flushQueue();
    }
  }

  void _forwardMessage(MeshMessage message) {
    final signer = _signer;
    if (signer == null) return;
    if (message.ttl > 0 && _authenticatedPeers.length > 1) {
      final msgId = '${message.senderId}_${message.timestamp}_${message.type.value}';
      if (!_forwardedMessages.add(msgId)) return;
      if (_forwardedMessages.length > 5000) {
        _forwardedMessages.clear();
      }
      final forwarded = message.copyWith(
        ttl: message.ttl - 1,
        signature: '',
      );
      final resigned = forwarded.copyWith(signature: signer.sign(forwarded));
      sendMessage(resigned);
    }
  }

  void dispose() {
    disconnect();
    _messageController.close();
  }
}
