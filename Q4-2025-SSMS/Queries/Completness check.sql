-- completness check
use Deel_2025;

-- in Q4-2025:
select count(*), SUM(CAST(total_cashout_usd AS DECIMAL(18,2))) AS sum_total_cashout_usd,
sum(CAST(INITIAL_WITHDRAWAL_AMOUNT_USD AS DECIMAL(18,2))) AS sum_initial_withdrawal_usd
FROM dbo.stg_payout_q4_2025
WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) IS NOT NULL
    AND YEAR(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) = 2025
    AND MONTH(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) IN (10,11,12);
-- cnt: 1,356,950 | sum cashout: 2,218,289,378 | sum initial: 2,230,587,061


select count(*), SUM(CAST(usd_amount     AS DECIMAL(18,2))) AS sum_tms_usd_amount
from dbo.stg_tms_transactions_q4_2025
WHERE TRY_CONVERT(date, LEFT(CREATED_AT, 10)) IS NOT NULL
      AND YEAR(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) = 2025
      AND MONTH(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) IN (10,11,12)
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL;
-- cnt: 1,380,680 | sum: 2,273,878,607

-- dups in join diff BVNK

SELECT tms_reconciliation_id,COUNT(*) AS cnt
    FROM dbo.stg_payout_q4_2025
  WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) IS NOT NULL
        AND YEAR(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) = 2025
        AND MONTH(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) IN (10,11,12)
        and tms_reconciliation_id is not null
    group by tms_reconciliation_id
    having count(*)>1;
-- no dups

select *
from dbo.stg_payout_q4_2025
WHERE tms_reconciliation_id is null;
-- cnt 658

with tms_with_dups as (
select reconciliation_id, PROVIDER, count(*) as cnt, SUM(CAST(usd_amount     AS DECIMAL(18,2))) AS sum_tms_usd_amount
from dbo.stg_tms_transactions_q4_2025
WHERE TRY_CONVERT(date, LEFT(CREATED_AT, 10)) IS NOT NULL
      AND YEAR(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) = 2025
      AND MONTH(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) IN (10,11,12)
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL
group by reconciliation_id, PROVIDER
HAVING count(*)>1)

select PROVIDER, count(*) as counters
from tms_with_dups
group by PROVIDER;
-- BVNK cases


select reconciliation_id, usd_amount
from dbo.stg_tms_transactions_q4_2025
WHERE reconciliation_id = '24668557';
-- BVNK cases

select tms_reconciliation_id, total_cashout_usd, INITIAL_WITHDRAWAL_AMOUNT_USD
from dbo.stg_payout_q4_2025
WHERE tms_reconciliation_id = '24668557';   
-- BVNK cases


-- join difference between payout and TMS
WITH payout_q4_2025 AS (
    SELECT *
    FROM dbo.stg_payout_q4_2025
  WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) IS NOT NULL
        AND YEAR(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) = 2025
        AND MONTH(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) IN (10,11,12)),
all_bank_transactions_q4_25_groupped AS (
    SELECT reconciliation_id, PROVIDER, SUM(CAST(usd_amount AS DECIMAL(18,2))) AS usd_amount
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
      group by reconciliation_id, PROVIDER)
SELECT
    COUNT(*) AS cnt,
    SUM(CAST(payout.total_cashout_usd AS DECIMAL(18,2))) AS sum_total_cashout_usd, SUM(CAST(tms_q4_25.usd_amount     AS DECIMAL(18,2))) AS sum_tms_usd_amount,
    SUM(CAST(payout.total_cashout_usd AS DECIMAL(18,2))- CAST(tms_q4_25.usd_amount AS DECIMAL(18,2))) AS sum_diff_usd
FROM payout_q4_2025 payout
LEFT JOIN all_bank_transactions_q4_25_groupped tms_q4_25
    ON payout.tms_reconciliation_id = tms_q4_25.reconciliation_id
WHERE tms_q4_25.reconciliation_id IS NOT NULL;
-- 0 USD - Done

-- in payount not in TMS:

