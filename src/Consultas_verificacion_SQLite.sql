-- SQLite
-- s1
-- SELECT ROUND(SUM(saldo), 2) 
-- FROM saldos 
-- WHERE fecha = '2026-08-31' 
-- AND cuenta = '1';

--S2
-- SELECT e.razon_social, ROUND(i.roe, 2) 
-- FROM indicadores i JOIN entidades e USING (ruc) 
-- WHERE e.razon_social LIKE '%mushu%' 
-- AND i.fecha = '2026-06-30';

-- verificacion de roa 0 en S2
-- SELECT i.fecha,i.patrimonio,i.roe
-- FROM indicadores i JOIN entidades e USING (ruc) 
-- WHERE e.razon_social LIKE '%POLIC%'
-- ORDER BY i.fecha

--M1
-- SELECT ROUND(100.0 * SUM(i.cartera_improductiva) / SUM(i.cartera_bruta), 2) 
-- FROM indicadores i JOIN entidades e USING (ruc) 
-- WHERE e.segmento = 'SEGMENTO 1' 
-- AND i.fecha = '2026-08-31'


--M2
-- SELECT E.razon_social,ROUND(i.roa, 2) 
-- FROM indicadores i JOIN entidades e USING (ruc) 
-- WHERE e.segmento = 'SEGMENTO 2' 
-- AND i.fecha = '2026-08-31' 
-- ORDER BY i.roa DESC 
-- LIMIT 10

--M3
-- SELECT ROUND(
--   SUM(
--     CASE WHEN fecha = '2026-08-31' THEN 
--       CASE cuenta WHEN '14' THEN 
--             saldo WHEN '1499' THEN 
--             -saldo 
--       END 
--     END) - 
--   SUM(
--     CASE WHEN fecha = '2026-01-31' THEN 
--       CASE cuenta WHEN '14' THEN 
--             saldo WHEN '1499' THEN 
--             -saldo 
--       END 
--     END), 2) 
-- FROM saldos 
-- WHERE cuenta IN ('14', '1499')

--M4
-- SELECT E.razon_social,ROUND(liquidez, 2) 
-- FROM indicadores JOIN entidades e USING (ruc)
-- WHERE fecha = '2026-08-31' 
-- ORDER BY activo DESC


--s3
-- SELECT * FROM entidades
-- WHERE razon_social LIKE '%SAN MIGUEL%';

--m5
SELECT ROUND(100.0 * SUM(i.cartera_improductiva) / SUM(i.cartera_bruta), 2) AS m 
FROM indicadores i JOIN entidades e USING (ruc) 
WHERE e.segmento = 'SEGMENTO 3' AND i.fecha >= '2026-01-31' 
GROUP BY i.fecha 
ORDER BY m DESC 
LIMIT 1

--M6
-- SELECT ROUND(100.0 * SUM(CASE WHEN s.cuenta IN ('1428','1436','1444','1452','1460','1468') THEN s.saldo END) / SUM(s.saldo), 2) FROM saldos s JOIN entidades e USING (ruc) WHERE e.segmento = 'SEGMENTO 2' AND s.fecha = '2026-08-31' AND s.cuenta IN ('1404','1412','1420','1428','1436','1444','1452','1460','1468')