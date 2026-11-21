import 'package:flutter_test/flutter_test.dart';
import 'package:sesis_cop/core/network/mesh_protocol.dart';

void main() {
  const psk = 'test-mesh-psk-32-bytes-long-000000';

  MeshMessage message({
    Map<String, dynamic> payload = const {'text': 'SITREP'},
    int timestamp = 1700000000,
    int ttl = 3,
  }) {
    return MeshMessage(
      type: MeshMessageType.fieldReport,
      payload: payload,
      senderId: 'node-a',
      timestamp: timestamp,
      ttl: ttl,
    );
  }

  group('MeshSigner', () {
    test('firma y verifica un mensaje', () {
      final signer = MeshSigner(psk);
      final signed = message().copyWith(signature: signer.sign(message()));

      expect(signed.signature, isNotEmpty);
      expect(signer.verify(signed), isTrue);
    });

    test('rechaza firma vacía', () {
      expect(MeshSigner(psk).verify(message()), isFalse);
    });

    test('rechaza payload manipulado', () {
      final signer = MeshSigner(psk);
      final original = message();
      final signed = original.copyWith(signature: signer.sign(original));
      final tampered = signed.copyWith(payload: const {'text': 'INJECTED'});

      expect(signer.verify(tampered), isFalse);
    });

    test('rechaza firma con otra PSK', () {
      final signer = MeshSigner(psk);
      final signed = message().copyWith(signature: signer.sign(message()));

      expect(MeshSigner('otra-psk-distinta-000000000000000').verify(signed), isFalse);
    });

    test('firma canónica no depende del orden de claves', () {
      final signer = MeshSigner(psk);
      final a = message(payload: const {'alpha': 1, 'beta': 2});
      final b = message(payload: const {'beta': 2, 'alpha': 1});

      expect(signer.sign(a), signer.sign(b));
    });

    test('handshake válido e inválido', () {
      final signer = MeshSigner(psk);
      final hmac = signer.signHandshake('node-b', 1700000123);

      expect(signer.verifyHandshake('node-b', 1700000123, hmac), isTrue);
      expect(signer.verifyHandshake('node-b', 1700000124, hmac), isFalse);
      expect(signer.verifyHandshake('node-b', 1700000123, ''), isFalse);
    });
  });

  group('MeshMessage serialización', () {
    test('roundtrip toJson/fromJson preserva campos', () {
      final original = message().copyWith(
        signature: 'abc123',
        relayPath: 'node-a,node-b',
        ttl: 2,
      );
      final restored = MeshMessage.fromJson(original.toJson());

      expect(restored.type, original.type);
      expect(restored.payload, original.payload);
      expect(restored.senderId, original.senderId);
      expect(restored.timestamp, original.timestamp);
      expect(restored.ttl, original.ttl);
      expect(restored.signature, original.signature);
      expect(restored.relayPath, original.relayPath);
    });

    test('tipo desconocido cae a intelUpdate', () {
      final json = message().toJson()..['type'] = 'desconocido';
      expect(MeshMessage.fromJson(json).type, MeshMessageType.intelUpdate);
    });
  });

  group('MeshRouter', () {
    test('deduplica mensajes por id lógico', () {
      final router = MeshRouter();
      final msg = message(timestamp: 42);

      router.store('node-x', msg);
      router.store('node-x', msg);

      expect(router.getMessagesForRelay('node-x'), hasLength(1));
    });

    test('filtra mensajes con ttl agotado', () {
      final router = MeshRouter();
      router.store('node-y', message(timestamp: 1, ttl: 3));
      router.store('node-y', message(timestamp: 2, ttl: 0));

      final relay = router.getMessagesForRelay('node-y');
      expect(relay, hasLength(1));
      expect(relay.single.timestamp, 1);
    });

    test('clear vacía el estado', () {
      final router = MeshRouter();
      router.store('node-z', message(timestamp: 7));
      router.clear();

      expect(router.getMessagesForRelay('node-z'), isEmpty);
    });
  });
}
