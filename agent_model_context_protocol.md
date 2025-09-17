# AI Agent Model Context Protocol

## Overview

This document defines the structured context format that the AI Agent uses to generate human-readable alerts and status messages. The protocol ensures consistent, actionable, and appropriately detailed communications for different stakeholder groups.

## Context Structure

### 1. Core Context Schema

```json
{
  "context_version": "1.0",
  "timestamp": "ISO-8601 timestamp",
  "context_id": "unique identifier",
  "context_type": "alert|status|report|notification",
  
  "campaign_context": {
    "campaign_id": "string",
    "campaign_name": "string", 
    "priority": "critical|high|medium|low",
    "launch_date": "ISO-8601 date",
    "products": ["array of product names"],
    "target_regions": ["array of region codes"],
    "target_audience": "string description",
    "budget_allocated": "number (USD)",
    "expected_roi": "number (percentage)"
  },
  
  "system_context": {
    "environment": "production|staging|development",
    "system_health": "healthy|degraded|critical",
    "active_campaigns": "number",
    "queue_depth": "number",
    "processing_rate": "number (per minute)",
    "error_rate": "number (percentage)",
    "uptime": "number (seconds)",
    "last_deployment": "ISO-8601 timestamp"
  },
  
  "issue_context": {
    "issue_id": "unique identifier",
    "issue_type": "string",
    "severity": "critical|high|medium|low",
    "detected_at": "ISO-8601 timestamp",
    "affected_components": ["array of component names"],
    "impact_scope": "string description",
    "root_cause": "string description",
    "estimated_resolution": "ISO-8601 timestamp"
  },
  
  "metrics_context": {
    "current_metrics": {},
    "baseline_metrics": {},
    "deviation_percentage": {},
    "trend": "improving|stable|degrading"
  },
  
  "stakeholder_context": {
    "recipient_role": "executive|creative_lead|ad_ops|it|legal",
    "communication_channel": "email|slack|dashboard|sms",
    "detail_level": "executive|operational|technical",
    "previous_communications": ["array of previous message IDs"],
    "escalation_level": "number (1-5)"
  },
  
  "recommendation_context": {
    "immediate_actions": ["array of action items"],
    "long_term_solutions": ["array of solutions"],
    "required_approvals": ["array of approval items"],
    "estimated_costs": {},
    "expected_outcomes": {}
  }
}
```

## Field Definitions

### Campaign Context Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `campaign_id` | string | Yes | Unique campaign identifier | "summer_sale_2024" |
| `campaign_name` | string | Yes | Human-readable campaign name | "Summer Flash Sale" |
| `priority` | enum | Yes | Campaign priority level | "critical" |
| `launch_date` | ISO-8601 | Yes | Scheduled launch date | "2024-09-20T00:00:00Z" |
| `products` | array | Yes | Products in campaign | ["sunglasses", "beachwear"] |
| `target_regions` | array | Yes | Target market codes | ["US", "UK", "DE"] |
| `target_audience` | string | No | Audience description | "Adults 25-45" |
| `budget_allocated` | number | No | Campaign budget in USD | 50000 |
| `expected_roi` | number | No | Expected ROI percentage | 250 |

### System Context Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `environment` | enum | Yes | Deployment environment | "production" |
| `system_health` | enum | Yes | Overall system status | "degraded" |
| `active_campaigns` | number | Yes | Currently processing | 12 |
| `queue_depth` | number | Yes | Items awaiting processing | 45 |
| `processing_rate` | number | Yes | Items per minute | 10.5 |
| `error_rate` | number | Yes | Error percentage | 2.3 |
| `uptime` | number | No | Seconds since last restart | 86400 |
| `last_deployment` | ISO-8601 | No | Last code deployment | "2024-09-15T10:00:00Z" |

### Issue Context Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `issue_id` | string | Yes | Unique issue identifier | "ISS-2024-091701" |
| `issue_type` | string | Yes | Category of issue | "api_rate_limit" |
| `severity` | enum | Yes | Issue severity level | "critical" |
| `detected_at` | ISO-8601 | Yes | When issue was detected | "2024-09-17T14:30:00Z" |
| `affected_components` | array | Yes | Affected system parts | ["image_generator", "api_client"] |
| `impact_scope` | string | Yes | Description of impact | "4 campaigns delayed" |
| `root_cause` | string | No | Identified root cause | "Provider capacity limit" |
| `estimated_resolution` | ISO-8601 | No | Expected fix time | "2024-09-17T18:00:00Z" |

## Redaction Rules

### PII Protection
```python
redaction_patterns = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "api_key": r"(api[_-]?key|apikey|api_secret)[\s:=]+[\w-]+",
}

def redact_pii(text):
    for pattern_name, pattern in redaction_patterns.items():
        text = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", text)
    return text
```

### Sensitive Data Rules

