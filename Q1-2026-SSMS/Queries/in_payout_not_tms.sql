/* ============================================================
   in_payout_not_TMS.sql
   Q4-2025
   Logic:
   Payout Q4 records whose reconciliation_id does NOT appear
   in TMS Q4 Withdrawal transactions (DISTINCT reconciliation_id)
   ============================================================ */

WITH payout_q4_2025 AS (
    SELECT
        p.*,
        d.withdrawal_date
    FROM dbo.stg_payout_q4_2025 p
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(p.withdrawal_created_at, 10))
    ) d(withdrawal_date)
    WHERE d.withdrawal_date >= '2025-10-01'
      AND d.withdrawal_date <  '2026-01-01'
),

tms_q4_25 AS (
    SELECT DISTINCT
        t.reconciliation_id
    FROM dbo.stg_tms_transactions_q4_2025 t
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(t.created_at, 10))
    ) d(created_date)
    WHERE d.created_date >= '2025-10-01'
      AND d.created_date <  '2026-01-01'
      AND t.direction = 'OUTGOING'
      AND t.deel_platform_type = 'Withdrawal'
      AND t.type <> 'Returned'
      AND t.receiver_id IS NULL
      AND t.sender_id IS NULL
      AND t.return_id IS NULL
),

in_payout_not_in_tms AS (
    SELECT
        p.*
    FROM payout_q4_2025 p
    WHERE NOT EXISTS (
        SELECT 1
        FROM tms_q4_25 t
        WHERE t.reconciliation_id = p.tms_reconciliation_id
    )
),

full_tms AS (
    SELECT
        f.reconciliation_id,
        d.created_date
    FROM dbo.stg_full_tms_q4_2025 f
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(f.created_at, 10))
    ) d(created_date)
)

SELECT
    YEAR(ft.created_date)  AS tms_cutoff_year,
    MONTH(ft.created_date) AS tms_cutoff_month,

    CASE
        WHEN LOWER(LTRIM(RTRIM(p.payment_provider_name))) = 'alviere'
            THEN 'Alviere'
        ELSE 'No Alviere'
    END AS if_alviere,

    CASE
        WHEN p.tms_reconciliation_id IS NOT NULL
            THEN 'recon_id_exist'
        ELSE 'no_recon_id'
    END AS if_recon_id,

    COUNT(*) AS cnt,

    SUM(TRY_CAST(p.initial_withdrawal_amount_usd AS DECIMAL(18,2)))
        AS sum_initial_withdrawal_usd,

    SUM(TRY_CAST(p.total_cashout_usd AS DECIMAL(18,2)))
        AS sum_total_cashout_usd

FROM in_payout_not_in_tms p
LEFT JOIN full_tms ft
    ON p.tms_reconciliation_id = ft.reconciliation_id

GROUP BY
    YEAR(ft.created_date),
    MONTH(ft.created_date),
    CASE
        WHEN LOWER(LTRIM(RTRIM(p.payment_provider_name))) = 'alviere'
            THEN 'Alviere'
        ELSE 'No Alviere'
    END,
    CASE
        WHEN p.tms_reconciliation_id IS NOT NULL
            THEN 'recon_id_exist'
        ELSE 'no_recon_id'
    END;