import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

import '../network/mesh_protocol.dart';

/// Elemento en cola: mensaje firmado + metadatos de persistencia.
class QueuedMeshMessage {
  final String id;
  final MeshMessage message;
  final DateTime queuedAt;

  const QueuedMeshMessage({
    required this.id,
    required this.message,
    required this.queuedAt,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'queued_at': queuedAt.toUtc().toIso8601String(),
        'message': message.toJson(),
      };

  factory QueuedMeshMessage.fromJson(Map<String, dynamic> json) {
    return QueuedMeshMessage(
      id: json['id'] as String,
      message: MeshMessage.fromJson(
        Map<String, dynamic>.from(json['message'] as Map),
      ),
      queuedAt: DateTime.tryParse(json['queued_at'] as String? ?? '') ??
          DateTime.now().toUtc(),
    );
  }
}

/// Cola offline persistente del mesh táctico.
///
/// Los mensajes firmados se guardan en el almacenamiento privado de la app
/// (`getApplicationDocumentsDirectory`) para sobrevivir a reinicios y a la
/// pérdida de conectividad. La cola está acotada ([maxItems]) para evitar
/// crecimiento sin límite en escenarios de aislamiento prolongado y se
/// escribe de forma atómica (fichero temporal + rename).
class OfflineQueue {
  static const String _fileName = 'mesis_offline_queue.json';
  static const int maxItems = 500;

  List<QueuedMeshMessage>? _cache;
  Future<void> _writeLock = Future.value();

  Future<File> _file() async {
    final dir = await getApplicationDocumentsDirectory();
    return File('${dir.path}/$_fileName');
  }

  Future<List<QueuedMeshMessage>> _load() async {
    final cached = _cache;
    if (cached != null) return cached;

    try {
      final file = await _file();
      if (!await file.exists()) {
        _cache = <QueuedMeshMessage>[];
        return _cache!;
      }
      final raw = await file.readAsString();
      if (raw.trim().isEmpty) {
        _cache = <QueuedMeshMessage>[];
        return _cache!;
      }
      final decoded = jsonDecode(raw) as List<dynamic>;
      _cache = decoded
          .whereType<Map>()
          .map((item) => QueuedMeshMessage.fromJson(
                Map<String, dynamic>.from(item),
              ))
          .toList();
    } catch (error) {
      // Un fichero corrupto no debe tumbar el mesh: se descarta la cola.
      debugPrint('OfflineQueue: cola corrupta, se reinicia ($error)');
      _cache = <QueuedMeshMessage>[];
    }
    return _cache!;
  }

  Future<void> _persist(List<QueuedMeshMessage> items) async {
    _cache = items;
    _writeLock = _writeLock.then((_) async {
      try {
        final file = await _file();
        final tmp = File('${file.path}.tmp');
        await tmp.writeAsString(
          jsonEncode(items.map((e) => e.toJson()).toList()),
          flush: true,
        );
        await tmp.rename(file.path);
      } catch (error) {
        debugPrint('OfflineQueue: no se pudo persistir ($error)');
      }
    });
    await _writeLock;
  }

  Future<void> enqueue(MeshMessage message) async {
    final items = List<QueuedMeshMessage>.from(await _load());
    final id =
        '${message.senderId}_${message.timestamp}_${message.type.value}_${items.length}';
    items.add(QueuedMeshMessage(
      id: id,
      message: message,
      queuedAt: DateTime.now().toUtc(),
    ));
    if (items.length > maxItems) {
      items.removeRange(0, items.length - maxItems);
    }
    await _persist(items);
  }

  Future<List<QueuedMeshMessage>> pending() async {
    final items = await _load();
    return List<QueuedMeshMessage>.unmodifiable(items);
  }

  Future<void> remove(String id) async {
    final items = List<QueuedMeshMessage>.from(await _load());
    items.removeWhere((item) => item.id == id);
    await _persist(items);
  }

  Future<void> clear() async {
    await _persist(<QueuedMeshMessage>[]);
  }

  Future<int> size() async => (await _load()).length;
}
