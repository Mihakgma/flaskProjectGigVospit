SELECT
    *
FROM
    public.applicant_vizit
WHERE
    applicant_id IN (
        SELECT
            applicant_id
        FROM
            public.applicant_vizit
        GROUP BY
            applicant_id
        HAVING
            COUNT(*) > 1
    )
ORDER BY
    applicant_id DESC, vizit_id DESC;
