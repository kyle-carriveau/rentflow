from datetime import datetime, timedelta
from flask import current_app, request
from flask_login import current_user
import json
from collections import defaultdict, Counter

class SecurityMonitor:
    """
    Security monitoring and alerting system for RE2.
    Analyzes security events and provides real-time threat detection.
    """

    # Threat thresholds
    FAILED_LOGIN_THRESHOLD = 5  # Failed logins within time window
    FAILED_LOGIN_WINDOW_MINUTES = 15
    SESSION_HIJACK_ALERT_THRESHOLD = 1  # Any session hijacking attempt
    SUSPICIOUS_ACTIVITY_THRESHOLD = 10  # Multiple suspicious events

    # Alert levels
    ALERT_INFO = 'info'
    ALERT_WARNING = 'warning'
    ALERT_CRITICAL = 'critical'

    @classmethod
    def analyze_security_threats(cls, company_id=None, hours=24):
        """
        Analyze recent security events for threats and anomalies.

        Returns:
            dict: Security analysis report
        """
        from .models import AuditLogModel
        from . import db

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Build query
        query = db.session.query(AuditLogModel)\
            .filter(AuditLogModel.timestamp >= start_time)\
            .filter(AuditLogModel.category == 'security')

        if company_id:
            query = query.filter(AuditLogModel.company_id == company_id)

        security_events = query.all()

        # Analyze threats
        threats = cls._analyze_failed_logins(security_events)
        threats.update(cls._analyze_session_attacks(security_events))
        threats.update(cls._analyze_suspicious_patterns(security_events))

        # Generate summary
        summary = {
            'analysis_period_hours': hours,
            'total_security_events': len(security_events),
            'threats_detected': len(threats),
            'threat_summary': cls._categorize_threats(threats),
            'threats': list(threats.values()),
            'recommendations': cls._generate_security_recommendations(threats)
        }

        return summary

    @classmethod
    def _analyze_failed_logins(cls, events):
        """Analyze failed login patterns."""
        threats = {}

        # Group failed logins by IP address
        failed_logins_by_ip = defaultdict(list)
        for event in events:
            if event.event_type == 'login_failed':
                failed_logins_by_ip[event.ip_address].append(event)

        # Check for brute force attacks
        for ip, login_events in failed_logins_by_ip.items():
            if len(login_events) >= cls.FAILED_LOGIN_THRESHOLD:
                # Check if within time window
                recent_failures = [
                    e for e in login_events
                    if e.timestamp >= datetime.utcnow() - timedelta(minutes=cls.FAILED_LOGIN_WINDOW_MINUTES)
                ]

                if len(recent_failures) >= cls.FAILED_LOGIN_THRESHOLD:
                    threats[f'brute_force_{ip}'] = {
                        'type': 'brute_force_attack',
                        'severity': cls.ALERT_CRITICAL,
                        'description': f'Potential brute force attack from IP {ip}',
                        'details': {
                            'ip_address': ip,
                            'failed_attempts': len(recent_failures),
                            'time_window_minutes': cls.FAILED_LOGIN_WINDOW_MINUTES,
                            'targeted_emails': list(set([
                                json.loads(e.details).get('email', 'unknown')
                                for e in recent_failures
                                if e.details
                            ]))
                        },
                        'first_seen': min(e.timestamp for e in recent_failures),
                        'last_seen': max(e.timestamp for e in recent_failures),
                        'recommendation': 'Consider blocking IP address and reviewing login security'
                    }

        return threats

    @classmethod
    def _analyze_session_attacks(cls, events):
        """Analyze session-based attacks."""
        threats = {}

        session_attacks = [e for e in events if e.event_type == 'session_hijacking_attempt']

        for event in session_attacks:
            threat_id = f'session_hijack_{event.ip_address}_{event.timestamp.isoformat()}'
            threats[threat_id] = {
                'type': 'session_hijacking',
                'severity': cls.ALERT_CRITICAL,
                'description': f'Session hijacking attempt detected from IP {event.ip_address}',
                'details': {
                    'ip_address': event.ip_address,
                    'user_email': event.user_email,
                    'user_agent': event.user_agent,
                    'session_details': json.loads(event.details) if event.details else {}
                },
                'first_seen': event.timestamp,
                'last_seen': event.timestamp,
                'recommendation': 'Immediately review user session and consider forced logout'
            }

        return threats

    @classmethod
    def _analyze_suspicious_patterns(cls, events):
        """Analyze patterns that might indicate suspicious activity."""
        threats = {}

        # Group events by user
        events_by_user = defaultdict(list)
        for event in events:
            if event.user_email:
                events_by_user[event.user_email].append(event)

        # Look for users with many security events
        for user_email, user_events in events_by_user.items():
            if len(user_events) >= cls.SUSPICIOUS_ACTIVITY_THRESHOLD:
                event_types = Counter(e.event_type for e in user_events)

                threats[f'suspicious_user_{user_email}'] = {
                    'type': 'suspicious_user_activity',
                    'severity': cls.ALERT_WARNING,
                    'description': f'Unusual security activity detected for user {user_email}',
                    'details': {
                        'user_email': user_email,
                        'total_security_events': len(user_events),
                        'event_breakdown': dict(event_types),
                        'unique_ip_addresses': len(set(e.ip_address for e in user_events if e.ip_address))
                    },
                    'first_seen': min(e.timestamp for e in user_events),
                    'last_seen': max(e.timestamp for e in user_events),
                    'recommendation': 'Review user account for potential compromise'
                }

        return threats

    @classmethod
    def _categorize_threats(cls, threats):
        """Categorize threats by type and severity."""
        summary = {
            'by_type': defaultdict(int),
            'by_severity': defaultdict(int)
        }

        for threat in threats.values():
            summary['by_type'][threat['type']] += 1
            summary['by_severity'][threat['severity']] += 1

        return dict(summary)

    @classmethod
    def _generate_security_recommendations(cls, threats):
        """Generate security recommendations based on threats."""
        recommendations = []

        threat_types = [t['type'] for t in threats.values()]

        if 'brute_force_attack' in threat_types:
            recommendations.append({
                'priority': 'high',
                'action': 'Implement IP-based rate limiting',
                'description': 'Consider blocking IPs with repeated failed login attempts'
            })

        if 'session_hijacking' in threat_types:
            recommendations.append({
                'priority': 'critical',
                'action': 'Review session security',
                'description': 'Force logout affected users and review session fingerprinting'
            })

        if len(threats) > 5:
            recommendations.append({
                'priority': 'medium',
                'action': 'Increase monitoring frequency',
                'description': 'Consider more frequent security reviews due to elevated threat activity'
            })

        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'action': 'Continue monitoring',
                'description': 'No immediate threats detected. Continue regular security monitoring.'
            })

        return recommendations

    @classmethod
    def get_security_dashboard_data(cls, company_id=None, days=7):
        """Get data for security dashboard."""
        from .models import AuditLogModel, User
        from . import db

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        # Build base query
        query = db.session.query(AuditLogModel).filter(AuditLogModel.timestamp >= start_time)

        if company_id:
            query = query.filter(AuditLogModel.company_id == company_id)

        all_events = query.all()
        security_events = [e for e in all_events if e.category == 'security']
        auth_events = [e for e in all_events if e.category == 'authentication']

        # Calculate metrics
        dashboard_data = {
            'period_days': days,
            'total_events': len(all_events),
            'security_events': len(security_events),
            'authentication_events': len(auth_events),

            # Event breakdown
            'events_by_category': dict(Counter(e.category for e in all_events)),
            'events_by_severity': dict(Counter(e.severity for e in all_events)),

            # Authentication metrics
            'successful_logins': len([e for e in auth_events if e.event_type == 'login_success']),
            'failed_logins': len([e for e in auth_events if e.event_type == 'login_failed']),
            'password_changes': len([e for e in auth_events if e.event_type == 'password_change']),

            # Security metrics
            'csrf_violations': len([e for e in security_events if e.event_type == 'csrf_violation']),
            'session_timeouts': len([e for e in security_events if e.event_type == 'session_timeout']),
            'suspicious_activity': len([e for e in security_events if 'suspicious' in e.event_type]),

            # Threat analysis
            'threats': cls.analyze_security_threats(company_id, days * 24),

            # Top IPs by activity
            'top_ips': dict(Counter(
                e.ip_address for e in all_events
                if e.ip_address
            ).most_common(10)),

            # Recent critical events
            'recent_critical_events': [
                cls._serialize_event(e) for e in
                sorted([e for e in all_events if e.severity == 'critical'],
                       key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }

        return dashboard_data

    @classmethod
    def _serialize_event(cls, event):
        """Serialize audit event for dashboard."""
        return {
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'category': event.category,
            'severity': event.severity,
            'user_email': event.user_email,
            'ip_address': event.ip_address,
            'details': json.loads(event.details) if event.details else {}
        }

    @classmethod
    def check_real_time_threats(cls):
        """
        Real-time threat detection for current request.
        Called from middleware to detect immediate threats.
        """
        threats = []

        # Check for rapid successive requests (potential DoS)
        if hasattr(request, 'rate_limit_exceeded'):
            threats.append({
                'type': 'rate_limit_exceeded',
                'severity': cls.ALERT_WARNING,
                'description': 'Rate limit exceeded for current IP',
                'immediate_action': True
            })

        # Check for suspicious user agents
        user_agent = request.headers.get('User-Agent', '').lower()
        suspicious_agents = ['bot', 'crawler', 'scanner', 'curl', 'wget']
        if any(agent in user_agent for agent in suspicious_agents):
            threats.append({
                'type': 'suspicious_user_agent',
                'severity': cls.ALERT_INFO,
                'description': f'Suspicious user agent detected: {user_agent}',
                'immediate_action': False
            })

        return threats

    @classmethod
    def generate_security_report(cls, company_id, start_date=None, end_date=None):
        """
        Generate comprehensive security report for a company.

        Args:
            company_id: Company to generate report for
            start_date: Report start date (default: 30 days ago)
            end_date: Report end date (default: now)

        Returns:
            dict: Comprehensive security report
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        from .models import AuditLogModel, User, Company
        from . import db

        company = Company.query.get(company_id)
        if not company:
            return None

        # Get all audit logs for the period
        audit_logs = db.session.query(AuditLogModel)\
            .filter(AuditLogModel.company_id == company_id)\
            .filter(AuditLogModel.timestamp >= start_date)\
            .filter(AuditLogModel.timestamp <= end_date)\
            .all()

        # Get company users
        users = User.query.filter_by(company_id=company_id).all()

        # Generate comprehensive report
        report = {
            'report_metadata': {
                'company_name': company.name,
                'company_id': company_id,
                'report_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'generated_at': datetime.utcnow().isoformat(),
                'total_users': len(users),
                'total_audit_events': len(audit_logs)
            },

            # Security overview
            'security_overview': {
                'threat_level': cls._calculate_threat_level(audit_logs),
                'security_score': cls._calculate_security_score(users, audit_logs),
                'total_security_events': len([e for e in audit_logs if e.category == 'security']),
                'failed_login_attempts': len([e for e in audit_logs if e.event_type == 'login_failed']),
                'successful_logins': len([e for e in audit_logs if e.event_type == 'login_success']),
            },

            # Detailed analysis
            'detailed_analysis': cls.analyze_security_threats(company_id, (end_date - start_date).total_seconds() / 3600),

            # User security status
            'user_security_status': cls._analyze_user_security(users),

            # Compliance metrics
            'compliance_metrics': cls._calculate_compliance_metrics(audit_logs),

            # Recommendations
            'recommendations': cls._generate_company_recommendations(company, users, audit_logs)
        }

        return report

    @classmethod
    def _calculate_threat_level(cls, audit_logs):
        """Calculate overall threat level based on recent events."""
        critical_events = len([e for e in audit_logs if e.severity == 'critical'])
        error_events = len([e for e in audit_logs if e.severity == 'error'])
        warning_events = len([e for e in audit_logs if e.severity == 'warning'])

        if critical_events > 0:
            return 'HIGH'
        elif error_events > 5:
            return 'MEDIUM'
        elif warning_events > 20:
            return 'MEDIUM'
        else:
            return 'LOW'

    @classmethod
    def _calculate_security_score(cls, users, audit_logs):
        """Calculate overall security score (0-100)."""
        score = 100

        # Deduct points for security issues
        critical_events = len([e for e in audit_logs if e.severity == 'critical'])
        failed_logins = len([e for e in audit_logs if e.event_type == 'login_failed'])

        score -= critical_events * 10  # -10 points per critical event
        score -= min(failed_logins * 2, 20)  # -2 points per failed login, max -20

        # Add points for good security practices
        users_with_2fa = len([u for u in users if getattr(u, 'totp_enabled', False)])
        verified_users = len([u for u in users if getattr(u, 'email_verified', False)])

        if len(users) > 0:
            score += (users_with_2fa / len(users)) * 20  # Up to +20 for 100% 2FA adoption
            score += (verified_users / len(users)) * 10  # Up to +10 for 100% email verification

        return max(0, min(100, int(score)))

    @classmethod
    def _analyze_user_security(cls, users):
        """Analyze security status of users."""
        analysis = {
            'total_users': len(users),
            'email_verified_count': len([u for u in users if getattr(u, 'email_verified', False)]),
            'totp_enabled_count': len([u for u in users if getattr(u, 'totp_enabled', False)]),
            'owner_count': len([u for u in users if u.role == 'owner']),
            'manager_count': len([u for u in users if u.role == 'manager']),
            'staff_count': len([u for u in users if u.role == 'staff']),
            'viewer_count': len([u for u in users if u.role == 'viewer']),
        }

        analysis['security_compliance_percentage'] = (
            (analysis['email_verified_count'] + analysis['totp_enabled_count']) /
            (len(users) * 2) * 100
        ) if users else 0

        return analysis

    @classmethod
    def _calculate_compliance_metrics(cls, audit_logs):
        """Calculate compliance-related metrics."""
        return {
            'total_logged_events': len(audit_logs),
            'data_access_events': len([e for e in audit_logs if e.category == 'data_access']),
            'data_modification_events': len([e for e in audit_logs if e.category == 'data_modification']),
            'authentication_events': len([e for e in audit_logs if e.category == 'authentication']),
            'authorization_events': len([e for e in audit_logs if e.category == 'authorization']),
            'audit_coverage_score': min(100, len(audit_logs) // 10)  # Simple coverage score
        }

    @classmethod
    def _generate_company_recommendations(cls, company, users, audit_logs):
        """Generate security recommendations for the company."""
        recommendations = []

        # Check 2FA adoption
        users_with_2fa = len([u for u in users if getattr(u, 'totp_enabled', False)])
        if users and (users_with_2fa / len(users)) < 0.5:
            recommendations.append({
                'priority': 'high',
                'category': 'authentication',
                'title': 'Increase Two-Factor Authentication Adoption',
                'description': f'Only {users_with_2fa}/{len(users)} users have 2FA enabled. Consider requiring 2FA for all users.'
            })

        # Check email verification
        verified_users = len([u for u in users if getattr(u, 'email_verified', False)])
        if users and (verified_users / len(users)) < 1.0:
            recommendations.append({
                'priority': 'medium',
                'category': 'authentication',
                'title': 'Ensure All Email Addresses Are Verified',
                'description': f'{len(users) - verified_users} users have unverified email addresses.'
            })

        # Check for excessive failed logins
        failed_logins = len([e for e in audit_logs if e.event_type == 'login_failed'])
        if failed_logins > 50:
            recommendations.append({
                'priority': 'high',
                'category': 'security',
                'title': 'Review Failed Login Attempts',
                'description': f'High number of failed login attempts ({failed_logins}) detected. Review for potential attacks.'
            })

        return recommendations