import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class CopScreen extends StatelessWidget {
  const CopScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MilitaryColors.background,
      appBar: AppBar(
        backgroundColor: MilitaryColors.surface,
        title: const Text('COP DASHBOARD', style: TextStyle(color: MilitaryColors.primary, fontSize: 18, fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.satellite_alt, color: MilitaryColors.info),
            onPressed: () => Navigator.of(context).pushNamed('/satellite'),
          ),
          IconButton(
            icon: const Icon(Icons.groups, color: MilitaryColors.warning),
            onPressed: () => Navigator.of(context).pushNamed('/agents'),
          ),
          IconButton(
            icon: const Icon(Icons.assignment, color: MilitaryColors.primary),
            onPressed: () => Navigator.of(context).pushNamed('/mission'),
          ),
          IconButton(
            icon: const Icon(Icons.feed, color: MilitaryColors.textPrimary),
            onPressed: () => Navigator.of(context).pushNamed('/intel'),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: MilitaryColors.classificationRestricted,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text('RESTRICTED // NATO OPEN', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 32),
            const Icon(Icons.map, size: 96, color: MilitaryColors.surfaceLight),
            const SizedBox(height: 16),
            const Text('TACTICAL COP OVERVIEW', style: TextStyle(color: MilitaryColors.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Mesh Connected • 0 Alerts • 1 Active Sensor', style: TextStyle(color: MilitaryColors.textSecondary, fontSize: 13)),
          ],
        ),
      ),
    );
  }
}
