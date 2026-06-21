select
    businessentityid as business_entity_id,
    nationalidnumber as national_id_number,
    loginid as login_id,
    jobtitle as job_title,
    birthdate::date as birth_date,
    maritalstatus as marital_status,
    gender,
    hiredate::date as hire_date,
    salariedflag as is_salaried,
    vacationhours as vacation_hours,
    sickleavehours as sick_leave_hours,
    currentflag as is_current,
    rowguid,
    modifieddate as modified_at
from {{ source('oltp_humanresources', 'employee') }}
