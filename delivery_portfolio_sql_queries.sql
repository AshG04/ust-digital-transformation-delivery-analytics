-- UST Digital Transformation Delivery Analytics Work Sample
-- Synthetic SQL examples for client delivery, SLA, backlog, and executive reporting

-- 1. Client and project health summary

SELECT
    client_name,
    project_name,
    workstream,
    COUNT(DISTINCT delivery_item_id) AS total_items,
    SUM(CASE WHEN status IN ('Open', 'In Progress', 'Blocked') THEN 1 ELSE 0 END) AS open_backlog,
    SUM(CASE WHEN actual_resolution_hours > sla_target_hours THEN 1 ELSE 0 END) AS sla_breaches,
    ROUND(AVG(actual_resolution_hours), 1) AS avg_resolution_hours,
    ROUND(AVG(sprint_throughput), 1) AS avg_sprint_throughput
FROM delivery_portfolio
GROUP BY client_name, project_name, workstream
ORDER BY sla_breaches DESC, open_backlog DESC;


-- 2. SLA breach rate by client and item type

SELECT
    client_name,
    item_type,
    COUNT(DISTINCT delivery_item_id) AS total_items,
    SUM(CASE WHEN actual_resolution_hours > sla_target_hours THEN 1 ELSE 0 END) AS sla_breaches,
    ROUND(
        SUM(CASE WHEN actual_resolution_hours > sla_target_hours THEN 1 ELSE 0 END) * 1.0
        / COUNT(DISTINCT delivery_item_id),
        3
    ) AS sla_breach_rate
FROM delivery_portfolio
GROUP BY client_name, item_type
ORDER BY sla_breach_rate DESC, sla_breaches DESC;


-- 3. Root-cause analysis for blocked and breached items

SELECT
    root_cause,
    COUNT(DISTINCT delivery_item_id) AS affected_items,
    SUM(CASE WHEN status = 'Blocked' THEN 1 ELSE 0 END) AS blocked_items,
    SUM(CASE WHEN actual_resolution_hours > sla_target_hours THEN 1 ELSE 0 END) AS sla_breaches,
    ROUND(AVG(actual_resolution_hours), 1) AS avg_resolution_hours
FROM delivery_portfolio
WHERE status = 'Blocked'
   OR actual_resolution_hours > sla_target_hours
GROUP BY root_cause
ORDER BY affected_items DESC;


-- 4. Sprint throughput trend by project

SELECT
    reporting_month,
    client_name,
    project_name,
    ROUND(AVG(sprint_throughput), 1) AS avg_sprint_throughput,
    COUNT(DISTINCT delivery_item_id) AS total_items_completed
FROM delivery_portfolio
WHERE status = 'Closed'
GROUP BY reporting_month, client_name, project_name
ORDER BY reporting_month, client_name, project_name;


-- 5. High-severity leadership escalation list

SELECT
    delivery_item_id,
    client_name,
    project_name,
    workstream,
    item_type,
    status,
    severity,
    root_cause,
    sla_target_hours,
    actual_resolution_hours,
    recommended_action
FROM delivery_portfolio
WHERE severity IN ('Critical', 'High')
  AND (
        status IN ('Open', 'In Progress', 'Blocked')
        OR actual_resolution_hours > sla_target_hours
      )
ORDER BY severity, actual_resolution_hours DESC;


-- 6. Data quality check for missing or invalid operational fields

SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN client_name IS NULL THEN 1 ELSE 0 END) AS missing_client_name,
    SUM(CASE WHEN project_name IS NULL THEN 1 ELSE 0 END) AS missing_project_name,
    SUM(CASE WHEN sla_target_hours IS NULL OR sla_target_hours <= 0 THEN 1 ELSE 0 END) AS invalid_sla_target,
    SUM(CASE WHEN actual_resolution_hours IS NULL OR actual_resolution_hours < 0 THEN 1 ELSE 0 END) AS invalid_resolution_hours
FROM delivery_portfolio;