| Data Type | Redaction Rule | Example Output |
|-----------|---------------|----------------|
| API Keys | Full redaction | `[REDACTED_API_KEY]` |
| Passwords | Full redaction | `[REDACTED_PASSWORD]` |
| Customer Names | Partial masking | `John D***` |
| Email Addresses | Domain preserved | `***@company.com` |
| IP Addresses | Last octet masked | `192.168.1.***` |
| File Paths | User directory hidden | `/home/***/project/` |
| Database URLs | Password removed | `postgres://user:***@host/db` |

## Alert Generation Examples

### Example 1: Good Alert (Actionable, Clear, Contextual)

**Context Input:**
```json
{
  "context_type": "alert",
  "issue_context": {
    "issue_type": "insufficient_variants",
    "severity": "high",
    "impact_scope": "Summer Sale campaign missing 2 aspect ratios"
  },
  "campaign_context": {
    "campaign_name": "Summer Flash Sale",
    "launch_date": "2024-09-20T00:00:00Z"
  },
  "recommendation_context": {
    "immediate_actions": ["Generate missing 9:16 and 16:9 variants"],
    "estimated_costs": {"additional_generation": 0.60}
  }
}
```

**Generated Alert:**
```
🔔 HIGH PRIORITY: Summer Flash Sale Campaign Alert

Issue: Missing creative variants detected
Impact: Campaign requires 2 additional aspect ratios (9:16, 16:9)
Launch Risk: 3 days until launch (Sept 20)

Action Required:
✓ Generate missing variants (est. $0.60)
✓ No approval needed - within budget

[Generate Now] [View Campaign] [Dismiss]
```

### Example 2: Bad Alert (Noisy, Vague, Non-actionable)

**What NOT to generate:**
```
❌ SYSTEM ALERT ❌

Something went wrong with a campaign.
Multiple errors detected in the system.
Please check the dashboard for more information.
Various issues may be affecting performance.
Contact support if problems persist.
```

**Problems:**
- No specific campaign identified
- Vague description ("something went wrong")
- No clear action items
- No severity indication
- No timeline or urgency

### Example 3: Role-Specific Alert Formatting

**For Executive (High-level, Business Impact):**
```json
{
  "stakeholder_context": {
    "recipient_role": "executive",
    "detail_level": "executive"
  }
}
```

**Generated Message:**
```
Campaign Status Update - Executive Summary

• 4 campaigns at risk: $125K revenue impact
• Root cause: GenAI capacity constraints  
• Recommended action: Approve $10K emergency provisioning
• Decision needed by: 5 PM today

[Approve] [Schedule Discussion] [View Details]
```

**For IT Department (Technical, Detailed):**
```json
{
  "stakeholder_context": {
    "recipient_role": "it",
    "detail_level": "technical"
  }
}
```

**Generated Message:**
```
Technical Alert - API Rate Limit Exceeded

Endpoint: api.openai.com/v1/images/generations
Error Code: 429 (Too Many Requests)
Current Rate: 25 req/min (down from 100)
Queue Depth: 45 pending
Retry After: 60 seconds

Mitigation Applied:
- Exponential backoff enabled
- Failover to Stability AI (40% capacity)
- Cache hit ratio increased to 70%

Action: Consider implementing request batching
```

## Status Message Templates

### Campaign Progress Status
```python
template = """
Campaign: {campaign_name}
Status: {status}
Progress: {progress_bar} {percentage}%
Variants: {completed}/{total}
ETA: {estimated_completion}
Cost: ${cost:.2f}
"""
```

### System Health Status
```python
template = """
System Health: {health_emoji} {health_status}
Active Campaigns: {active_count}
Processing Rate: {rate:.1f}/min
Queue: {queue_depth} pending
Errors: {error_rate:.1%}
Uptime: {uptime_hours}h
"""
```

### Daily Summary Status
```python
template = """
Daily Summary - {date}

Campaigns Processed: {campaigns_completed}
Assets Generated: {assets_created}
Success Rate: {success_rate:.1%}
Total Cost: ${total_cost:.2f}
Avg Generation Time: {avg_time:.1f}s

Top Issues:
{top_issues_list}

Upcoming:
{upcoming_campaigns_list}
"""
```

## Severity Level Mappings

| Severity | SLA Response | Channels | Escalation | Color Code |
|----------|--------------|----------|------------|------------|
| Critical | < 15 min | SMS, Email, Slack, Phone | Immediate | 🔴 Red |
| High | < 1 hour | Email, Slack | After 30 min | 🟠 Orange |
| Medium | < 4 hours | Email, Dashboard | After 2 hours | 🟡 Yellow |
| Low | < 24 hours | Dashboard | None | 🟢 Green |
| Info | Best effort | Dashboard | None | 🔵 Blue |

## Communication Channel Rules

### Email Rules
- Subject line must include severity emoji and issue type
- Executive emails limited to 5 paragraphs
- Technical emails can include code snippets
- Always include unsubscribe link

