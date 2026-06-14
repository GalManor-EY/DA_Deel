WITH payout_q1_2026 AS (
    SELECT *
    FROM dbo.stg_payout_q1_2026
    WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) IS NOT NULL
      AND YEAR(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) = 2026
      AND MONTH(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) IN (1, 2, 3)
),
all_bank_transactions_q1_2026_groupped AS (
    SELECT
        reconciliation_id,
        PROVIDER,
        SUM(CAST(usd_amount AS DECIMAL(18,2))) AS usd_amount
    FROM dbo.stg_tms_transactions_q1_2026
    WHERE TRY_CONVERT(date, LEFT(CREATED_AT, 10)) IS NOT NULL
      AND YEAR(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) = 2026
      AND MONTH(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) IN (1, 2, 3)
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL
    GROUP BY reconciliation_id, PROVIDER
)
SELECT
    COUNT(*) AS cnt,
    SUM(CAST(payout.total_cashout_usd AS DECIMAL(18,2))) AS sum_total_cashout_usd,
    SUM(CAST(tms_q1_26.usd_amount AS DECIMAL(18,2)))      AS sum_tms_usd_amount,
    SUM(
        CAST(payout.total_cashout_usd AS DECIMAL(18,2)) 
      - CAST(tms_q1_26.usd_amount     AS DECIMAL(18,2))
    ) AS sum_diff_usd
FROM payout_q1_2026 payout
LEFT JOIN all_bank_transactions_q1_2026_groupped tms_q1_26
    ON payout.tms_reconciliation_id = tms_q1_26.reconciliation_id
WHERE tms_q1_26.reconciliation_id IS NOT NULL;

-- ✅ Expected result:
-- sum_diff_usd = 0  → Done V (26/5/2026)