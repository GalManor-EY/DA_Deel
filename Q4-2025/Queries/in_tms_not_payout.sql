
WITH all_bank_transactions_filtered_q4_2025 AS (
    SELECT *
    FROM all_bank_transactions_full_to_Q4_2025
    WHERE YEAR(LEFT(CREATED_AT,10)) = 2025
      AND MONTH(LEFT(CREATED_AT,10)) IN (10,11,12)
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL
),
all_payment_contractor_withdrawal AS (
    SELECT *
    FROM payment_contractor_withdrawal_q2_25
    WHERE PURPOSE = 'contractor_payment'
      AND LEFT(CREATED_AT, 4) IN ('2024','2025')
),
tms_only_contractor_withdrawals AS (
    SELECT
        atw.deel_platform_id,
        apcw.WITHDRAWAL_ID,
        atw.CREATED_AT,
        atw.reconciliation_id,
        atw.provider,
        atw.usd_amount
    FROM all_bank_transactions_filtered_q4_2025 atw
    INNER JOIN all_payment_contractor_withdrawal apcw
        ON atw.deel_platform_id = apcw.WITHDRAWAL_ID
),
payout_filtered_q4_25 AS (
    SELECT *
    FROM payout_full_to_Q4_25
    WHERE MONTH(LEFT(withdrawal_created_at,10)) IN (10,11,12)
      AND YEAR(LEFT(withdrawal_created_at,10)) = 2025
),
list_in_tms_not_in_payout_q4_25 AS (
    SELECT
        tocw.reconciliation_id,
        tocw.provider,
        tocw.usd_amount,
        tocw.created_at,
        tocw.deel_platform_id
    FROM tms_only_contractor_withdrawals tocw
    LEFT JOIN payout_filtered_q4_25 payout_q4
        ON tocw.reconciliation_id = payout_q4.tms_reconciliation_id
    WHERE payout_q4.tms_reconciliation_id IS NULL
),
payout_full AS (
    SELECT
        *,
        LEFT(withdrawal_created_at,10) AS withdrawal_created_at_date
    FROM payout_full_to_Q4_25
)
SELECT
    YEAR(payout_full.withdrawal_created_at_date) AS cutoff_year,
    MONTH(payout_full.withdrawal_created_at_date) AS cutoff_month,
    apcw.status,
    COUNT(*) AS cnt,
    SUM(list_in_tms_not_in_payout_q4_25.usd_amount) AS sum_usd_amount
FROM list_in_tms_not_in_payout_q4_25
LEFT JOIN payout_full
    ON list_in_tms_not_in_payout_q4_25.reconciliation_id = payout_full.TMS_reconciliation_id
LEFT JOIN all_payment_contractor_withdrawal apcw
    ON apcw.WITHDRAWAL_ID = list_in_tms_not_in_payout_q4_25.deel_platform_id
GROUP BY 1,2,3;
