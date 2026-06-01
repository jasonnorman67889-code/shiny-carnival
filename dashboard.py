import csv
import json
import os
from datetime import datetime
from io import StringIO

from flask import Flask, Response, jsonify, render_template, request, g

app = Flask(__name__)

# Simple role-based users. Replace passwords with secure values in production.
users = {
    "admin": {"password": os.getenv("DASHBOARD_ADMIN_PASS", "adminpass"), "role": "admin"},
    "viewer": {"password": os.getenv("DASHBOARD_VIEWER_PASS", "viewerpass"), "role": "viewer"}
}

LOG_JSON_PATH = os.getenv("JSON_LOG_FILE", "email_status_log.json")
SUMMARY_PATH = os.getenv("SUMMARY_FILE", "batch_summary.json")
OPT_OUT_CSV_PATH = os.getenv("OPT_OUT_CSV_PATH", "opt_outs.csv")
OPT_OUT_HISTORY_PATH = os.getenv("OPT_OUT_HISTORY_PATH", "opt_out_history.json")
COMPLIANCE_REPORT_PATH = os.getenv("COMPLIANCE_REPORT_PATH", "compliance_report.json")
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "users.csv")


def load_opt_outs():
    if not os.path.exists(OPT_OUT_CSV_PATH):
        return set()
    with open(OPT_OUT_CSV_PATH, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def append_opt_out(email):
    email = email.strip().lower()
    if not email:
        return

    existing = load_opt_outs()
    if email not in existing:
        with open(OPT_OUT_CSV_PATH, "a", encoding="utf-8") as f:
            f.write(email + "\n")

    history = []
    if os.path.exists(OPT_OUT_HISTORY_PATH):
        with open(OPT_OUT_HISTORY_PATH, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append({"email": email, "timestamp": datetime.now().isoformat()})
    with open(OPT_OUT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def load_opt_out_history():
    if not os.path.exists(OPT_OUT_HISTORY_PATH):
        return []
    with open(OPT_OUT_HISTORY_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def load_compliance_report():
    if not os.path.exists(COMPLIANCE_REPORT_PATH):
        return {}
    with open(COMPLIANCE_REPORT_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def load_batch_summary():
    if not os.path.exists(SUMMARY_PATH):
        return {}
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def load_user_region_data():
    regions = []
    if not os.path.exists(CSV_FILE_PATH):
        return regions
    with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = str(row.get("region", "USA")).strip().upper() or "USA"
            regions.append({
                "email": row.get("email", ""),
                "name": row.get("name", ""),
                "region": region,
                "channel": row.get("channel", "unknown")
            })
    return regions


def summarize_opt_out_history():
    history = load_opt_out_history()
    sorted_history = sorted(history, key=lambda x: x.get("timestamp", ""))
    return sorted_history


def check_auth(username, password):
    return username in users and users[username]["password"] == password


def authenticate():
    html = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>Login Required</title>
  <style>body{font-family:Arial,sans-serif;background:#f8f9fb;color:#111;margin:0;padding:40px;} .page{max-width:480px;margin:auto;background:#fff;border-radius:12px;box-shadow:0 10px 24px rgba(0,0,0,.08);padding:28px;} h1{margin-top:0;color:#111;} p{line-height:1.6;}</style>
</head>
<body>
  <div class=\"page\">
    <h1>Login required</h1>
    <p>Basic authentication is required to access this dashboard.</p>
  </div>
</body>
</html>"""
    return Response(html, 401, {"WWW-Authenticate": 'Basic realm="Login Required"', "Content-Type": "text/html; charset=utf-8"})


@app.before_request
def require_login():
    if request.path == "/unsubscribe":
        return None
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    g.role = users[auth.username]["role"]


def load_log_lines():
    if not os.path.exists(LOG_JSON_PATH):
        return []
    with open(LOG_JSON_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def filter_logs(logs, email=None, status=None, date_from=None, date_to=None):
    filtered = []
    for entry in logs:
        if email and email.lower() not in entry.get("recipient_email", "").lower():
            continue
        if status and status.lower() != entry.get("delivery_status", "").lower():
            continue
        timestamp = entry.get("timestamp")
        if timestamp and (date_from or date_to):
            try:
                dt = datetime.fromisoformat(timestamp)
            except ValueError:
                dt = None
            if dt:
                if date_from and dt < datetime.fromisoformat(date_from):
                    continue
                if date_to and dt > datetime.fromisoformat(date_to):
                    continue
        filtered.append(entry)
    return filtered


@app.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            return render_template("unsubscribe.html", error="Please enter a valid email.")
        append_opt_out(email)
        return render_template("unsubscribe.html", success=True, email=email)
    return render_template("unsubscribe.html")


@app.route("/opt-outs")
def opt_outs():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(summarize_opt_out_history())


@app.route("/compliance-report")
def compliance_report():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(COMPLIANCE_REPORT_PATH):
        return jsonify({"error": "Compliance report not found"}), 404
    with open(COMPLIANCE_REPORT_PATH, "r", encoding="utf-8") as f:
        return Response(f.read(), mimetype="application/json")


@app.route("/")
def index():
    return render_template("dashboard.html")


def load_region_counts_from_logs():
    region_stats = {}
    logs = load_log_lines()
    for entry in logs:
        region = str(entry.get("region", "USA")).strip().upper() or "USA"
        region_stats.setdefault(region, {"region": region, "recipient_count": 0})
        region_stats[region]["recipient_count"] += 1
    return region_stats


def parse_iso_timestamp(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def load_transformation_insights():
    logs = load_log_lines()
    total_events = len(logs)
    success_count = sum(1 for entry in logs if entry.get("delivery_status", "").upper() == "SUCCESS")
    failed_count = sum(1 for entry in logs if entry.get("delivery_status", "").upper() in {"FAILED", "DEFERRED", "SKIPPED"})

    region_counts = {}
    for entry in logs:
        region = str(entry.get("region", "USA")).strip().upper() or "USA"
        region_counts.setdefault(region, 0)
        region_counts[region] += 1

    opt_out_history = load_opt_out_history()
    opt_out_count = len(opt_out_history)
    recent_timestamps = [parse_iso_timestamp(item.get("timestamp", "")) for item in opt_out_history[-5:]]
    recent_timestamps = [ts for ts in recent_timestamps if ts]
    opt_out_trend = "stable"
    if len(recent_timestamps) >= 3:
        intervals = [
            (recent_timestamps[i] - recent_timestamps[i - 1]).total_seconds()
            for i in range(1, len(recent_timestamps))
        ]
        if intervals and sum(intervals) / len(intervals) < 86400:
            opt_out_trend = "accelerating"

    compliance = load_compliance_report()
    pending_regions = [item.get("region") for item in compliance.get("regional_audit", []) if item.get("status") != "Compliant"]

    insights = []
    if opt_out_count and opt_out_trend == "accelerating":
        insights.append({
            "title": "Opt-out Momentum",
            "detail": "Recent unsubscribe activity is accelerating. Consider prioritizing email and push channels over SMS.",
            "type": "risk"
        })
    if failed_count and total_events and failed_count / total_events > 0.1:
        insights.append({
            "title": "Delivery Stability",
            "detail": "Failure rates exceed 10% of recent sends. Investigate delivery issues and channel performance.",
            "type": "alert"
        })
    if pending_regions:
        insights.append({
            "title": "Compliance Oversight",
            "detail": f"Regional compliance review required for: {', '.join(pending_regions)}.",
            "type": "governance"
        })
    if not insights:
        insights.append({
            "title": "Transformation Health",
            "detail": "Campaign and governance signals are stable. Continue monitoring and scale successful strategies.",
            "type": "info"
        })

    actions = []
    if opt_out_count and opt_out_trend == "accelerating":
        actions.append("Shift creative emphasis away from SMS and towards email + push content.")
    if pending_regions:
        actions.append("Align regional campaigns with audit-ready compliance language and review governance status.")
    if not actions:
        actions.append("Maintain current cadence while expanding successful regional campaigns.")

    return {
        "engine_status": "active",
        "total_events": total_events,
        "success_rate": f"{(success_count / total_events * 100) if total_events else 0:.1f}%",
        "opt_out_count": opt_out_count,
        "pending_compliance_regions": pending_regions,
        "region_counts": [{"region": region, "recipient_count": count} for region, count in sorted(region_counts.items())],
        "insights": insights,
        "actions": actions
    }


def build_strategy_nexus():
    transformation = load_transformation_insights()
    summary = load_batch_summary()
    user_regions = load_user_region_data()
    recommendations = []
    if transformation["pending_compliance_regions"]:
        recommendations.append("Embed compliance checkpoint review within every regional campaign launch.")
    if transformation["opt_out_count"] and transformation["opt_out_count"] > 5:
        recommendations.append("Use leadership messaging to reinforce consent and preference controls.")
    if transformation["success_rate"] and float(transformation["success_rate"].rstrip('%')) < 90:
        recommendations.append("Optimize audience targeting and creative for higher deliverability.")
    if not recommendations:
        recommendations.append("Continue aligning campaign execution to market signals and governance priorities.")

    if summary.get("failed_deliveries", 0) > 0:
        recommendations.insert(0, "Investigate failed delivery paths and retry key audience segments.")
    if len(user_regions) > 10:
        recommendations.append("Leverage regional customer data to personalize high-value campaigns.")

    return {
        "nexus_status": "aligned",
        "vision": "Unified strategic intelligence across innovation, compliance, and campaign performance.",
        "recommendations": recommendations,
        "headline_insight": "Leverage the transformation engine to maintain a single enterprise brain for leadership decision-making.",
        "audience_regions": sorted({entry["region"] for entry in user_regions})
    }


def load_transcendent_intelligence_core():
    logs = load_log_lines()
    compliance = load_compliance_report()
    opt_out_count = len(load_opt_out_history())
    region_counts = {}
    for entry in logs:
        region = str(entry.get("region", "USA")).strip().upper() or "USA"
        region_counts.setdefault(region, 0)
        region_counts[region] += 1

    pending_compliance = [item for item in compliance.get("regional_audit", []) if item.get("status") != "Compliant"]
    detected_conditions = [
        "Parallel universe with stricter compliance" if pending_compliance else "No active compliance anomalies",
        "Solar storm forecast in current timeline" if any("storm" in str(item).lower() for item in compliance.get("solar_events", [])) else "No immediate cosmic alerts",
        "Regional audit cycle synchronization mismatch" if len(pending_compliance) > 1 else "Regional compliance cadence stable"
    ]
    resilience_score = int(min(100, 90 + max(0, len(logs) - opt_out_count) * 2 - len(pending_compliance) * 5))
    return {
        "core_status": "transcendent",
        "dimension_layers": ["planetary", "cosmic", "multiversal"],
        "temporal_layers": ["past", "present", "future"],
        "detected_conditions": detected_conditions,
        "core_action": "Harmonize strategies across realities, reschedule campaigns, and preserve universal campaign coherence.",
        "resilience_score": resilience_score,
        "region_activity": [{"region": region, "count": count} for region, count in sorted(region_counts.items())],
        "recommendations": [
            "Harmonize strategies across realities and reschedule sensitive campaigns.",
            "Elevate consent-first messaging for regions with emerging regulatory pressure.",
            "Align planetary campaign signals with cosmic foresight and legacy values."
        ],
        "legacy_alignment": compliance.get("legacy_alignment", "enabled"),
        "pending_compliance_count": len(pending_compliance)
    }


def load_legacy_preservation_framework():
    compliance = load_compliance_report()
    opt_out_count = len(load_opt_out_history())
    pending_regions = [item.get("region") for item in compliance.get("regional_audit", []) if item.get("status") != "Compliant"]
    horizons = [
        {"horizon": "10 years", "priority": "sustainability", "status": "established"},
        {"horizon": "25 years", "priority": "cultural inheritance", "status": "maturing"},
        {"horizon": "50 years", "priority": "strategic archiving", "status": "anchored"},
        {"horizon": "100 years", "priority": "future validation", "status": "future-proofed"}
    ]
    brand_resilience = max(40, 100 - opt_out_count * 10 - len(pending_regions) * 8)
    archive_actions = [
        "Archive sustainability-aligned campaigns to preserve legacy brand trust.",
        "Embed cultural values into campaign playbooks for generational resonance.",
        "Validate new initiatives against long-term legacy and governance goals."
    ]
    if pending_regions:
        archive_actions.insert(0, "Preserve audit-ready records for regions with compliance gaps.")
    century_forecast = "Shift toward eco-minimalism and values-based engagement."
    return {
        "framework_status": "legacy",
        "generation_horizons": horizons,
        "archive_actions": archive_actions,
        "century_forecast": century_forecast,
        "framework_action": "Archive future-aligned campaigns and enforce eco-values across new launches.",
        "brand_resilience_score": brand_resilience,
        "governance_archive": compliance.get("archive_records", []),
        "regulatory_heritage": compliance.get("regulatory_heritage", "maintained"),
        "opt_out_count": opt_out_count,
        "pending_compliance_regions": pending_regions
    }


def load_singularity_governance_matrix():
    compliance = load_compliance_report()
    pending = [item for item in compliance.get("regional_audit", []) if item.get("status") != "Compliant"]
    detected_conditions = [
        "Compliance tightening in Europe" if any(item.get("region") == "EUROPE" for item in pending) else "Europe compliance stable",
        "Cultural shift in Australia" if any(item.get("region") == "AUSTRALIA" for item in pending) else "APAC compliance stable",
        "Campaign tone drift across timelines" if pending else "Campaign tone aligned across regions"
    ]
    health_status = "stable" if not pending else "attention"
    if len(pending) > 2:
        health_status = "at-risk"
    actions = [
        "Harmonize governance rules globally and unify matrix oversight.",
        "Adjust campaign tone for regional cultures while preserving universal alignment.",
        "Maintain a self-sustaining oversight layer with continuous policy reconciliation."
    ]
    return {
        "matrix_status": "singularity",
        "convergence_layers": ["compliance", "foresight", "sustainability", "innovation"],
        "detected_conditions": detected_conditions,
        "matrix_action": "Harmonize governance rules globally, adjust campaign tone, and maintain universal compliance.",
        "result": "Universal compliance maintained, engagement stabilized" if not pending else "Universal compliance review required",
        "recommended_actions": actions,
        "governance_health": health_status,
        "pending_compliance_count": len(pending)
    }


def load_infinite_continuity_engine():
    # Use logs and compliance to compute a continuity resilience index.
    logs = load_log_lines()
    compliance = load_compliance_report()
    total = len(logs)
    success = sum(1 for e in logs if e.get("delivery_status", "").upper() == "SUCCESS")
    success_rate = (success / total * 100) if total else 100

    regional_issues = len([r for r in compliance.get("regional_audit", []) if r.get("status") != "Compliant"]) if isinstance(compliance, dict) else 0

    resilience_index = int(min(100, (success_rate * 0.6) + (100 - regional_issues * 5)))

    metrics = {
        "resilience_index": resilience_index,
        "decay_prevention": "enabled" if resilience_index > 80 else "monitor",
        "future_horizon_years": 500
    }

    actions = [
        "Preserve adaptive campaign frameworks and embed timeless values.",
        "Monitor fidelity metrics continuously and reset governance drift as needed.",
        "Prioritize remediation in regions with active audit items."
    ]

    return {
        "engine_status": "infinite",
        "endless_evolution": True,
        "decay_prevention": metrics["decay_prevention"],
        "continuity_forecast": "500 years of cultural shifts toward digital minimalism",
        "engine_action": "Preserve adaptive campaign frameworks and embed timeless values.",
        "result": "Governance and engagement remain resilient based on current signals",
        "metrics": metrics,
        "recommended_actions": actions
    }


def load_cosmic_eternal_nexus():
    """Synthesize cosmic foresight, singularity governance and continuity into one nexus."""
    compliance = load_compliance_report()
    solar_events = compliance.get("solar_events", ["none"]) if isinstance(compliance, dict) else ["none"]
    detected = [
        "Solar storm forecast" if any("storm" in str(event).lower() for event in solar_events) else "No immediate cosmic alerts"
    ]
    transcendent = load_transcendent_intelligence_core()
    continuity = load_infinite_continuity_engine()
    matrix = load_singularity_governance_matrix()
    score = min(100, int((transcendent.get("resilience_score", 90) + continuity.get("metrics", {}).get("resilience_index", 95) + (100 - matrix.get("pending_compliance_count", 0) * 5)) / 3))
    return {
        "nexus_status": "cosmic-eternal",
        "detected_conditions": detected + matrix.get("detected_conditions", []),
        "nexus_action": "Harmonize governance, reschedule sensitive campaigns, embed timeless values.",
        "unified_resilience_score": score,
        "components": {
            "transcendent": transcendent.get("core_status"),
            "continuity": continuity.get("engine_status"),
            "matrix": matrix.get("matrix_status")
        },
        "pending_compliance_count": matrix.get("pending_compliance_count", 0)
    }


def load_omniversal_strategy_continuum():
    """Aggregate multiversal and timeline simulations into a single continuum view."""
    multiversal = load_multiversal_simulations()
    continuum = load_governance_continuum()
    transcendent = load_transcendent_intelligence_core()
    sims = multiversal.get("simulations", [])
    timelines = continuum.get("timelines", [])
    success_rate = float(multiversal.get("success_rate", "0%").rstrip("%")) if multiversal.get("success_rate") else 0
    overall_resilience = min(100, int(success_rate + 10 - len(timelines)))
    recommended = [
        "Embed adaptive consent workflows across universes.",
        "Apply timeless eco-values to future-facing campaigns.",
        "Orchestrate timeline-specific creative with omniversal governance checks."
    ]
    if transcendent.get("pending_compliance_count", 0) > 0:
        recommended.insert(0, "Harmonize omniversal strategy with current compliance remediation plans.")
    return {
        "continuum_status": "omniversal",
        "simulations": sims,
        "timelines": timelines,
        "resilience_summary": {
            "universe_count": len(sims),
            "timeline_count": len(timelines),
            "overall_resilience": overall_resilience
        },
        "recommendations": recommended,
        "transcendent_anchor": transcendent.get("core_action")
    }


def load_multiversal_simulations():
    logs = load_log_lines()
    # Derive simple scenario metrics from historical logs as a placeholder for richer simulations.
    total = len(logs)
    success = sum(1 for e in logs if e.get("delivery_status", "").upper() == "SUCCESS")
    fail = total - success
    success_rate = (success / total * 100) if total else 0

    sims = [
        {
            "universe": "A",
            "scenario": "GDPR abolished",
            "roi_change": int(success_rate * 0.28) if total else 0,
            "resilience": "high" if success_rate > 80 else "medium",
            "recommended_strategy": "Automated consent workflows with transparent personalization"
        },
        {
            "universe": "B",
            "scenario": "GDPR expanded",
            "roi_change": int((success_rate - 100) * 0.22) if total else 0,
            "resilience": "medium" if success_rate > 50 else "low",
            "recommended_strategy": "Embedded preference controls and adaptive consent architecture"
        }
    ]

    return {
        "engine_status": "multiversal",
        "simulations": sims,
        "scenario_count": total,
        "insight": "Cross-universe resilience favors consent-first workflows that perform in both relaxed and strict privacy states.",
        "success_rate": f"{success_rate:.1f}%",
        "failure_count": fail,
    }


def load_governance_continuum():
    compliance = load_compliance_report()
    regional_audit = compliance.get("regional_audit", []) if isinstance(compliance, dict) else []
    pending = [item for item in regional_audit if item.get("status") != "Compliant"]
    horizons = [
        {"horizon": "1 year", "governance_health": "stable" if not pending else "watch", "focus": "current regulatory alignment"},
        {"horizon": "5 years", "governance_health": "maturing", "focus": "sustainability and generational trust"},
        {"horizon": "10 years", "governance_health": "resilient", "focus": "timeless compliance and cultural adaptability"},
        {"horizon": "50 years", "governance_health": "future-proof", "focus": "intergenerational ecosystem stewardship"}
    ]
    recommended_actions = [
        "Embed sustainability metrics into all campaign compliance checks.",
        "Build generational foresight into cross-region policy review cycles.",
        "Maintain a governance continuum dashboard for long-term resilience monitoring."
    ]
    if pending:
        recommended_actions.insert(0, f"Resolve {len(pending)} pending compliance items before the next governance review.")
    elif not regional_audit:
        recommended_actions.insert(0, "Generate a regional audit baseline to anchor the governance continuum.")
    return {
        "continuum_status": "eternal",
        "timelines": horizons,
        "recommended_actions": recommended_actions,
        "headline": "Eternal governance continues through a blend of policy resilience, sustainability permanence, and cultural foresight.",
        "pending_compliance_count": len(pending)
    }


@app.route("/multiversal-simulations")
def multiversal_simulations():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_multiversal_simulations())


@app.route("/governance-continuum")
def governance_continuum():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_governance_continuum())


@app.route("/transcendent-core")
def transcendent_core():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_transcendent_intelligence_core())
    
@app.route("/cosmic-nexus")
def cosmic_nexus():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_cosmic_eternal_nexus())

@app.route("/omniversal-continuum")
def omniversal_continuum():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_omniversal_strategy_continuum())


@app.route("/legacy-framework")
def legacy_framework():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_legacy_preservation_framework())
    
@app.route("/singularity-matrix")
def singularity_matrix():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_singularity_governance_matrix())

@app.route("/continuity-engine")
def continuity_engine():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_infinite_continuity_engine())


@app.route("/transformation-insights")
def transformation_insights():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(load_transformation_insights())


@app.route("/strategy-nexus")
def strategy_nexus():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    return jsonify(build_strategy_nexus())


@app.route("/region-summary")
def region_summary():
    region_stats = {}
    if os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                region = str(row.get("region", "USA")).strip().upper() or "USA"
                region_stats.setdefault(region, {"region": region, "recipient_count": 0})
                region_stats[region]["recipient_count"] += 1
    else:
        region_stats = load_region_counts_from_logs()

    compliance = load_compliance_report()
    audit_map = {item.get("region"): item for item in compliance.get("regional_audit", [])}
    for region, stats in region_stats.items():
        audit_item = audit_map.get(region, {})
        stats["law"] = audit_item.get("law")
        stats["channels"] = audit_item.get("channels")
        stats["status"] = audit_item.get("status", "Pending review")
    return jsonify(list(region_stats.values()))


@app.route("/summary")
def summary():
    if os.path.exists(SUMMARY_PATH):
        with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"total_emails": 0, "successful_deliveries": 0, "failed_deliveries": 0, "log_files": {}})


@app.route("/logs")
def logs():
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    logs = load_log_lines()
    email = request.args.get("email")
    status = request.args.get("status")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    filtered = filter_logs(logs, email=email, status=status, date_from=date_from, date_to=date_to)
    return jsonify(filtered)


@app.route("/export/<format>")
def export_logs(format):
    if g.role != "admin":
        return jsonify({"error": "Access denied"}), 403
    logs = load_log_lines()
    email = request.args.get("email")
    status = request.args.get("status")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    filtered = filter_logs(logs, email=email, status=status, date_from=date_from, date_to=date_to)

    if format == "csv":
        if not filtered:
            return Response("", mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=logs.csv"})
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=filtered[0].keys())
        writer.writeheader()
        writer.writerows(filtered)
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=logs.csv"})
    elif format == "json":
        return Response(json.dumps(filtered, indent=4), mimetype="application/json", headers={"Content-Disposition": "attachment;filename=logs.json"})
    return jsonify({"error": "Unsupported export format"}), 400


@app.route("/role")
def role():
    return jsonify({"role": g.role})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("DASHBOARD_PORT", 5000)), debug=True)
