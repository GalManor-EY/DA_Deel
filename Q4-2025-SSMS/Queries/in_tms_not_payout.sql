/* ============================================================
   in_TMS_not_PAYOUT.sql
   Q4-2025
   Logic:
   TMS Q4 Withdrawal transactions whose reconciliation_id
   does NOT appear in PAYOUT Q4
   ============================================================ */

WITH all_bank_transactions_filtered_q4_2025 AS (
    SELECT *
    FROM dbo.stg_tms_transactions_q4_2025
    WHERE TRY_CONVERT(date, LEFT(created_at, 10)) >= '2025-10-01'
      AND TRY_CONVERT(date, LEFT(created_at, 10)) <  '2026-01-01'
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL
),

all_payment_contractor_withdrawal AS (
    SELECT *
    FROM dbo.stg_payment_contractor_withdrawal
    WHERE PURPOSE = 'contractor_payment'
      AND LEFT(CREATED_AT, 4) IN ('2024','2025')
),

tms_only_contractor_withdrawals AS (
    SELECT
        atw.deel_platform_id,
        atw.created_at,
        atw.reconciliation_id,
        atw.provider,
        atw.usd_amount,
        apcw.WITHDRAWAL_ID
    FROM all_bank_transactions_filtered_q4_2025 atw
    LEFT JOIN all_payment_contractor_withdrawal apcw
        ON atw.deel_platform_id = apcw.WITHDRAWAL_ID
),

payout_q4 AS (
    SELECT DISTINCT
        tms_reconciliation_id
    FROM dbo.stg_payout_q4_2025
    WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) >= '2025-10-01'
      AND TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) <  '2026-01-01'
),

tms_not_in_payout_q4 AS (
    SELECT *
    FROM tms_only_contractor_withdrawals t
    WHERE NOT EXISTS (
        SELECT 1
        FROM payout_q4 p
        WHERE p.tms_reconciliation_id = t.reconciliation_id
    )
),

full_payout AS (
    SELECT
        tms_reconciliation_id,
        TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) AS payout_date
    FROM dbo.stg_full_payout_q4_2025
    WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) IS NOT NULL
)

SELECT
    YEAR(fp.payout_date)  AS payout_from_year,
    MONTH(fp.payout_date) AS payout_from_month,

    CASE
        WHEN fp.tms_reconciliation_id IS NOT NULL THEN 1
        ELSE 0
    END AS exists_in_full_payout,

    CASE
        WHEN t.WITHDRAWAL_ID IS NOT NULL
            THEN 'contractor_withdrawal'
        ELSE 'other_withdrawal'
    END AS withdrawal_type,

    apcw.STATUS,

    COUNT(*) AS cnt,

    SUM(TRY_CAST(t.usd_amount AS DECIMAL(18,2))) AS sum_usd_amount

FROM tms_not_in_payout_q4 t
LEFT JOIN full_payout fp
    ON t.reconciliation_id = fp.tms_reconciliation_id
LEFT JOIN all_payment_contractor_withdrawal apcw
    ON t.WITHDRAWAL_ID = apcw.WITHDRAWAL_ID

GROUP BY
    YEAR(fp.payout_date),
    MONTH(fp.payout_date),
    CASE
        WHEN fp.tms_reconciliation_id IS NOT NULL THEN 1
        ELSE 0
    END,
    CASE
        WHEN t.WITHDRAWAL_ID IS NOT NULL
            THEN 'contractor_withdrawal'
        ELSE 'other_withdrawal'
    END,
    apcw.STATUS

ORDER BY
    payout_from_year,
    payout_from_month,
    exists_in_full_payout;