# Instrucciones para la ejecución con Docker

Versión de Docker sugerida: 29.5.2

Para levantar la solución completa basta con ejecutar:

```bash
docker compose up --build -d
```

Para detener los servicios y eliminar el volumen de la base de datos, ejecutar:

```bash
docker compose down -v 
```

Este levantará los servicions `server` (Django) y utilizando guvicorn, y `client` (React) utilizando nginx.

El cliente se encontrará disponible en [http://localhost:5173](http://localhost:5173) y el backoffice en [http://localhost:8080](http://localhost:8080).

> **Nota**: La DB de SQLite se encuentra en un volumen, por lo que los datos persistirán entre reinicios del contenedor.
