import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class SatelliteScreen extends StatelessWidget {
  const SatelliteScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MilitaryColors.background,
      appBar: AppBar(
        title: const Text('SATELLITE / IMINT', style: TextStyle(color: MilitaryColors.textPrimary)),
        backgroundColor: MilitaryColors.surface,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.satellite_outlined, size: 80, color: MilitaryColors.info),
            SizedBox(height: 16),
            Text(
              'SENTINEL-2 / LANDSAT PASSES',
              style: TextStyle(color: MilitaryColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 8),
            Text(
              'Next scheduled pass: T+03:42:15\nChange detection engine armed.',
              textAlign: TextAlign.center,
              style: TextStyle(color: MilitaryColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}
