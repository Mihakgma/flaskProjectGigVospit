@echo off
where /F libssl-*.dll > nul && echo Found SSL library || echo Missing SSL library
where /F libcrypto-*.dll > nul && echo Found Crypto library || echo Missing Crypto library
where /F libpq.dll > nul && echo Found PostgreSQL library || echo Missing PostgreSQL library
pause
