-- SELECT * FROM public.vizit
-- WHERE contract_id > 0
-- ORDER BY id ASC 

SELECT
    -- v.*, -- Выбираем все поля из таблицы vizit
    a.last_name,
    a.first_name,
    a.middle_name,
    -- Конкатенация ФИО (синтаксис может немного отличаться в зависимости от вашей СУБД)
    -- Для PostgreSQL:
    a.last_name || ' ' || a.first_name || COALESCE(' ' || a.middle_name, '') AS applicant_full_name,
    -- Для MySQL:
    -- CONCAT_WS(' ', a.last_name, a.first_name, a.middle_name) AS applicant_full_name
    -- Для SQL Server:
    -- a.last_name + ' ' + a.first_name + ISNULL(' ' + a.middle_name, '') AS applicant_full_name
	v.visit_date
FROM
    public.vizit v
JOIN
    public.applicant a ON v.applicant_id = a.id -- Условие соединения таблиц
WHERE
    v.contract_id > 0
ORDER BY
    v.id ASC;
