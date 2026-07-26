import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';
import '../../core/constants.dart';

class ApiClient {
  ApiClient._();
  static final ApiClient _instance = ApiClient._();
  factory ApiClient() => _instance;

  late final http.Client _client = _buildPinnedClient();

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static const String _kAccessToken = 'access_token';
  static const String _kRefreshToken = 'refresh_token';

  String? _memoryAccessToken;
  String? _memoryRefreshToken;
  bool _secureStorageAvailable = true;

  http.Client _buildPinnedClient() {
    if (kIsWeb) return http.Client();
    final pins = AppConstants.tlsPins
        .split(',')
        .map((p) => p.trim().replaceAll(':', '').toLowerCase())
        .where((p) => p.isNotEmpty)
        .toList();
    if (pins.isEmpty) {
      return IOClient(HttpClient());
    }
    final context = SecurityContext(withTrustedRoots: false);
    final httpClient = HttpClient(context: context);
    httpClient.badCertificateCallback = (X509Certificate cert, String host, int port) {
      final fingerprint = sha256.convert(cert.der).toString();
      final valid = pins.contains(fingerprint);
      if (!valid) {
        debugPrint('TLS pinning: certificado rechazado para $host (sha256/$fingerprint)');
      }
      return valid;
    };
    return IOClient(httpClient);
  }

  Future<void> saveTokens({required String accessToken, String? refreshToken}) async {
    _memoryAccessToken = accessToken;
    _memoryRefreshToken = refreshToken;
    if (!_secureStorageAvailable) return;
    try {
      await _secureStorage.write(key: _kAccessToken, value: accessToken);
      if (refreshToken != null) {
        await _secureStorage.write(key: _kRefreshToken, value: refreshToken);
      }
    } catch (e) {
      debugPrint('Secure storage no disponible, usando memoria: $e');
      _secureStorageAvailable = false;
    }
  }

  Future<String?> getAccessToken() async {
    if (_secureStorageAvailable) {
      try {
        final token = await _secureStorage.read(key: _kAccessToken);
        if (token != null) {
          _memoryAccessToken = token;
          return token;
        }
      } catch (e) {
        debugPrint('Secure storage no disponible, usando memoria: $e');
        _secureStorageAvailable = false;
      }
    }
    return _memoryAccessToken;
  }

  Future<String?> getRefreshToken() async {
    if (_secureStorageAvailable) {
      try {
        final token = await _secureStorage.read(key: _kRefreshToken);
        if (token != null) {
          _memoryRefreshToken = token;
          return token;
        }
      } catch (e) {
        debugPrint('Secure storage no disponible, usando memoria: $e');
        _secureStorageAvailable = false;
      }
    }
    return _memoryRefreshToken;
  }

  Future<void> clearTokens() async {
    _memoryAccessToken = null;
    _memoryRefreshToken = null;
    if (_secureStorageAvailable) {
      try {
        await _secureStorage.delete(key: _kAccessToken);
        await _secureStorage.delete(key: _kRefreshToken);
      } catch (e) {
        debugPrint('Secure storage no disponible: $e');
        _secureStorageAvailable = false;
      }
    }
  }

  Future<Map<String, String>> _buildHeaders() async {
    final token = await getAccessToken();
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
      'X-Client-Version': AppConstants.version,
    };
  }

  Future<Map<String, dynamic>> get(String path, {Map<String, String>? queryParams}) async {
    try {
      final uri = Uri.parse('${AppConstants.apiBaseUrl}$path').replace(queryParameters: queryParams);
      final response = await _client.get(uri, headers: await _buildHeaders()).timeout(
        Duration(seconds: AppConstants.connectionTimeout),
      );
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection', 0);
    } on http.ClientException catch (e) {
      throw ApiException(e.message, 0);
    }
  }

  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body}) async {
    try {
      final uri = Uri.parse('${AppConstants.apiBaseUrl}$path');
      final response = await _client.post(uri, headers: await _buildHeaders(), body: body != null ? jsonEncode(body) : null).timeout(
        Duration(seconds: AppConstants.connectionTimeout),
      );
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection', 0);
    } on http.ClientException catch (e) {
      throw ApiException(e.message, 0);
    }
  }

  Future<Map<String, dynamic>> put(String path, {Map<String, dynamic>? body}) async {
    try {
      final uri = Uri.parse('${AppConstants.apiBaseUrl}$path');
      final response = await _client.put(uri, headers: await _buildHeaders(), body: body != null ? jsonEncode(body) : null).timeout(
        Duration(seconds: AppConstants.connectionTimeout),
      );
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection', 0);
    } on http.ClientException catch (e) {
      throw ApiException(e.message, 0);
    }
  }

  Future<Map<String, dynamic>> delete(String path) async {
    try {
      final uri = Uri.parse('${AppConstants.apiBaseUrl}$path');
      final response = await _client.delete(uri, headers: await _buildHeaders()).timeout(
        Duration(seconds: AppConstants.connectionTimeout),
      );
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection', 0);
    } on http.ClientException catch (e) {
      throw ApiException(e.message, 0);
    }
  }

  Map<String, dynamic> _handleResponse(http.Response response) {
    final body = response.body.isNotEmpty ? jsonDecode(response.body) as Map<String, dynamic> : <String, dynamic>{};
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }
    throw ApiException(body['message'] as String? ?? 'Request failed', response.statusCode);
  }

  void dispose() {
    _client.close();
  }
}

class ApiException implements Exception {
  final String message;
  final int statusCode;
  ApiException(this.message, this.statusCode);

  @override
  String toString() => 'ApiException($statusCode): $message';
}
