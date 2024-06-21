populate:
	docker exec -i postgres_db psql -U postgres -d students < dump_file.sql

