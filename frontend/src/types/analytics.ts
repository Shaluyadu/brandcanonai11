export interface RuleViolationStat {
  rule_term: string;
  category: string;
  count: number;
  severity: string;
}

export interface AnalyticsOverview {
  compliance_rate: number;
  total_submissions_analyzed: number;
  total_findings_detected: number;
  critical_findings_count: number;
  average_turnaround_hours: number;
  top_violated_rules: RuleViolationStat[];
  violations_by_channel: Record<string, number>;
  violations_by_severity: Record<string, number>;
  submission_status_breakdown: Record<string, number>;
}

