SELECT
  event_name,
  COUNT(*) AS bottleneck_count,
  AVG(predicted_is_bottleneck_probs[OFFSET(1)].prob) AS avg_bottleneck_probability,
  MIN(predicted_is_bottleneck_probs[OFFSET(1)].prob) AS min_probability,
  MAX(predicted_is_bottleneck_probs[OFFSET(1)].prob) AS max_probability
FROM
  ML.PREDICT(
    MODEL `ace-shine-465713-h2.analytics_494976509.ML_0903_1`,
    (
      SELECT
        event_name,
        event_timestamp,
        param.key AS param_key,

        MAX(
          CASE
            WHEN param.key LIKE '%Response_Time'
            THEN param.value.double_value
          END
        ) AS response_time,

        MAX(
          CASE
            WHEN param.key LIKE '%Response_Code'
            THEN param.value.int_value
          END
        ) AS response_code,

        COALESCE(
          CAST(
            MAX(
              CASE
                WHEN param.key LIKE '%Response_Time'
                THEN param.value.double_value
              END
            ) AS NUMERIC
          ),
          CAST(
            MAX(
              CASE
                WHEN param.key LIKE '%Response_Code'
                THEN param.value.int_value
              END
            ) AS NUMERIC
          )
        ) AS response_value,

        CASE
          WHEN MAX(
                 CASE
                   WHEN param.key LIKE '%Response_Code'
                   THEN param.value.int_value
                 END
               ) != 200
            OR MAX(
                 CASE
                   WHEN param.key LIKE '%Response_Time'
                   THEN param.value.double_value
                 END
               ) > 0.450
          THEN TRUE
          ELSE FALSE
        END AS is_bottleneck

      FROM
        `ace-shine-465713-h2.analytics_494976509.events_intraday_20260116`,
        UNNEST(event_params) AS param
      WHERE
        param.key <> 'tool'
        AND event_name = 'jmeter_01162026_1'
      GROUP BY
        event_name,
        event_timestamp,
        param.key
    )
  )
WHERE
  predicted_is_bottleneck = TRUE
GROUP BY
  event_name;