-- Total amount in payout not in TMS:

WITH payout_q4_25 AS (
    SELECT
        p.*,
        TRY_CONVERT(date, LEFT(p.WITHDRAWAL_CREATED_AT, 10)) AS withdrawal_date
    FROM dbo.stg_payout_q4_2025 p
    WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at, 10)) IS NOT NULL
        AND YEAR(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) = 2025
        AND MONTH(TRY_CONVERT(date, LEFT(withdrawal_created_at, 10))) IN (10,11,12)
),
tms_q4_25 AS (
    SELECT
    RECONCILIATION_ID
    FROM dbo.stg_tms_transactions_q4_2025 t
    WHERE TRY_CONVERT(date, LEFT(CREATED_AT, 10)) IS NOT NULL
      AND YEAR(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) = 2025
      AND MONTH(TRY_CONVERT(date, LEFT(CREATED_AT, 10))) IN (10,11,12)
      AND DIRECTION = 'OUTGOING'
      AND DEEL_PLATFORM_TYPE = 'Withdrawal'
      AND TYPE <> 'Returned'
      AND RECEIVER_ID IS NULL
      AND SENDER_ID IS NULL
      AND RETURN_ID IS NULL
    group by RECONCILIATION_ID
),
in_payout_not_in_tms AS (
    SELECT
        p.*
    FROM payout_q4_25 p
    LEFT JOIN tms_q4_25 t
        ON p.tms_reconciliation_id = t.reconciliation_id
    WHERE t.reconciliation_id IS NULL
)
SELECT
    COUNT(*) AS cnt,
    SUM(TRY_CAST(p.INITIAL_WITHDRAWAL_AMOUNT_USD AS DECIMAL(18,2))) AS sum_initial_withdrawal_usd,
    SUM(TRY_CAST(p.total_cashout_usd AS DECIMAL(18,2))) AS sum_total_cashout_usd
FROM in_payout_not_in_tms p;

-- Looking for cut-off, Alviere and no TMS reconciliation id:

WITH payout_q4_2025 AS (
    SELECT p.*, d.withdrawal_date
    FROM dbo.stg_payout_q4_2025 p
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(p.withdrawal_created_at,10))
    ) d(withdrawal_date)
    WHERE d.withdrawal_date >= '2025-10-01'
      AND d.withdrawal_date <  '2026-01-01'
),

tms_q4_25 AS (
    SELECT DISTINCT t.reconciliation_id
    FROM dbo.stg_tms_transactions_q4_2025 t
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(t.created_at,10))
    ) d(created_date)
    WHERE d.created_date >= '2025-10-01'
      AND d.created_date <  '2026-01-01'
      AND t.direction = 'OUTGOING'
      AND t.deel_platform_type = 'Withdrawal'
      AND t.type <> 'Returned'
      AND t.receiver_id IS NULL
      AND t.sender_id IS NULL
      AND t.return_id IS NULL),

in_payout_not_in_tms AS (
    SELECT p.*
    FROM payout_q4_2025 p
    WHERE NOT EXISTS (
        SELECT 1
        FROM tms_q4_25 t
        WHERE t.reconciliation_id = p.tms_reconciliation_id)),

full_tms AS (
    SELECT
        f.reconciliation_id,
        d.created_date
    FROM dbo.stg_full_tms_q4_2025 f
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(f.created_at,10))
    ) d(created_date))
SELECT
    YEAR(ft.created_date)  AS tms_cutoff_year, MONTH(ft.created_date) AS tms_cutoff_month,
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
-- 

select *
from in_payout_not_in_tms p
LEFT JOIN full_tms ft
    ON p.tms_reconciliation_id = ft.reconciliation_id
where ft.reconciliation_id is null and LOWER(LTRIM(RTRIM(p.payment_provider_name))) <> 'alviere' and p.tms_reconciliation_id is not null



-- in TMS not in payout

WITH tms_q4_agg AS (
    SELECT reconciliation_id, PROVIDER, SUM(CAST(usd_amount AS DECIMAL(18,2))) AS usd_amount
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
      group by reconciliation_id, PROVIDER
),

