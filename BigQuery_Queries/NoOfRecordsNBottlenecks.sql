SELECT 
  COUNT(*) as NumofBottlenecks
FROM (
  SELECT
    event_name,
    event_timestamp, 
    param.key AS param_key,

    -- Extract response time
    MAX(CASE WHEN param.key LIKE '%Response_Time' THEN param.value.double_value END) AS response_time,

    -- Extract response code
    MAX(CASE WHEN param.key LIKE '%Response_Code' THEN param.value.int_value END) AS response_code,

    -- Bottleneck condition
    CASE 
      WHEN MAX(CASE WHEN param.key LIKE '%Response_Code' THEN param.value.int_value END) != 200 
           OR MAX(CASE WHEN param.key LIKE '%Response_Time' THEN param.value.double_value END) > 0.450
      THEN TRUE 
      ELSE FALSE 
    END AS is_bottleneck

  FROM
    `ace-shine-465713-h2.analytics_494976509.events_intraday_20260116`,
    UNNEST(event_params) AS param

  WHERE 
    param.key <> 'tool' and event_name = 'jmeter_01162026_1'

  GROUP BY 
    event_name, event_timestamp, param.key
)
where is_bottleneck = true
GROUP BY event_name, is_bottleneck
ORDER BY event_name, is_bottleneck DESC;
