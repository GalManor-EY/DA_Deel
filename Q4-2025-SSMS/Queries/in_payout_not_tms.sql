

WITH payout_q4_2025 AS (
    SELECT *
    FROM dbo.stg_payout_q4_2025
    WHERE MONTH(withdrawal_created_at) IN (10,11,12)
      AND YEAR(withdrawal_created_at) = 2025
),
all_bank_transactions_q4_25 AS (
    SELECT *
    FROM dbo.stg_tms_transactions_q4_2025
    WHERE YEAR(LEFT(CREATED_AT,10)) = 2025
      AND MONTH(LEFT(CREATED_AT,10)) IN (10,11,12)
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL
),
in_payout_not_in_tms AS (
    SELECT payout.*
    FROM payout_q4_2025 payout
    LEFT JOIN all_bank_transactions_q4_25 tms_q4_25
        ON payout.tms_reconciliation_id = tms_q4_25.reconciliation_id
    WHERE tms_q4_25.reconciliation_id IS NULL
),
all_tms_25 AS (
    SELECT
        *,
        LEFT(CREATED_AT,10) AS created_at_date
    FROM dbo.stg_full_tms_q4_2025
    WHERE DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID is null
      AND SENDER_ID is null
      AND RETURN_ID is null
)

SELECT
    YEAR(all_tms_25.created_at_date)  AS cutoff_year,
    MONTH(all_tms_25.created_at_date) AS cutoff_month,
    CASE 
      WHEN LOWER(TRIM(in_payout_not_in_tms.PAYMENT_PROVIDER_NAME)) = 'alviere' THEN 'Alviere'
      ELSE 'No Alviere'
    END AS if_alviere,
    COUNT(*) AS cnt,
    SUM(in_payout_not_in_tms.INITIAL_WITHDRAWAL_AMOUNT_USD) AS sum_initial_withdrawal_usd
FROM in_payout_not_in_tms
LEFT JOIN all_tms_25
  ON in_payout_not_in_tms.tms_reconciliation_id = all_tms_25.reconciliation_id
GROUP BY cutoff_year, cutoff_month, if_alviere;