payout_q4 AS (
    SELECT DISTINCT
        p.tms_reconciliation_id
    FROM dbo.stg_payout_q4_2025 p
    WHERE TRY_CONVERT(date, LEFT(p.withdrawal_created_at,10)) >= '2025-10-01'
      AND TRY_CONVERT(date, LEFT(p.withdrawal_created_at,10)) <  '2026-01-01'
      AND p.tms_reconciliation_id IS NOT NULL
)

SELECT
    COUNT(*) AS tms_not_in_payout_cnt,
    SUM(t.usd_amount) AS tms_not_in_payout_usd_sum
FROM tms_q4_agg t
WHERE NOT EXISTS (
    SELECT 1
    FROM payout_q4 p
    WHERE p.tms_reconciliation_id = t.reconciliation_id
);
-- cnt: 11,931 | sum: 76,945,261


-- Looking for cut-off
WITH all_bank_transactions_filtered_q4_2025 AS (
    SELECT *
    FROM dbo.stg_tms_transactions_q4_2025
    WHERE TRY_CONVERT(date, LEFT(created_at,10)) >= '2025-10-01'
      AND TRY_CONVERT(date, LEFT(created_at,10)) <  '2026-01-01'
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
    FROM dbo.stg_payout_q4_2025
    WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at,10)) >= '2025-10-01'
      AND TRY_CONVERT(date, LEFT(withdrawal_created_at,10)) <  '2026-01-01'
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
)

SELECT
    YEAR(list_in_tms_not_in_payout_q4_25.created_at)  AS cutoff_year,
    MONTH(list_in_tms_not_in_payout_q4_25.created_at) AS cutoff_month,
    COUNT(*) AS cnt,
    SUM(
        TRY_CAST(list_in_tms_not_in_payout_q4_25.usd_amount AS DECIMAL(18,2))
    ) AS sum_usd_amount
FROM list_in_tms_not_in_payout_q4_25
LEFT JOIN stg_full_payout_q4_2025 full_payout
    ON list_in_tms_not_in_payout_q4_25.RECONCILIATION_ID = full_payout.TMS_RECONCILIATION_ID
GROUP BY
    YEAR(list_in_tms_not_in_payout_q4_25.created_at),
    MONTH(list_in_tms_not_in_payout_q4_25.created_at);

-- In TMS not in Payout (TO RUN)- Looking for cut-off with keeping on completness (not only contractor withdrawals)

WITH all_bank_transactions_filtered_q4_2025 AS (
    SELECT *
    FROM dbo.stg_tms_transactions_q4_2025
    WHERE TRY_CONVERT(date, LEFT(created_at,10)) >= '2025-10-01'
      AND TRY_CONVERT(date, LEFT(created_at,10)) <  '2026-01-01'
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
    -- WHERE apcw.WITHDRAWAL_ID IS NOT NULL
),

payout_q4 AS (
    SELECT DISTINCT
        tms_reconciliation_id
    FROM dbo.stg_payout_q4_2025
    WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at,10)) >= '2025-10-01'
      AND TRY_CONVERT(date, LEFT(withdrawal_created_at,10)) <  '2026-01-01'
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
        TRY_CONVERT(date, LEFT(withdrawal_created_at,10)) AS payout_date
    FROM dbo.stg_full_payout_q4_2025
    WHERE TRY_CONVERT(date, LEFT(withdrawal_created_at,10)) IS NOT NULL
)

SELECT
    YEAR(fp.payout_date)  AS payout_from_year,
    MONTH(fp.payout_date) AS payout_from_month,
    CASE
        WHEN fp.tms_reconciliation_id IS NOT NULL THEN 1
        ELSE 0
    END AS exists_in_full_payout,
    CASE
        when t.WITHDRAWAL_ID is not null then 'contractor_withdrawal'
        else 'other_withdrawal'
    END AS withdrawal_type,
    apcw.STATUS,
    COUNT(*) AS cnt,
    SUM(TRY_CAST(t.usd_amount AS DECIMAL(18,2))) AS sum_usd_amount
