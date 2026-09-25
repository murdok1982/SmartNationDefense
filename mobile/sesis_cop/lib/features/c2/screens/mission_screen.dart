import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class MissionScreen extends StatelessWidget {
  const MissionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MilitaryColors.background,
      appBar: AppBar(
        title: const Text('MISSION & OPORD', style: TextStyle(color: MilitaryColors.textPrimary)),
        backgroundColor: MilitaryColors.surface,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'ACTIVE OPERATION: VANGUARD SENTINEL',
              style: TextStyle(color: MilitaryColors.primary, fontWeight: FontWeight.bold, fontSize: 18),
            ),
            const SizedBox(height: 12),
            Card(
              color: MilitaryColors.surface,
              child: const Padding(
                padding: EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('1. SITUATION', style: TextStyle(color: MilitaryColors.warning, fontWeight: FontWeight.bold)),
                    SizedBox(height: 4),
                    Text('Northern frontier perimeter surveillance and multi-sensor correlation.', style: TextStyle(color: MilitaryColors.textSecondary)),
                    SizedBox(height: 12),
                    Text('2. MISSION', style: TextStyle(color: MilitaryColors.warning, fontWeight: FontWeight.bold)),
                    SizedBox(height: 4),
                    Text('Maintain unbroken COP synchronization across field units via encrypted mesh.', style: TextStyle(color: MilitaryColors.textSecondary)),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
