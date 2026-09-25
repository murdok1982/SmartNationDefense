import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  void _login() {
    setState(() => _isLoading = true);
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) {
        setState(() => _isLoading = false);
        Navigator.of(context).pushReplacementNamed('/cop');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MilitaryColors.background,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.shield, size: 72, color: MilitaryColors.primary),
              const SizedBox(height: 16),
              const Text(
                'SESIS-COP',
                style: TextStyle(
                  color: MilitaryColors.textPrimary,
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                ),
              ),
              const Text(
                'Common Operating Picture',
                style: TextStyle(color: MilitaryColors.textSecondary, fontSize: 14),
              ),
              const SizedBox(height: 36),
              TextField(
                controller: _usernameController,
                style: const TextStyle(color: MilitaryColors.textPrimary),
                decoration: const InputDecoration(
                  labelText: 'Operator ID',
                  prefixIcon: Icon(Icons.person, color: MilitaryColors.primary),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                obscureText: true,
                style: const TextStyle(color: MilitaryColors.textPrimary),
                decoration: const InputDecoration(
                  labelText: 'Credential',
                  prefixIcon: Icon(Icons.lock, color: MilitaryColors.primary),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: MilitaryColors.primary),
                  onPressed: _isLoading ? null : _login,
                  child: _isLoading
                      ? const CircularProgressIndicator(color: MilitaryColors.background)
                      : const Text('AUTHENTICATE', style: TextStyle(color: MilitaryColors.background, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => Navigator.of(context).pushNamed('/duress'),
                child: const Text('EMERGENCY DURESS PROTOCOL', style: TextStyle(color: MilitaryColors.error, fontSize: 12)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