FROM tms_not_in_payout_q4 t
LEFT JOIN full_payout fp
    ON t.reconciliation_id = fp.tms_reconciliation_id
LEFT join all_payment_contractor_withdrawal apcw
    ON t.WITHDRAWAL_ID = apcw.WITHDRAWAL_ID
GROUP BY
    YEAR(fp.payout_date),
    MONTH(fp.payout_date),
    CASE
        WHEN fp.tms_reconciliation_id IS NOT NULL THEN 1
        ELSE 0
    END,
    CASE
        when t.WITHDRAWAL_ID is not null then 'contractor_withdrawal'
        else 'other_withdrawal'
    END,
    apcw.STATUS
ORDER BY
    payout_from_year,
    payout_from_month,
    exists_in_full_payout;

-- -------------- TEST -------------------------------

with payout_q4_2025 AS (
    SELECT
        p.*,
        d.withdrawal_date
    FROM dbo.stg_payout_q4_2025 p
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(p.withdrawal_created_at,10))
    ) d(withdrawal_date)
    WHERE d.withdrawal_date >= '2025-10-01'
      AND d.withdrawal_date <  '2026-01-01'
),
tms_q4_25 AS (
    SELECT DISTINCT
        t.reconciliation_id
    FROM dbo.stg_tms_transactions_q4_2025 t
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(t.created_at,10))
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
    SELECT p.*
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
        SELECT TRY_CONVERT(date, LEFT(f.created_at,10))
    ) d(created_date)
    -- WHERE d.created_date IS NOT NULL
)

select p.*,ft.created_date
FROM in_payout_not_in_tms p
LEFT JOIN full_tms ft
    ON p.tms_reconciliation_id = ft.reconciliation_id
where p.TMS_RECONCILIATION_ID is not null and ft.reconciliation_id is null and LOWER(LTRIM(RTRIM(p.payment_provider_name))) <> 'alviere'; 



  SELECT
        f.reconciliation_id,
        d.created_date
    FROM dbo.stg_full_tms_q4_2025 f
    CROSS APPLY (
        SELECT TRY_CONVERT(date, LEFT(f.created_at,10))
    ) d(created_date)
    WHERE f.RECONCILIATION_ID=24632042;


select *
FROM dbo.stg_payout_q4_2025 p
WHERE p.tms_reconciliation_id=24632042;


SELECT *
FROM dbo.stg_full_tms_q4_2025 f
WHERE reconciliation_id in ('24617296');


select month(TRY_CONVERT(date, LEFT(f.created_at,10))), year(TRY_CONVERT(date, LEFT(f.created_at,10))), count(*)
from dbo.stg_tms_transactions_q4_2025 f
group by month(TRY_CONVERT(date, LEFT(f.created_at,10))), year(TRY_CONVERT(date, LEFT(f.created_at,10)));

select month(TRY_CONVERT(date, LEFT(f.created_at,10))), year(TRY_CONVERT(date, LEFT(f.created_at,10))), count(*)
from dbo.stg_full_tms_q4_2025 f
group by month(TRY_CONVERT(date, LEFT(f.created_at,10))), year(TRY_CONVERT(date, LEFT(f.created_at,10)));


select *
from dbo.stg_full_tms_q4_2025 f
where f.RECONCILIATION_ID='19785211';


select *
from dbo.stg_payout_q4_2025 p
where p.tms_reconciliation_id='19785211';

select DIRECTION, count(*)
from dbo.stg_tms_transactions_q4_2025 f
group by DIRECTION;


select TYPE, count(*)
from dbo.stg_full_tms_q4_2025 f
group by TYPE;

select SETTLEMENT_CURRENCY, count(*)
from dbo.stg_payment_contractor_withdrawal p
group by SETTLEMENT_CURRENCY;

select DEEL_PLATFORM_TYPE, COUNT(*)
from dbo.stg_full_tms_q4_2025 f
group by DEEL_PLATFORM_TYPE;