DO $$
DECLARE
    r RECORD;
BEGIN
    -- Получаем все таблицы из схемы 'public' (или другой нужной схемы)
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        -- Динамически формируем и выполняем команду DROP TABLE
        -- CASCADE удалит также все зависимые объекты (ограничения, индексы и т.д.)
        -- и таблицы, которые ссылаются на удаляемую через внешние ключи.
        -- Если вы не хотите каскадного удаления, используйте RESTRICT (и убедитесь, что нет зависимостей).
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;