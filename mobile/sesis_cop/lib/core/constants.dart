class AppConstants {
  AppConstants._();

  static const String appName = 'SESIS-COP';
  static const String version = '1.0.0';
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
  static const String wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'ws://10.0.2.2:8000/ws',
  );
  static const String meshPsk = String.fromEnvironment('MESH_PSK', defaultValue: '');
  static const String tlsPins = String.fromEnvironment('TLS_PINS', defaultValue: '');
  static const int meshTimestampToleranceSeconds = 60;
  static const int connectionTimeout = 15;
  static const int syncIntervalSeconds = 30;
  static const int locationUpdateIntervalMs = 5000;
  static const int meshBeaconIntervalMs = 10000;
  static const int maxOfflineMessages = 1000;
  static const int maxRetryAttempts = 5;

  static const List<String> classificationLevels = [
    'RESTRICTED',
    'CONFIDENTIAL',
    'SECRET',
    'TOP_SECRET',
    'COSMIC_TOP_SECRET',
  ];

  static const Map<String, int> classificationPriority = {
    'RESTRICTED': 0,
    'CONFIDENTIAL': 1,
    'SECRET': 2,
    'TOP_SECRET': 3,
    'COSMIC_TOP_SECRET': 4,
  };

  static const String dbName = 'sesis_cop.db';
  static const int dbVersion = 1;
  static const String secureStorageKey = 'sesis_cop_vault';
  static const String defaultMeshServiceId = 'sesis-mesh';
  static const String cryptoAlgorithm = 'AES-256-GCM';
  static const String kyberVariant = 'Kyber768';
}
