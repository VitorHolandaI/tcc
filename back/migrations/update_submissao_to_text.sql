-- Migration: Update submissoes table to use TEXT type for code fields
-- This preserves newlines, tabs, and indentation in student code submissions

-- Change codigo_submetido from VARCHAR to TEXT
ALTER TABLE submissoes
ALTER COLUMN codigo_submetido TYPE TEXT;

-- Change resultado_execucao from VARCHAR to TEXT
ALTER TABLE submissoes
ALTER COLUMN resultado_execucao TYPE TEXT;

-- Verify the changes
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'submissoes'
AND column_name IN ('codigo_submetido', 'resultado_execucao');
