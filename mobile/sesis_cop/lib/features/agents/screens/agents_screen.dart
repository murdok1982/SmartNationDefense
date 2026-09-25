import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class AgentsScreen extends StatelessWidget {
  const AgentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MilitaryColors.background,
      appBar: AppBar(
        title: const Text('DEPLOYED AGENTS', style: TextStyle(color: MilitaryColors.textPrimary)),
        backgroundColor: MilitaryColors.surface,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          ListTile(
            tileColor: MilitaryColors.surface,
            leading: Icon(Icons.psychology, color: MilitaryColors.primary),
            title: Text('Agent Sentinel-01', style: TextStyle(color: MilitaryColors.textPrimary)),
            subtitle: Text('Task: Ingestion & Telemetry Parser • ONLINE', style: TextStyle(color: MilitaryColors.textSecondary)),
          ),
          SizedBox(height: 8),
          ListTile(
            tileColor: MilitaryColors.surface,
            leading: Icon(Icons.radar, color: MilitaryColors.info),
            title: Text('Agent Recon-02', style: TextStyle(color: MilitaryColors.textPrimary)),
            subtitle: Text('Task: Drone Stream Monitor • IDLE', style: TextStyle(color: MilitaryColors.textSecondary)),
          ),
        ],
      ),
    );
  }
}
