use deel_2025;

select AR.analytics_NS_MAPPING, 
count(*) as record_count,
SUM(TRY_CAST(AMOUNT_USD AS DECIMAL(18,2))) as total_amount
from dbo.AR_fy_25 as AR
group by AR.analytics_NS_MAPPING;


select month(TRY_CONVERT(date, LEFT(AR.POSTING_DATE,10))), year(TRY_CONVERT(date, LEFT(AR.POSTING_DATE,10))), count(*) as record_count
from dbo.AR_fy_25 as AR
group by month(TRY_CONVERT(date, LEFT(AR.POSTING_DATE,10))), year(TRY_CONVERT(date, LEFT(AR.POSTING_DATE,10)));


select count(*)
from dbo.AR_fy_25 as AR;

select top 100 *
from dbo.AR_fy_25 as AR;


select distinct REVERSAL_DATE
from dbo.AR_fy_25 as AR;