### Slack Rules
- Use thread for updates on same issue
- Mention relevant users based on severity
- Include actionable buttons when possible
- Limit message to 500 characters

### SMS Rules
- Only for critical severity
- Maximum 160 characters
- Include ticket ID and callback number
- No PII in messages

### Dashboard Rules
- Auto-refresh every 30 seconds
- Visual indicators for severity
- Clickable elements for details
- Export functionality for reports

## Noise Reduction Strategies

### Deduplication Rules
```python
def should_deduplicate(new_alert, existing_alerts):
    for existing in existing_alerts:
        if (new_alert.issue_type == existing.issue_type and
            new_alert.campaign_id == existing.campaign_id and
            time_diff(new_alert, existing) < 300):  # 5 minutes
            return True
    return False
```

### Aggregation Rules
- Combine similar alerts within 5-minute window
- Group by campaign when multiple issues
- Summarize repeated errors into single alert
- Batch non-critical notifications hourly

### Filtering Rules
```python
alert_filters = {
    "executive": lambda a: a.severity in ["critical", "high"],
    "creative_lead": lambda a: a.affects_creative,
    "ad_ops": lambda a: a.affects_campaigns,
    "it": lambda a: True,  # IT sees all
    "legal": lambda a: a.compliance_related
}
```

## Validation Requirements

### Required Context Validation
```python
def validate_context(context):
    required_fields = [
        "context_version",
        "timestamp",
        "context_type",
        "campaign_context.campaign_id",
        "system_context.system_health",
        "stakeholder_context.recipient_role"
    ]
    
    for field in required_fields:
        if not get_nested_field(context, field):
            raise ValidationError(f"Missing required field: {field}")
    
    return True
```

### Output Validation
```python
def validate_output(generated_message):
    checks = {
        "max_length": len(generated_message) <= 2000,
        "has_action": "action" in generated_message.lower(),
        "has_severity": any(sev in generated_message for sev in ["critical", "high", "medium", "low"]),
        "no_pii": not contains_pii(generated_message),
        "proper_format": is_properly_formatted(generated_message)
    }
    
    return all(checks.values()), checks
```

## Performance Metrics

### Alert Quality Metrics
- **Actionability Rate**: % of alerts with clear actions
- **False Positive Rate**: % of alerts that didn't require action
- **Response Time**: Average time to acknowledge
- **Resolution Time**: Average time to resolve
- **Noise Ratio**: Duplicate alerts / Total alerts

### Target Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Actionability | >90% | 92% | ✅ |
| False Positives | <5% | 3% | ✅ |
| Response Time | <30min | 25min | ✅ |
| Resolution Time | <2hr | 1.5hr | ✅ |
| Noise Ratio | <10% | 7% | ✅ |

## Implementation Examples

### Python Implementation
```python
class AlertContextBuilder:
    def __init__(self):
        self.context = {
            "context_version": "1.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def add_campaign(self, campaign):
        self.context["campaign_context"] = {
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "priority": campaign.priority,
            "launch_date": campaign.launch_date.isoformat()
        }
        return self
    
    def add_issue(self, issue):
        self.context["issue_context"] = {
            "issue_type": issue.type,
            "severity": issue.severity,
            "impact_scope": issue.get_impact_description()
        }
        return self
    
    def build(self):
        validate_context(self.context)
        return self.context

class AlertGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def generate(self, context):
        prompt = self._build_prompt(context)
        message = self.llm.generate(prompt)
        message = redact_pii(message)
        
        valid, checks = validate_output(message)
        if not valid:
            raise GenerationError(f"Invalid output: {checks}")
        
        return message
```

## Testing & Validation

### Test Cases
```python
test_cases = [
    {
        "name": "Critical API Failure",
        "context": {...},
        "expected_severity": "critical",
        "expected_actions": ["switch_provider", "notify_executive"]
    },
    {
        "name": "Minor Delay Warning",
        "context": {...},
        "expected_severity": "low",
        "expected_actions": ["monitor", "log"]
    }
]
```

### Validation Checklist
- [ ] All required fields present
- [ ] PII properly redacted
- [ ] Appropriate severity level
- [ ] Clear action items included
- [ ] Correct stakeholder targeting
- [ ] Message under length limit
- [ ] No duplicate alerts generated
- [ ] Proper channel selected

## Future Enhancements

1. **Machine Learning Optimization**
   - Learn from alert acknowledgment patterns
   - Predict optimal send times
   - Auto-tune severity thresholds

2. **Natural Language Improvements**
   - Multi-language support
   - Sentiment analysis for tone
   - Dynamic vocabulary based on recipient

3. **Advanced Context**
   - Historical pattern inclusion
   - Predictive impact assessment
   - Cost-benefit analysis automation

4. **Integration Expansions**
   - JIRA ticket creation
   - PagerDuty escalation
   - Teams/Discord support
   - Voice call integration