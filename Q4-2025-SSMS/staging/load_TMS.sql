
-----------------------------------------
-- (A) Q4 TMS table used by in_payout_not_tms.sql
-----------------------------------------
DROP TABLE IF EXISTS dbo.stg_TMS_transactions_q4_25;


SELECT *
INTO dbo.stg_tms_transactions_q4_2025
FROM OPENROWSET(
    BULK 'C:\Users\Gal.Manor\EY\IL-Tech_Risk - מסמכים\Clients\2025\Deel\DA\Deel IT Audit Q4-25\01 - Org files\Q4 2025 - TMS Transactions and Balances\Shared on 30-03-2026\Q4 2025 - TMS Transactions & Reconciliations.csv',
    FORMAT = 'CSV',
    FIRSTROW = 2
) AS t;


