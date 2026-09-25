import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class IntelFeedScreen extends StatelessWidget {
  const IntelFeedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MilitaryColors.background,
      appBar: AppBar(
        title: const Text('INTEL FEED', style: TextStyle(color: MilitaryColors.textPrimary)),
        backgroundColor: MilitaryColors.surface,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildIntelCard(
            'SITREP 2026-09-25 #01',
            'Border Sector Alpha monitoring indicates standard telemetry. No anomalous EW signatures detected.',
            'RESTRICTED',
            '10m ago',
          ),
          const SizedBox(height: 12),
          _buildIntelCard(
            'OSINT ATALAYA BRIEFING',
            'Open source news aggregation completed for regional maritime traffic. 14 vessels tracked.',
            'UNCLASSIFIED',
            '25m ago',
          ),
        ],
      ),
    );
  }

  Widget _buildIntelCard(String title, String summary, String clearance, String time) {
    return Card(
      color: MilitaryColors.surface,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(title, style: const TextStyle(color: MilitaryColors.primary, fontWeight: FontWeight.bold, fontSize: 16)),
                Text(time, style: const TextStyle(color: MilitaryColors.textMuted, fontSize: 12)),
              ],
            ),
            const SizedBox(height: 8),
            Text(summary, style: const TextStyle(color: MilitaryColors.textPrimary, fontSize: 14)),
            const SizedBox(height: 8),
            Chip(
              label: Text(clearance, style: const TextStyle(color: Colors.white, fontSize: 10)),
              backgroundColor: MilitaryColors.classificationRestricted,
              padding: EdgeInsets.zero,
            ),
          ],
        ),
      ),
    );
  }
}
