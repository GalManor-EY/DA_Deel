-- testtt

WITH payout_q4_2025 AS (
    SELECT *
    FROM payout_q4_25
    WHERE MONTH(withdrawal_created_at) IN (10,11,12)
      AND YEAR(withdrawal_created_at) = 2025
),
all_bank_transactions_q4_25 AS (
    SELECT *
    FROM tms_transactions_q4_25
    WHERE YEAR(LEFT(CREATED_AT,10)) = 2025
      AND MONTH(LEFT(CREATED_AT,10)) IN (10,11,12)
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
    SUM(payout.total_cashout_usd) AS sum_total_cashout_usd,
    SUM(tms_q4_25.usd_amount) AS sum_tms_usd_amount,
    SUM(payout.total_cashout_usd - tms_q4_25.usd_amount) AS sum_diff_usd
FROM payout_q4_2025 payout
LEFT JOIN all_bank_transactions_q4_25 tms_q4_25
    ON payout.tms_reconciliation_id = tms_q4_25.reconciliation_id
WHERE (payout.total_cashout_usd - tms_q4_25.usd_amount) <> 0
  AND tms_q4_25.reconciliation_id IS NOT NULL
GROUP BY payout.PAYMENT_METHOD;



