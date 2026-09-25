import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class DuressScreen extends StatelessWidget {
  const DuressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MilitaryColors.background,
      appBar: AppBar(
        title: const Text('DURESS PROTOCOL', style: TextStyle(color: MilitaryColors.error, fontWeight: FontWeight.bold)),
        backgroundColor: MilitaryColors.surface,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.warning_amber_rounded, size: 80, color: MilitaryColors.error),
            const SizedBox(height: 24),
            const Text(
              'COVERT SILENT ALARM',
              style: TextStyle(color: MilitaryColors.textPrimary, fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            const Text(
              'Entering duress PIN will simulate normal login while transmitting high-priority distress beacon via mesh protocol.',
              textAlign: TextAlign.center,
              style: TextStyle(color: MilitaryColors.textSecondary, fontSize: 14),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: MilitaryColors.error),
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('CANCEL & RETURN', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }
}
