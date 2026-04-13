
WITH payout_q4_2025 AS (
    SELECT *
    FROM dbo.stg_payout_q4_2025
  WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) IS NOT NULL
        AND YEAR(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) = 2025
        AND MONTH(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) IN (10,11,12)

),
all_bank_transactions_q4_25 AS (
    SELECT *
    FROM dbo.stg_tms_transactions_q4_2025
    WHERE TRY_CONVERT(date, LEFT(CREATED_AT, 10)) IS NOT NULL
      AND YEAR(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) = 2025
      AND MONTH(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) IN (10,11,12)
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL
)
SELECT
    payout.PAYMENT_METHOD,
    COUNT(*) AS cnt,
    SUM(CAST(payout.total_cashout_usd AS DECIMAL(18,2))) AS sum_total_cashout_usd,
    SUM(CAST(tms_q4_25.usd_amount     AS DECIMAL(18,2))) AS sum_tms_usd_amount,
    SUM(CAST(payout.total_cashout_usd AS DECIMAL(18,2))- CAST(tms_q4_25.usd_amount AS DECIMAL(18,2))) AS sum_diff_usd

FROM payout_q4_2025 payout
LEFT JOIN all_bank_transactions_q4_25 tms_q4_25
    ON payout.tms_reconciliation_id = tms_q4_25.reconciliation_id
WHERE CAST(payout.total_cashout_usd AS DECIMAL(18,2)) - CAST(tms_q4_25.usd_amount AS DECIMAL(18,2)) <> 0
  AND tms_q4_25.reconciliation_id IS NOT NULL
  AND tms_q4_25.reconciliation_id IS NOT NULL
GROUP BY payout.PAYMENT_METHOD;



